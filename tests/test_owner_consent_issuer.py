import re
import unittest
from dataclasses import replace

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from core.owner_consent_protocol import canonical_payload
from core.owner_consent_issuer import (
    AuthenticatedOwnerSession,
    EnrolledOwnerDevice,
    issue_owner_consent_challenge,
)

NOW = 1_700_000_000_000
NONCE = "0123456789abcdef0123456789abcdef"


class FakeRegistry:
    def __init__(self, record=None, error=False):
        self.record = record
        self.error = error

    def lookup_active_device(self, device_id):
        if self.error:
            raise OSError("registry unavailable")
        if self.record is None or self.record.device_id != device_id:
            return None
        return self.record


class OwnerConsentIssuerTests(unittest.TestCase):
    def setUp(self):
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_der = self.private_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.record = EnrolledOwnerDevice(
            owner_id="owner-1",
            device_id="pixel9pro-1",
            public_key_spki_der=self.public_der,
        )
        self.session = AuthenticatedOwnerSession(
            owner_id="owner-1",
            device_id="pixel9pro-1",
            session_id="session-1",
            authenticated_at_epoch_ms=NOW - 1000,
            expires_at_epoch_ms=NOW + 60000,
        )
        self.registry = FakeRegistry(self.record)

    def test_issues_exact_session_bound_30_second_challenge(self):
        result = issue_owner_consent_challenge(
            self.session, action="read_screen", registry=self.registry,
            now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
        )
        self.assertTrue(result.issued)
        self.assertEqual(result.reason, "ISSUED")
        challenge = result.capability.challenge
        self.assertEqual(challenge.owner_id, self.session.owner_id)
        self.assertEqual(challenge.device_id, self.session.device_id)
        self.assertEqual(challenge.session_id, self.session.session_id)
        self.assertEqual(challenge.action, "read_screen")
        self.assertEqual(challenge.nonce, NONCE)
        self.assertEqual(challenge.issued_at_epoch_ms, NOW)
        self.assertEqual(challenge.expires_at_epoch_ms, NOW + 30000)
        self.assertEqual(
            result.capability.trusted_public_key_spki_der, self.public_der
        )
        self.assertTrue(canonical_payload(challenge))

    def test_challenge_never_outlives_authenticated_session(self):
        short_session = replace(
            self.session, expires_at_epoch_ms=NOW + 5000
        )
        result = issue_owner_consent_challenge(
            short_session, action="read_screen", registry=self.registry,
            now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
        )
        self.assertTrue(result.issued)
        self.assertEqual(
            result.capability.challenge.expires_at_epoch_ms, NOW + 5000
        )

    def test_accepts_short_valid_lifetime_at_signed_64_bit_boundary(self):
        maximum = (1 << 63) - 1
        edge_session = replace(
            self.session,
            authenticated_at_epoch_ms=maximum - 40000,
            expires_at_epoch_ms=maximum,
        )
        result = issue_owner_consent_challenge(
            edge_session, action="read_screen", registry=self.registry,
            now_epoch_ms=maximum - 29999,
            nonce_factory=lambda n: NONCE,
        )
        self.assertTrue(result.issued)
        self.assertEqual(result.capability.challenge.expires_at_epoch_ms, maximum)
        self.assertEqual(
            result.capability.challenge.expires_at_epoch_ms
            - result.capability.challenge.issued_at_epoch_ms,
            29999,
        )

    def test_default_nonce_is_128_bit_lowercase_hex(self):
        first = issue_owner_consent_challenge(
            self.session, action="read_screen", registry=self.registry,
            now_epoch_ms=NOW,
        )
        second = issue_owner_consent_challenge(
            self.session, action="read_screen", registry=self.registry,
            now_epoch_ms=NOW,
        )
        self.assertTrue(first.issued)
        self.assertTrue(second.issued)
        self.assertRegex(
            first.capability.challenge.nonce, re.compile(r"^[0-9a-f]{32}$")
        )
        self.assertNotEqual(
            first.capability.challenge.nonce,
            second.capability.challenge.nonce,
        )

    def test_rejects_expired_and_not_yet_valid_sessions(self):
        expired = replace(self.session, expires_at_epoch_ms=NOW)
        before = replace(self.session, authenticated_at_epoch_ms=NOW + 1)
        for session, expected in (
            (expired, "SESSION_EXPIRED"),
            (before, "SESSION_NOT_YET_VALID"),
        ):
            result = issue_owner_consent_challenge(
                session, action="read_screen", registry=self.registry,
                now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
            )
            self.assertFalse(result.issued)
            self.assertEqual(result.reason, expected)

    def test_rejects_invalid_session_fields_and_clock_types(self):
        invalid = replace(self.session, session_id="bad session")
        result = issue_owner_consent_challenge(
            invalid, action="read_screen", registry=self.registry,
            now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
        )
        self.assertEqual(result.reason, "INVALID_SESSION")
        result = issue_owner_consent_challenge(
            self.session, action="read_screen", registry=self.registry,
            now_epoch_ms=True, nonce_factory=lambda n: NONCE,
        )
        self.assertEqual(result.reason, "INVALID_CLOCK")

    def test_rejects_unsupported_action_and_invalid_nonce(self):
        result = issue_owner_consent_challenge(
            self.session, action="open_app", registry=self.registry,
            now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
        )
        self.assertEqual(result.reason, "INVALID_ACTION")
        result = issue_owner_consent_challenge(
            self.session, action="read_screen", registry=self.registry,
            now_epoch_ms=NOW, nonce_factory=lambda n: "short",
        )
        self.assertEqual(result.reason, "INVALID_NONCE")

    def test_rejects_nonce_source_failure(self):
        def broken(_):
            raise OSError("entropy source unavailable")
        result = issue_owner_consent_challenge(
            self.session, action="read_screen", registry=self.registry,
            now_epoch_ms=NOW, nonce_factory=broken,
        )
        self.assertEqual(result.reason, "NONCE_SOURCE_FAILED")

    def test_rejects_unregistered_inactive_or_mismatched_device(self):
        missing = issue_owner_consent_challenge(
            self.session, action="read_screen", registry=FakeRegistry(),
            now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
        )
        self.assertEqual(missing.reason, "DEVICE_NOT_ENROLLED")
        inactive = replace(self.record, active=False)
        result = issue_owner_consent_challenge(
            self.session, action="read_screen", registry=FakeRegistry(inactive),
            now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
        )
        self.assertEqual(result.reason, "DEVICE_NOT_ACTIVE")
        wrong_owner = replace(self.record, owner_id="owner-other")
        result = issue_owner_consent_challenge(
            self.session, action="read_screen", registry=FakeRegistry(wrong_owner),
            now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
        )
        self.assertEqual(result.reason, "OWNER_DEVICE_MISMATCH")

    def test_rejects_rsa_wrong_curve_and_malformed_public_keys(self):
        rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        rsa_der = rsa_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        p384_der = ec.generate_private_key(ec.SECP384R1()).public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        for key in (rsa_der, p384_der, b"invalid", b""):
            record = replace(self.record, public_key_spki_der=key)
            result = issue_owner_consent_challenge(
                self.session, action="read_screen", registry=FakeRegistry(record),
                now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
            )
            self.assertEqual(result.reason, "INVALID_TRUSTED_KEY")

    def test_credential_generation_snapshot_must_match_both_registry_lookups(self):
        session = replace(
            self.session,
            transport_certificate_sha256="a" * 64,
            credential_generation=4,
        )
        changed_record = replace(
            self.record,
            transport_certificate_sha256="b" * 64,
            credential_generation=4,
        )
        result = issue_owner_consent_challenge(
            session, action="read_screen", registry=FakeRegistry(changed_record),
            now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
        )
        self.assertEqual(result.reason, "CREDENTIAL_GENERATION_CHANGED")

    def test_matching_credential_generation_snapshot_is_accepted(self):
        session = replace(
            self.session,
            transport_certificate_sha256="a" * 64,
            credential_generation=4,
        )
        matching_record = replace(
            self.record,
            transport_certificate_sha256="a" * 64,
            credential_generation=4,
        )
        result = issue_owner_consent_challenge(
            session, action="read_screen", registry=FakeRegistry(matching_record),
            now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
        )
        self.assertTrue(result.issued, result.reason)

    def test_registry_failure_fails_closed(self):
        result = issue_owner_consent_challenge(
            self.session, action="read_screen", registry=FakeRegistry(error=True),
            now_epoch_ms=NOW, nonce_factory=lambda n: NONCE,
        )
        self.assertEqual(result.reason, "REGISTRY_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
