import base64
import hashlib
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa

from core.owner_enrollment_registry import (
    EnrollmentConflict, EnrollmentRegistryError, EnrollmentStatementError,
    SQLiteOwnerEnrollmentRegistry, _canonical_payload, SCHEMA_NAME,
)
from core.owner_consent_issuer import EnrolledOwnerDevice
from core.owner_consent_transport import EnrolledTransportCertificate


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
