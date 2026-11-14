import base64
import hashlib
import json
import os
import sqlite3
import tempfile
import threading
import subprocess
import sys
import time
import unittest
from unittest.mock import Mock, patch
from contextlib import closing, contextmanager
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa

from core.owner_enrollment_registry import (
    EnrollmentConflict, EnrollmentOutcomeUnknown, EnrollmentRegistryError,
    EnrollmentStatementError, SQLiteOwnerEnrollmentRegistry, _canonical_payload,
    SCHEMA_NAME,
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


_ENROLLMENT_COMMIT_CRASH_SUBPROCESS = r"""
import base64
import sys
import time
from pathlib import Path

from core.owner_enrollment_registry import SQLiteOwnerEnrollmentRegistry

def decode(value):
    return base64.urlsafe_b64decode(value + ("=" * ((4 - len(value) % 4) % 4)))

database_path, authority_b64, authority_key_id, envelope_b64, now_text, marker_path, mode = sys.argv[1:]
registry = SQLiteOwnerEnrollmentRegistry(
    database_path,
    authority_public_key_spki_der=decode(authority_b64),
    authority_key_id=authority_key_id,
)
original_connect = registry._connect

class CommitBoundaryConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, statement, *parameters):
        if statement.strip().upper() == "COMMIT":
            if mode == "after":
                self._connection.execute(statement, *parameters)
            marker = Path(marker_path)
            staged = marker.with_name(marker.name + ".tmp")
            staged.write_text("ready", encoding="ascii")
            staged.replace(marker)
            while True:
                time.sleep(1)
        return self._connection.execute(statement, *parameters)

    def __getattr__(self, name):
        return getattr(self._connection, name)

registry._connect = lambda: CommitBoundaryConnection(original_connect())
registry.apply_signed_enrollment(
    decode(envelope_b64),
    now_epoch_ms=int(now_text),
)
"""


def _commit_boundary_marker_ready(marker: Path) -> bool:
    """A created but not-yet-written marker is not a completed signal."""
    try:
        return marker.read_text(encoding="ascii") == "ready"
    except FileNotFoundError:
        return False


class CommitAcknowledgementLossConnection:
    """Test-only SQLite proxy that loses the acknowledgement around COMMIT."""

    def __init__(self, connection, *, mode):
        if mode not in {"before", "after", "rollback-fails"}:
            raise ValueError("unsupported commit acknowledgement mode")
        self._connection = connection
        self._mode = mode

    def execute(self, statement, *parameters):
        normalized = statement.strip().upper()
        if normalized == "COMMIT":
            if self._mode == "after":
                self._connection.execute(statement, *parameters)
            raise sqlite3.OperationalError(
                "simulated lost SQLite COMMIT acknowledgement"
            )
        if normalized == "ROLLBACK" and self._mode == "rollback-fails":
            raise sqlite3.OperationalError("simulated SQLite ROLLBACK failure")
        return self._connection.execute(statement, *parameters)

    def __getattr__(self, name):
        return getattr(self._connection, name)



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

    def test_failed_connection_setup_closes_handle_and_denies(self):
        handle = Mock()
        handle.execute.side_effect = sqlite3.DatabaseError("injected PRAGMA failure")
        with patch("core.owner_enrollment_registry.sqlite3.connect", return_value=handle):
            with self.assertRaises(EnrollmentRegistryError):
                self.registry._connect()
        handle.close.assert_called_once()

    def test_corrupt_database_fails_closed_without_reset(self):
        self.path.write_bytes(b"corrupt")
        with self.assertRaises(EnrollmentRegistryError):
            self.registry.initialize(explicit_first_install=True)
        self.assertEqual(self.path.read_bytes(), b"corrupt")



    def test_final_admission_guard_runs_under_both_database_writer_locks(self):
        self.enroll()
        ledger, reserved = self._reserve_action_for_enrolled_device()
        revoke = self.statement(
            operation="revoke", generation=2,
            enrollment_id="revoke-after-final-guard",
            cert=self.cert1, key=self.consent1,
        )

        revoke_started = threading.Event()
        cancel_started = threading.Event()
        revoke_finished = threading.Event()
        cancel_finished = threading.Event()
        revoke_results = []
        cancel_results = []
        errors = []
        workers = []
        blocked = {}

        def revoke_worker():
            revoke_started.set()
            try:
                revoke_results.append(
                    self.registry.apply_signed_enrollment(
                        revoke, now_epoch_ms=NOW,
                    )
                )
            except Exception as exc:
                errors.append(exc)
            finally:
                revoke_finished.set()

        def cancel_worker():
            cancel_started.set()
            try:
                cancel_results.append(
                    ledger.cancel_before_dispatch(reserved.idempotency_key)
                )
            except Exception as exc:
                errors.append(exc)
            finally:
                cancel_finished.set()

        def final_guard():
            # Competing operations use fresh SQLite connections through the
            # public APIs. They must not commit while this callback is running.
            revoke_thread = threading.Thread(target=revoke_worker)
            cancel_thread = threading.Thread(target=cancel_worker)
            workers.extend((revoke_thread, cancel_thread))
            revoke_thread.start()
            cancel_thread.start()

            started = revoke_started.wait(2) and cancel_started.wait(2)
            blocked["enrollment_writer"] = (
                started and not revoke_finished.wait(0.2)
            )
            blocked["reservation_writer"] = (
                started and not cancel_finished.wait(0.2)
            )
            return True

        claim = ledger.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=final_guard,
        )
        for worker in workers:
            worker.join(5)

        self.assertTrue(blocked.get("enrollment_writer", False),
                        "signed revocation was not blocked during final guard")
        self.assertTrue(blocked.get("reservation_writer", False),
                        "pre-dispatch cancellation was not blocked during final guard")
        self.assertTrue(all(not worker.is_alive() for worker in workers))
        self.assertEqual(errors, [])
        self.assertTrue(claim.applied, claim.reason)
        self.assertEqual(claim.state, DISPATCH_STARTED)
        self.assertEqual(len(cancel_results), 1)
        self.assertFalse(cancel_results[0].applied)
        self.assertEqual(ledger.get(reserved.idempotency_key).state, DISPATCH_STARTED)
        self.assertEqual(len(revoke_results), 1)
        self.assertFalse(revoke_results[0].active)


    def test_commit_marker_readiness_rejects_early_file_visibility(self):
        marker = Path(self.temp.name) / "early-commit.marker"
        self.assertFalse(_commit_boundary_marker_ready(marker))
        marker.touch()
        self.assertFalse(_commit_boundary_marker_ready(marker))
        marker.write_text("rea", encoding="ascii")
        self.assertFalse(_commit_boundary_marker_ready(marker))
        marker.write_text("ready", encoding="ascii")
        self.assertTrue(_commit_boundary_marker_ready(marker))

    def _kill_enrollment_process_at_commit(self, envelope, *, mode):
        marker = Path(self.temp.name) / f"enrollment-{mode}-commit.marker"
        command = [
            sys.executable,
            "-c",
            _ENROLLMENT_COMMIT_CRASH_SUBPROCESS,
            str(self.path),
            b64u(spki(self.authority)),
            KEY_ID,
            b64u(envelope),
            str(NOW),
            str(marker),
            mode,
        ]
        process = subprocess.Popen(
            command,
            cwd=os.getcwd(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 15.0
            while not _commit_boundary_marker_ready(marker):
                if process.poll() is not None:
                    stdout, stderr = process.communicate(timeout=5)
                    self.fail(
                        "enrollment subprocess exited before commit marker: "
                        f"returncode={process.returncode}, stdout={stdout!r}, "
                        f"stderr={stderr!r}"
                    )
                if time.monotonic() >= deadline:
                    process.kill()
                    stdout, stderr = process.communicate(timeout=5)
                    self.fail(
                        "enrollment subprocess did not reach commit boundary: "
                        f"stdout={stdout!r}, stderr={stderr!r}"
                    )
                time.sleep(0.01)

            self.assertTrue(_commit_boundary_marker_ready(marker))
            process.kill()
            process.communicate(timeout=5)
            self.assertNotEqual(process.returncode, 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)

    def test_process_death_before_signed_revocation_commit_rolls_back_atomically(self):
        self.enroll()
        ledger, reserved = self._reserve_action_for_enrolled_device()
        revoke = self.statement(
            operation="revoke",
            generation=2,
            enrollment_id="revoke-crash-before-commit",
            cert=self.cert1,
            key=self.consent1,
        )

        self._kill_enrollment_process_at_commit(revoke, mode="before")

        reopened = SQLiteOwnerEnrollmentRegistry(
            self.path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        active = reopened.lookup_active_device("pixel-1")
        history = reopened.history("pixel-1")
        self.assertIsNotNone(active)
        self.assertEqual(active.credential_generation, 1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].operation, "enroll")
        self.assertEqual(history[0].credential_generation, 1)

        claim = ledger.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=reopened,
            final_admission_guard=lambda: True,
        )
        self.assertTrue(claim.applied, claim.reason)
        self.assertEqual(claim.state, DISPATCH_STARTED)
        duplicate = ledger.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=reopened,
            final_admission_guard=lambda: True,
        )
        self.assertFalse(duplicate.applied)
        self.assertEqual(duplicate.reason, "ALREADY_CLAIMED")

    def test_process_death_after_signed_revocation_commit_preserves_revocation_atomically(self):
        self.enroll()
        ledger, reserved = self._reserve_action_for_enrolled_device()
        revoke = self.statement(
            operation="revoke",
            generation=2,
            enrollment_id="revoke-crash-after-commit",
            cert=self.cert1,
            key=self.consent1,
        )

        self._kill_enrollment_process_at_commit(revoke, mode="after")

        reopened = SQLiteOwnerEnrollmentRegistry(
            self.path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        self.assertIsNone(reopened.lookup_active_device("pixel-1"))
        history = reopened.history("pixel-1")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].operation, "enroll")
        self.assertEqual(history[0].credential_generation, 1)
        self.assertEqual(history[1].operation, "revoke")
        self.assertEqual(history[1].credential_generation, 2)

        denied = ledger.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=reopened,
            final_admission_guard=lambda: True,
        )
        self.assertFalse(denied.applied)
        self.assertEqual(denied.reason, "DEVICE_NOT_ACTIVE")
        self.assertEqual(denied.state, RESERVED)
        self.assertEqual(ledger.get(reserved.idempotency_key).state, RESERVED)


    def _apply_with_lost_commit_acknowledgement(self, envelope, *, mode):
        original_connect = self.registry._connect
        self.registry._connect = lambda: CommitAcknowledgementLossConnection(
            original_connect(), mode=mode
        )
        try:
            with self.assertRaises(EnrollmentRegistryError) as raised:
                self.registry.apply_signed_enrollment(
                    envelope, now_epoch_ms=NOW
                )
            return raised.exception
        finally:
            self.registry._connect = original_connect

    def test_signed_rotation_commit_acknowledgement_loss_before_commit_rolls_back(self):
        self.enroll()
        rotate = self.statement(
            operation="rotate",
            generation=2,
            enrollment_id="rotate-ack-loss-before",
            cert=self.cert2,
            key=self.consent2,
        )

        outcome = self._apply_with_lost_commit_acknowledgement(rotate, mode="before")
        self.assertIs(type(outcome), EnrollmentRegistryError)

        reopened = SQLiteOwnerEnrollmentRegistry(
            self.path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        active = reopened.lookup_active_device("pixel-1")
        history = reopened.history("pixel-1")
        self.assertIsNotNone(active)
        self.assertEqual(active.credential_generation, 1)
        self.assertEqual(active.transport_certificate_sha256, self.cert1)
        self.assertEqual(active.public_key_spki_der, spki(self.consent1))
        self.assertIsNotNone(reopened.lookup_active_certificate(self.cert1))
        self.assertIsNone(reopened.lookup_active_certificate(self.cert2))
        self.assertEqual(
            [(item.operation, item.credential_generation) for item in history],
            [("enroll", 1)],
        )

        applied = reopened.apply_signed_enrollment(rotate, now_epoch_ms=NOW)
        self.assertEqual(applied.operation, "rotate")
        self.assertEqual(applied.credential_generation, 2)
        self.assertEqual(
            reopened.lookup_active_device("pixel-1").transport_certificate_sha256,
            self.cert2,
        )
        with self.assertRaises(EnrollmentConflict):
            reopened.apply_signed_enrollment(rotate, now_epoch_ms=NOW)
        history_after_replay = reopened.history("pixel-1")
        self.assertEqual(
            [(item.operation, item.credential_generation) for item in history_after_replay],
            [("enroll", 1), ("rotate", 2)],
        )

    def test_signed_rotation_commit_acknowledgement_loss_after_commit_preserves_once(self):
        self.enroll()
        rotate = self.statement(
            operation="rotate",
            generation=2,
            enrollment_id="rotate-ack-loss-after",
            cert=self.cert2,
            key=self.consent2,
        )

        outcome = self._apply_with_lost_commit_acknowledgement(rotate, mode="after")
        self.assertIsInstance(outcome, EnrollmentOutcomeUnknown)
        self.assertTrue(outcome.reconciliation_required)
        self.assertEqual(outcome.operation, "rotate")
        self.assertEqual(outcome.owner_id, "owner-1")
        self.assertEqual(outcome.device_id, "pixel-1")
        self.assertEqual(outcome.enrollment_id, "rotate-ack-loss-after")
        self.assertEqual(outcome.credential_generation, 2)
        self.assertEqual(outcome.envelope_sha256, hashlib.sha256(rotate).hexdigest())

        reopened = SQLiteOwnerEnrollmentRegistry(
            self.path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        active = reopened.lookup_active_device("pixel-1")
        history = reopened.history("pixel-1")
        self.assertIsNotNone(active)
        self.assertEqual(active.credential_generation, 2)
        self.assertEqual(active.transport_certificate_sha256, self.cert2)
        self.assertEqual(active.public_key_spki_der, spki(self.consent2))
        self.assertIsNone(reopened.lookup_active_certificate(self.cert1))
        self.assertIsNotNone(reopened.lookup_active_certificate(self.cert2))
        self.assertEqual(
            [(item.operation, item.credential_generation) for item in history],
            [("enroll", 1), ("rotate", 2)],
        )
        reconciliation = reopened.reconcile_outcome_unknown(outcome)
        self.assertEqual(reconciliation.status, "APPLIED")
        self.assertFalse(reconciliation.automatic_retry_permitted)

        with self.assertRaises(EnrollmentConflict):
            reopened.apply_signed_enrollment(rotate, now_epoch_ms=NOW)
        history_after_replay = reopened.history("pixel-1")
        self.assertEqual(
            [(item.operation, item.credential_generation) for item in history_after_replay],
            [("enroll", 1), ("rotate", 2)],
        )


    def test_signed_initial_enrollment_commit_acknowledgement_loss_reports_unknown(self):
        envelope = self.statement(enrollment_id="enroll-ack-loss-after")
        outcome = self._apply_with_lost_commit_acknowledgement(envelope, mode="after")

        self.assertIsInstance(outcome, EnrollmentOutcomeUnknown)
        self.assertEqual(outcome.operation, "enroll")
        self.assertEqual(outcome.owner_id, "owner-1")
        self.assertEqual(outcome.device_id, "pixel-1")
        self.assertEqual(outcome.enrollment_id, "enroll-ack-loss-after")
        self.assertEqual(outcome.credential_generation, 1)
        self.assertEqual(outcome.envelope_sha256, hashlib.sha256(envelope).hexdigest())

        reopened = SQLiteOwnerEnrollmentRegistry(
            self.path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        self.assertEqual(reopened.lookup_active_device("pixel-1").credential_generation, 1)
        history = reopened.history("pixel-1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].envelope_sha256, hashlib.sha256(envelope).hexdigest())
        reconciliation = reopened.reconcile_outcome_unknown(outcome)
        self.assertEqual(reconciliation.status, "APPLIED")
        self.assertEqual(reconciliation.reason, "MATCHING_HISTORY_AND_CURRENT_STATE")
        self.assertFalse(reconciliation.automatic_retry_permitted)
        with self.assertRaises(EnrollmentConflict):
            reopened.apply_signed_enrollment(envelope, now_epoch_ms=NOW)

    def test_signed_revocation_commit_acknowledgement_loss_reports_unknown(self):
        self.enroll()
        envelope = self.statement(
            operation="revoke",
            generation=2,
            enrollment_id="revoke-ack-loss-after",
            cert=self.cert1,
            key=self.consent1,
        )
        outcome = self._apply_with_lost_commit_acknowledgement(envelope, mode="after")

        self.assertIsInstance(outcome, EnrollmentOutcomeUnknown)
        self.assertEqual(outcome.operation, "revoke")
        self.assertEqual(outcome.owner_id, "owner-1")
        self.assertEqual(outcome.device_id, "pixel-1")
        self.assertEqual(outcome.enrollment_id, "revoke-ack-loss-after")
        self.assertEqual(outcome.credential_generation, 2)
        self.assertEqual(outcome.envelope_sha256, hashlib.sha256(envelope).hexdigest())

        reopened = SQLiteOwnerEnrollmentRegistry(
            self.path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        self.assertIsNone(reopened.lookup_active_device("pixel-1"))
        history = reopened.history("pixel-1")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1].operation, "revoke")
        self.assertEqual(history[1].envelope_sha256, hashlib.sha256(envelope).hexdigest())
        reconciliation = reopened.reconcile_outcome_unknown(outcome)
        self.assertEqual(reconciliation.status, "APPLIED")
        self.assertFalse(reconciliation.automatic_retry_permitted)
        with self.assertRaises(EnrollmentConflict):
            reopened.apply_signed_enrollment(envelope, now_epoch_ms=NOW)

    def test_signed_rotation_commit_and_rollback_failure_reports_unknown(self):
        self.enroll()
        envelope = self.statement(
            operation="rotate",
            generation=2,
            enrollment_id="rotate-rollback-failure",
            cert=self.cert2,
            key=self.consent2,
        )
        outcome = self._apply_with_lost_commit_acknowledgement(
            envelope, mode="rollback-fails"
        )

        self.assertIsInstance(outcome, EnrollmentOutcomeUnknown)
        self.assertEqual(outcome.operation, "rotate")
        self.assertEqual(outcome.envelope_sha256, hashlib.sha256(envelope).hexdigest())

        reopened = SQLiteOwnerEnrollmentRegistry(
            self.path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        self.assertEqual(reopened.lookup_active_device("pixel-1").credential_generation, 1)
        self.assertEqual(len(reopened.history("pixel-1")), 1)
        reconciliation = reopened.reconcile_outcome_unknown(outcome)
        self.assertEqual(reconciliation.status, "NOT_OBSERVED")
        self.assertEqual(reconciliation.reason, "NO_HISTORY_AND_PRIOR_STATE_MATCH")
        self.assertFalse(reconciliation.automatic_retry_permitted)

    def test_reconcile_unknown_outcome_with_mismatched_history_is_unresolved(self):
        self.enroll()
        outcome = EnrollmentOutcomeUnknown(
            operation="enroll",
            owner_id="owner-1",
            device_id="pixel-1",
            enrollment_id="missing-enrollment",
            credential_generation=1,
            envelope_sha256="0" * 64,
        )
        reconciliation = self.registry.reconcile_outcome_unknown(outcome)
        self.assertEqual(reconciliation.status, "UNRESOLVED")
        self.assertEqual(
            reconciliation.reason,
            "NO_MATCHING_HISTORY_OR_COHERENT_PRIOR_STATE",
        )
        self.assertFalse(reconciliation.automatic_retry_permitted)

    def test_reconcile_unknown_outcome_fails_closed_on_corrupt_database(self):
        envelope = self.statement(enrollment_id="corrupt-reconcile-db")
        outcome = self._apply_with_lost_commit_acknowledgement(envelope, mode="after")
        self.path.write_bytes(b"corrupt database")
        reconciliation = self.registry.reconcile_outcome_unknown(outcome)
        self.assertEqual(reconciliation.status, "UNRESOLVED")
        self.assertEqual(
            reconciliation.reason,
            "DATABASE_UNAVAILABLE_OR_INVALID",
        )
        self.assertFalse(reconciliation.automatic_retry_permitted)

    def test_reconciliation_enforces_sqlite_query_only_before_snapshot(self):
        envelope = self.statement(enrollment_id="query-only-reconcile")
        outcome = self._apply_with_lost_commit_acknowledgement(envelope, mode="after")
        reopened = SQLiteOwnerEnrollmentRegistry(
            self.path,
            authority_public_key_spki_der=spki(self.authority),
            authority_key_id=KEY_ID,
        )
        raw_connection = reopened._connect()

        class QueryOnlyProbe:
            def __init__(self, connection):
                self.connection = connection
                self.events = []
                self.write_was_blocked = False

            @property
            def in_transaction(self):
                return self.connection.in_transaction

            def execute(self, sql, parameters=()):
                self.events.append(sql)
                cursor = self.connection.execute(sql, parameters)
                if sql == "PRAGMA query_only=ON":
                    try:
                        self.connection.execute(
                            "UPDATE owner_device SET active=active WHERE device_id=?",
                            ("pixel-1",),
                        )
                    except sqlite3.OperationalError as exc:
                        if "readonly" not in str(exc).lower():
                            raise
                        self.write_was_blocked = True
                    else:
                        raise AssertionError("query_only did not block a write")
                return cursor

            def close(self):
                self.connection.close()

        probe = QueryOnlyProbe(raw_connection)
        reopened._connect = lambda: probe
        reconciliation = reopened.reconcile_outcome_unknown(outcome)

        self.assertEqual(reconciliation.status, "APPLIED")
        self.assertFalse(reconciliation.automatic_retry_permitted)
        self.assertTrue(probe.write_was_blocked)
        self.assertEqual(probe.events[:2], ["PRAGMA query_only=ON", "BEGIN"])

    def test_reconcile_unknown_outcome_rejects_current_row_history_mismatch(self):
        envelope = self.statement(enrollment_id="current-row-mismatch")
        outcome = self._apply_with_lost_commit_acknowledgement(envelope, mode="after")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "UPDATE owner_device SET transport_certificate_sha256=? WHERE device_id=?",
                ("0" * 64, "pixel-1"),
            )

        reconciliation = self.registry.reconcile_outcome_unknown(outcome)
        self.assertEqual(reconciliation.status, "UNRESOLVED")
        self.assertEqual(reconciliation.reason, "CURRENT_STATE_MISMATCH")
        self.assertFalse(reconciliation.automatic_retry_permitted)


if __name__ == "__main__":
    unittest.main()
