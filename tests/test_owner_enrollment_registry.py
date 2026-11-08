import base64
import hashlib
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa

from core.owner_enrollment_registry import (
    EnrollmentConflict, EnrollmentRegistryError, EnrollmentStatementError,
    SQLiteOwnerEnrollmentRegistry, _canonical_payload, SCHEMA_NAME,
)
from core.owner_consent_issuer import EnrolledOwnerDevice
from core.owner_consent_transport import EnrolledTransportCertificate
from core.action_reservation import (
    ActionReservationRequest, DurableActionReservationLedger,
    DISPATCH_STARTED, RESERVED,
)


NOW = 1_800_000_000_000
KEY_ID = "offline-enrollment-v1"
MAX_TTL = 300_000


def b64u(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def spki(key):
    return key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "enrollment.sqlite"
        self.authority = ed25519.Ed25519PrivateKey.generate()
        self.registry = SQLiteOwnerEnrollmentRegistry(
            self.path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        self.registry.initialize(explicit_first_install=True)
        self.consent1 = ec.generate_private_key(ec.SECP256R1())
        self.consent2 = ec.generate_private_key(ec.SECP256R1())
        self.cert1 = hashlib.sha256(b"synthetic transport cert one").hexdigest()
        self.cert2 = hashlib.sha256(b"synthetic transport cert two").hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def statement(self, operation="enroll", *, device="pixel-1", owner="owner-1",
                  generation=1, enrollment_id="enroll-1", cert=None, key=None,
                  digest=None, issued=NOW-1000, expires=NOW+60_000, authority=None,
                  key_id=KEY_ID):
        cert = cert or self.cert1
        key = key or self.consent1
        if operation == "revoke":
            key_der = None
            key_digest = digest or hashlib.sha256(spki(key)).hexdigest()
        else:
            key_der = spki(key)
            key_digest = digest or hashlib.sha256(key_der).hexdigest()
        payload = {
            "schema": SCHEMA_NAME,
            "version": 1,
            "operation": operation,
            "authority_key_id": key_id,
            "enrollment_id": enrollment_id,
            "owner_id": owner,
            "device_id": device,
            "credential_generation": generation,
            "issued_at_epoch_ms": issued,
            "expires_at_epoch_ms": expires,
            "transport_certificate_sha256": cert,
            "consent_public_key_spki_der": None if key_der is None else b64u(key_der),
            "consent_public_key_sha256": key_digest,
        }
        signer = authority or self.authority
        signature = b64u(signer.sign(_canonical_payload(payload)))
        return json.dumps(
            {"payload": payload, "signature": signature},
            sort_keys=True, separators=(",", ":"),
        ).encode("ascii")

    def enroll(self):
        return self.registry.apply_signed_enrollment(
            self.statement(), now_epoch_ms=NOW
        )

    def test_initialization_requires_explicit_first_install_and_never_resets(self):
        path = Path(self.temp.name) / "fresh.sqlite"
        registry = SQLiteOwnerEnrollmentRegistry(
            path, authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        with self.assertRaises(EnrollmentRegistryError):
            registry.initialize()
        registry.initialize(explicit_first_install=True)
        registry.apply_signed_enrollment(self.statement(), now_epoch_ms=NOW)
        registry.initialize(explicit_first_install=False)
        self.assertEqual(registry.lookup_active_device("pixel-1").device_id, "pixel-1")

    def test_database_is_owner_only(self):
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)

    def test_signed_enrollment_binds_both_registry_interfaces(self):
        result = self.enroll()
        self.assertEqual(result.operation, "enroll")
        self.assertEqual(result.credential_generation, 1)
        consent = self.registry.lookup_active_device("pixel-1")
        transport = self.registry.lookup_active_certificate(self.cert1)
        self.assertIs(type(consent), EnrolledOwnerDevice)
        self.assertIs(type(transport), EnrolledTransportCertificate)
        self.assertEqual(consent.owner_id, transport.owner_id)
        self.assertEqual(consent.device_id, transport.device_id)
        self.assertEqual(consent.transport_certificate_sha256, self.cert1)
        self.assertEqual(transport.credential_generation, 1)
        self.assertEqual(consent.credential_generation, 1)
        self.assertEqual(consent.public_key_spki_der, spki(self.consent1))

    def test_invalid_signature_fails_before_database_mutation(self):
        raw = bytearray(self.statement())
        raw[-3] = ord("A") if raw[-3] != ord("A") else ord("B")
        with self.assertRaises(EnrollmentStatementError):
            self.registry.apply_signed_enrollment(bytes(raw), now_epoch_ms=NOW)
        self.assertIsNone(self.registry.lookup_active_device("pixel-1"))

    def test_wrong_authority_key_id_and_wrong_authority_fail(self):
        with self.assertRaises(EnrollmentStatementError):
            self.registry.apply_signed_enrollment(
                self.statement(key_id="other-authority"), now_epoch_ms=NOW
            )
        other = ed25519.Ed25519PrivateKey.generate()
        with self.assertRaises(EnrollmentStatementError):
            self.registry.apply_signed_enrollment(
                self.statement(authority=other), now_epoch_ms=NOW
            )

    def test_expired_future_and_overlong_statements_fail(self):
        for issued, expires in (
            (NOW-100_000, NOW-1),
            (NOW+1, NOW+10_000),
            (NOW-1, NOW+MAX_TTL+1),
        ):
            with self.subTest(issued=issued, expires=expires):
                with self.assertRaises(EnrollmentStatementError):
                    self.registry.apply_signed_enrollment(
                        self.statement(enrollment_id=f"e{issued}", issued=issued, expires=expires),
                        now_epoch_ms=NOW,
                    )

    def test_duplicate_json_keys_and_oversized_envelope_fail(self):
        duplicate = b'{"payload":{},"payload":{},"signature":"AAAA"}'
        with self.assertRaises(EnrollmentStatementError):
            self.registry.apply_signed_enrollment(duplicate, now_epoch_ms=NOW)
        with self.assertRaises(EnrollmentStatementError):
            self.registry.apply_signed_enrollment(b" " * 4097, now_epoch_ms=NOW)

    def test_p384_and_rsa_consent_keys_are_rejected(self):
        for key in (
            ec.generate_private_key(ec.SECP384R1()),
            rsa.generate_private_key(public_exponent=65537, key_size=2048),
        ):
            with self.subTest(key=type(key).__name__):
                with self.assertRaises(EnrollmentStatementError):
                    self.registry.apply_signed_enrollment(
                        self.statement(key=key), now_epoch_ms=NOW
                    )

    def test_digest_mismatch_and_malformed_fingerprint_fail(self):
        with self.assertRaises(EnrollmentStatementError):
            self.registry.apply_signed_enrollment(
                self.statement(digest="0"*64), now_epoch_ms=NOW
            )
        with self.assertRaises(EnrollmentStatementError):
            self.registry.apply_signed_enrollment(
                self.statement(cert="not-a-fingerprint"), now_epoch_ms=NOW
            )

    def test_duplicate_enrollment_is_rejected(self):
        self.enroll()
        with self.assertRaises(EnrollmentConflict):
            self.registry.apply_signed_enrollment(
                self.statement(enrollment_id="enroll-2"), now_epoch_ms=NOW
            )

    def test_rotation_requires_exact_next_generation_and_replaces_both_credentials(self):
        self.enroll()
        bad = self.statement(
            operation="rotate", generation=3, enrollment_id="rotate-bad",
            cert=self.cert2, key=self.consent2,
        )
        with self.assertRaises(EnrollmentConflict):
            self.registry.apply_signed_enrollment(bad, now_epoch_ms=NOW)
        good = self.statement(
            operation="rotate", generation=2, enrollment_id="rotate-2",
            cert=self.cert2, key=self.consent2,
        )
        self.registry.apply_signed_enrollment(good, now_epoch_ms=NOW)
        self.assertIsNone(self.registry.lookup_active_certificate(self.cert1))
        consent = self.registry.lookup_active_device("pixel-1")
        self.assertEqual(consent.credential_generation, 2)
        self.assertEqual(consent.transport_certificate_sha256, self.cert2)
        self.assertEqual(consent.public_key_spki_der, spki(self.consent2))

    def test_revocation_is_signed_atomic_and_preserves_history(self):
        self.enroll()
        revoke = self.statement(
            operation="revoke", generation=2, enrollment_id="revoke-2",
            cert=self.cert1, key=self.consent1,
        )
        result = self.registry.apply_signed_enrollment(revoke, now_epoch_ms=NOW)
        self.assertFalse(result.active)
        self.assertIsNone(self.registry.lookup_active_device("pixel-1"))
        self.assertIsNone(self.registry.lookup_active_certificate(self.cert1))
        history = self.registry.history("pixel-1")
        self.assertEqual([x.operation for x in history], ["enroll", "revoke"])
        self.assertEqual([x.credential_generation for x in history], [1, 2])

    def test_revocation_must_match_current_pair(self):
        self.enroll()
        revoke = self.statement(
            operation="revoke", generation=2, enrollment_id="revoke-2",
            cert=self.cert2,
        )
        with self.assertRaises(EnrollmentConflict):
            self.registry.apply_signed_enrollment(revoke, now_epoch_ms=NOW)

    def test_credentials_cannot_be_reused_across_devices(self):
        self.enroll()
        duplicate = self.statement(
            device="pixel-2", owner="owner-1", enrollment_id="enroll-2"
        )
        with self.assertRaises(EnrollmentConflict):
            self.registry.apply_signed_enrollment(duplicate, now_epoch_ms=NOW)

    def test_rotation_can_reenroll_revoked_device_with_new_pair(self):
        self.enroll()
        self.registry.apply_signed_enrollment(
            self.statement(operation="revoke", generation=2, enrollment_id="revoke-2"),
            now_epoch_ms=NOW,
        )
        self.registry.apply_signed_enrollment(
            self.statement(operation="rotate", generation=3, enrollment_id="rotate-3",
                           cert=self.cert2, key=self.consent2),
            now_epoch_ms=NOW,
        )
        self.assertEqual(self.registry.lookup_active_device("pixel-1").credential_generation, 3)

    def test_concurrent_same_enrollment_commits_only_once(self):
        envelope = self.statement()
        outcomes = []
        barrier = threading.Barrier(2)
        def worker():
            barrier.wait()
            try:
                outcomes.append(self.registry.apply_signed_enrollment(
                    envelope, now_epoch_ms=NOW
                ).operation)
            except Exception as exc:
                outcomes.append(type(exc).__name__)
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(outcomes.count("enroll"), 1)
        self.assertEqual(len(outcomes), 2)
        self.assertEqual(len(self.registry.history("pixel-1")), 1)


    def _admission_args(self, *, nonce="0123456789abcdef0123456789abcdef",
                        owner="owner-1", device="pixel-1", cert=None,
                        key=None, generation=1, now=NOW):
        key = self.consent1 if key is None else key
        return {
            "owner_id": owner,
            "device_id": device,
            "nonce": nonce,
            "transport_certificate_sha256": self.cert1 if cert is None else cert,
            "credential_generation": generation,
            "consent_public_key_spki_der": spki(key),
            "now_epoch_ms": now,
        }

    def test_atomic_consent_admission_is_one_use_and_survives_reopen(self):
        self.enroll()
        args = self._admission_args()
        self.assertEqual(self.registry.consume_consent_nonce(**args), "ADMITTED")
        reopened = SQLiteOwnerEnrollmentRegistry(
            self.path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        self.assertEqual(
            reopened.consume_consent_nonce(**args), "REPLAY_OR_CAPACITY"
        )

    def test_revocation_committed_before_admission_is_rejected_atomically(self):
        self.enroll()
        revoke = self.statement(
            operation="revoke", generation=2, enrollment_id="revoke-2",
            cert=self.cert1, key=self.consent1,
        )
        self.registry.apply_signed_enrollment(revoke, now_epoch_ms=NOW)
        self.assertEqual(
            self.registry.consume_consent_nonce(**self._admission_args()),
            "ENROLLMENT_NOT_ACTIVE",
        )

    def test_rotation_committed_before_admission_rejects_old_pair(self):
        self.enroll()
        rotate = self.statement(
            operation="rotate", generation=2, enrollment_id="rotate-2",
            cert=self.cert2, key=self.consent2,
        )
        self.registry.apply_signed_enrollment(rotate, now_epoch_ms=NOW)
        self.assertEqual(
            self.registry.consume_consent_nonce(**self._admission_args()),
            "ENROLLMENT_CREDENTIAL_MISMATCH",
        )

    def test_concurrent_duplicate_consent_nonce_commits_exactly_once(self):
        self.enroll()
        args = self._admission_args()
        barrier = threading.Barrier(12)
        outcomes = []
        lock = threading.Lock()

        def worker():
            barrier.wait()
            result = self.registry.consume_consent_nonce(**args)
            with lock:
                outcomes.append(result)

        workers = [threading.Thread(target=worker) for _ in range(12)]
        for worker_thread in workers:
            worker_thread.start()
        for worker_thread in workers:
            worker_thread.join()
        self.assertEqual(outcomes.count("ADMITTED"), 1)
        self.assertEqual(outcomes.count("REPLAY_OR_CAPACITY"), 11)


    def test_wall_clock_advance_then_rollback_never_evicts_replay_nonce(self):
        self.enroll()
        args = self._admission_args()
        self.assertEqual(self.registry.consume_consent_nonce(**args), "ADMITTED")
        advanced = dict(args, now_epoch_ms=NOW + 120_000)
        self.assertEqual(
            self.registry.consume_consent_nonce(**advanced),
            "REPLAY_OR_CAPACITY",
        )
        rolled_back = dict(args, now_epoch_ms=NOW + 1_000)
        self.assertEqual(
            self.registry.consume_consent_nonce(**rolled_back),
            "REPLAY_OR_CAPACITY",
        )

    def test_invalid_consent_admission_context_does_not_mutate_state(self):
        self.enroll()
        args = self._admission_args(nonce="not-a-canonical-nonce")
        self.assertEqual(
            self.registry.consume_consent_nonce(**args),
            "INVALID_ADMISSION_CONTEXT",
        )
        self.assertEqual(
            self.registry.consume_consent_nonce(**self._admission_args()),
            "ADMITTED",
        )

    def _reserve_action_for_enrolled_device(self, *, nonce="0123456789abcdef0123456789abcdef"):
        consent_digest = hashlib.sha256(spki(self.consent1)).hexdigest()
        ledger = DurableActionReservationLedger(
            Path(self.temp.name) / "actions.sqlite",
            clock_ms=lambda: NOW,
        )
        decision = ledger.reserve(ActionReservationRequest(
            owner_id="owner-1",
            device_id="pixel-1",
            session_id="session-1",
            capability_nonce=nonce,
            protocol_version=2,
            action_id="navigate",
            arguments_sha256="a" * 64,
            issued_at_epoch_ms=NOW - 1_000,
            expires_at_epoch_ms=NOW + 29_000,
            transport_certificate_sha256=self.cert1,
            credential_generation=1,
            consent_public_key_sha256=consent_digest,
        ))
        self.assertTrue(decision.created, decision.reason)
        self.assertEqual(decision.state, RESERVED)
        return ledger, decision

    def test_dispatch_claim_rejects_revocation_committed_before_claim(self):
        self.enroll()
        ledger, reserved = self._reserve_action_for_enrolled_device()
        revoke = self.statement(
            operation="revoke", generation=2, enrollment_id="revoke-before-claim",
            cert=self.cert1, key=self.consent1,
        )
        self.registry.apply_signed_enrollment(revoke, now_epoch_ms=NOW)

        result = ledger.claim_dispatch(
            reserved.idempotency_key, enrollment_registry=self.registry,
 final_admission_guard=lambda: True,
        )
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "DEVICE_NOT_ACTIVE")
        self.assertEqual(result.state, RESERVED)
        self.assertEqual(ledger.get(reserved.idempotency_key).state, RESERVED)

    def test_dispatch_claim_rejects_rotation_committed_before_claim(self):
        self.enroll()
        ledger, reserved = self._reserve_action_for_enrolled_device()
        rotate = self.statement(
            operation="rotate", generation=2, enrollment_id="rotate-before-claim",
            cert=self.cert2, key=self.consent2,
        )
        self.registry.apply_signed_enrollment(rotate, now_epoch_ms=NOW)

        result = ledger.claim_dispatch(
            reserved.idempotency_key, enrollment_registry=self.registry,
 final_admission_guard=lambda: True,
        )
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "ENROLLMENT_CREDENTIAL_MISMATCH")
        self.assertEqual(result.state, RESERVED)
        self.assertEqual(ledger.get(reserved.idempotency_key).state, RESERVED)

    def test_dispatch_claim_holds_enrollment_lock_until_ledger_commit(self):
        self.enroll()
        ledger, reserved = self._reserve_action_for_enrolled_device()
        original = self.registry.hold_active_enrollment_for_dispatch
        lock_acquired = threading.Event()
        release_claim = threading.Event()
        revoke_started = threading.Event()
        revoke_finished = threading.Event()
        claim_result = []
        revoke_result = []
        errors = []

        @contextmanager
        def blocking_enrollment_lock(**kwargs):
            with original(**kwargs) as status:
                lock_acquired.set()
                if not release_claim.wait(5):
                    raise TimeoutError("test did not release enrollment lock")
                yield status

        self.registry.hold_active_enrollment_for_dispatch = blocking_enrollment_lock

        def claim_worker():
            try:
                claim_result.append(ledger.claim_dispatch(
                    reserved.idempotency_key, enrollment_registry=self.registry,
 final_admission_guard=lambda: True,
                ))
            except Exception as exc:
                errors.append(exc)

        def revoke_worker():
            revoke_started.set()
            try:
                revoke_result.append(self.registry.apply_signed_enrollment(
                    self.statement(
                        operation="revoke", generation=2,
                        enrollment_id="revoke-after-claim",
                        cert=self.cert1, key=self.consent1,
                    ),
                    now_epoch_ms=NOW,
                ))
            except Exception as exc:
                errors.append(exc)
            finally:
                revoke_finished.set()

        claim_thread = threading.Thread(target=claim_worker)
        revoke_thread = threading.Thread(target=revoke_worker)
        claim_thread.start()
        self.assertTrue(lock_acquired.wait(5), "claim never acquired enrollment writer lock")
        revoke_thread.start()
        self.assertTrue(revoke_started.wait(5), "revocation thread did not start")
        was_blocked = not revoke_finished.wait(0.1)
        release_claim.set()
        claim_thread.join(5)
        revoke_thread.join(5)
        self.registry.hold_active_enrollment_for_dispatch = original

        self.assertFalse(claim_thread.is_alive(), "claim thread did not finish")
        self.assertFalse(revoke_thread.is_alive(), "revocation thread did not finish")
        self.assertEqual(errors, [])
        self.assertTrue(was_blocked, "revocation committed while dispatch claim held the enrollment lock")
        self.assertEqual(len(claim_result), 1)
        self.assertTrue(claim_result[0].applied, claim_result[0].reason)
        self.assertEqual(claim_result[0].state, DISPATCH_STARTED)
        self.assertEqual(ledger.get(reserved.idempotency_key).state, DISPATCH_STARTED)
        self.assertEqual(len(revoke_result), 1)
        self.assertFalse(revoke_result[0].active)
        self.assertIsNone(self.registry.lookup_active_device("pixel-1"))

    def test_dispatch_claim_fails_closed_when_enrollment_store_is_unavailable(self):
        self.enroll()
        ledger, reserved = self._reserve_action_for_enrolled_device()
        corrupt_path = Path(self.temp.name) / "corrupt-enrollment.sqlite"
        corrupt_path.write_bytes(b"corrupt database")
        os.chmod(corrupt_path, 0o600)
        unavailable = SQLiteOwnerEnrollmentRegistry(
            corrupt_path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        result = ledger.claim_dispatch(
            reserved.idempotency_key, enrollment_registry=unavailable,
 final_admission_guard=lambda: True,
        )
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "ENROLLMENT_REGISTRY_UNAVAILABLE")
        self.assertEqual(result.state, RESERVED)
        self.assertEqual(ledger.get(reserved.idempotency_key).state, RESERVED)

    def test_v1_database_migration_is_explicit_additive_and_idempotent(self):
        self.enroll()
        db = sqlite3.connect(self.path)
        db.execute("DROP INDEX owner_consent_replay_age")
        db.execute("DROP TABLE owner_consent_replay")
        db.execute("PRAGMA user_version=1")
        db.commit()
        db.close()
        with self.assertRaises(EnrollmentRegistryError):
            self.registry.lookup_active_device("pixel-1")
        with self.assertRaises(EnrollmentRegistryError):
            self.registry.migrate_v1_to_v2()
        self.assertTrue(self.registry.migrate_v1_to_v2(explicit_migration=True))
        self.assertFalse(self.registry.migrate_v1_to_v2(explicit_migration=True))
        self.assertEqual(self.registry.lookup_active_device("pixel-1").device_id, "pixel-1")
        self.assertEqual(len(self.registry.history("pixel-1")), 1)

    def test_missing_database_fails_closed(self):
        path = Path(self.temp.name) / "missing.sqlite"
        registry = SQLiteOwnerEnrollmentRegistry(
            path, authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        with self.assertRaises(EnrollmentRegistryError):
            registry.lookup_active_device("pixel-1")

    def test_symlink_database_is_rejected(self):
        target = Path(self.temp.name) / "target.sqlite"
        target.write_bytes(b"not a database")
        link = Path(self.temp.name) / "link.sqlite"
        link.symlink_to(target)
        registry = SQLiteOwnerEnrollmentRegistry(
            link, authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        with self.assertRaises(EnrollmentRegistryError):
            registry.initialize(explicit_first_install=True)

    def test_permissive_database_mode_is_rejected(self):
        os.chmod(self.path, 0o644)
        with self.assertRaises(EnrollmentRegistryError):
            self.registry.lookup_active_device("pixel-1")

    def test_corrupt_database_fails_closed_without_reset(self):
        self.path.write_bytes(b"corrupt")
        with self.assertRaises(EnrollmentRegistryError):
            self.registry.initialize(explicit_first_install=True)
        self.assertEqual(self.path.read_bytes(), b"corrupt")


if __name__ == "__main__":
    unittest.main()
