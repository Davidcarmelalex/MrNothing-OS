import base64
import configparser
import json
import os
import tempfile
import unittest
from dataclasses import replace

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from core.command_admission import DurableReplayLedger
from core.owner_consent_issuer import EnrolledOwnerDevice
from core.owner_consent_protocol import (
    ConsentChallenge, MAX_CAPABILITY_TTL_MS, canonical_payload, verify_and_consume,
)

FIXTURE = os.path.join(
    os.path.dirname(__file__), "..", "android", "app", "src", "test",
    "resources", "owner-consent-v1.properties",
)


class _Registry:
    def __init__(self, record=None, *, fail=False, sequence=None):
        self.record = record
        self.fail = fail
        self.sequence = sequence
        self.calls = 0

    def lookup_active_device(self, device_id):
        if self.fail:
            raise OSError("synthetic enrollment registry failure")
        if self.sequence is not None:
            index = min(self.calls, len(self.sequence) - 1)
            self.calls += 1
            record = self.sequence[index]
        else:
            record = self.record
        if record is None or record.device_id != device_id:
            return None
        return record


class OwnerConsentProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp.name, "replay.sqlite")
        self.ledger = DurableReplayLedger(self.db_path, ttl_seconds=60)
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_der = self.private_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.challenge = ConsentChallenge(
            device_id="pixel9pro-1",
            owner_id="owner-1",
            session_id="session-1",
            action="read_screen",
            nonce="0123456789abcdef0123456789abcdef",
            issued_at_epoch_ms=1_700_000_000_000,
            expires_at_epoch_ms=1_700_000_030_000,
        )
        self.now = self.challenge.issued_at_epoch_ms + 1_000
        self.transport_fingerprint = "a" * 64
        self.enrollment = EnrolledOwnerDevice(
            owner_id="owner-1", device_id="pixel9pro-1",
            public_key_spki_der=self.public_der, active=True,
            transport_certificate_sha256=self.transport_fingerprint,
            credential_generation=1,
        )
        self.registry = _Registry(self.enrollment)

    def tearDown(self):
        self.temp.cleanup()

    def envelope(self, challenge=None, signer=None):
        challenge = self.challenge if challenge is None else challenge
        signer = self.private_key if signer is None else signer
        signature = signer.sign(canonical_payload(challenge), ec.ECDSA(hashes.SHA256()))
        encoded = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
        payload = {
            "version": challenge.version,
            "device_id": challenge.device_id,
            "owner_id": challenge.owner_id,
            "session_id": challenge.session_id,
            "action": challenge.action,
            "nonce": challenge.nonce,
            "issued_at_epoch_ms": challenge.issued_at_epoch_ms,
            "expires_at_epoch_ms": challenge.expires_at_epoch_ms,
        }
        return json.dumps(
            {"payload": payload, "signature": encoded},
            separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")

    def verify(self, envelope=None, **changes):
        args = {
            "challenge": self.challenge,
            "trusted_public_key_spki_der": self.public_der,
            "transport_authenticated": True,
            "enrollment_registry": self.registry,
            "transport_certificate_sha256": self.transport_fingerprint,
            "credential_generation": 1,
            "ledger": self.ledger,
            "now_epoch_ms": self.now,
        }
        args.update(changes)
        return verify_and_consume(
            self.envelope() if envelope is None else envelope, **args
        )

    def test_shared_cross_platform_canonical_fixture(self):
        fixture = configparser.ConfigParser()
        with open(FIXTURE, encoding="ascii") as source:
            fixture.read_string("[fixture]\n" + source.read())
        values = fixture["fixture"]
        challenge = ConsentChallenge(
            version=int(values["version"]),
            device_id=values["device_id"],
            owner_id=values["owner_id"],
            session_id=values["session_id"],
            action=values["action"],
            nonce=values["nonce"],
            issued_at_epoch_ms=int(values["issued_at_epoch_ms"]),
            expires_at_epoch_ms=int(values["expires_at_epoch_ms"]),
        )
        self.assertEqual(canonical_payload(challenge).decode("ascii"), values["canonical"])

    def test_valid_p256_capability_is_admitted_without_execution(self):
        result = self.verify()
        self.assertTrue(result.admitted)
        self.assertEqual(result.reason, "ADMITTED_NO_EXECUTION")

    def test_nonce_is_one_use_and_persists_after_ledger_reopen(self):
        self.assertTrue(self.verify().admitted)
        reopened = DurableReplayLedger(self.db_path, ttl_seconds=60)
        result = self.verify(ledger=reopened)
        self.assertFalse(result.admitted)
        self.assertEqual(result.reason, "REPLAY_OR_CAPACITY")

    def test_consent_nonce_uses_a_separate_replay_namespace(self):
        # A command with the same textual ID cannot pre-consume a consent nonce.
        self.assertTrue(self.ledger.reserve(
            self.challenge.device_id, self.challenge.nonce, self.now // 1000
        ))
        result = self.verify()
        self.assertTrue(result.admitted)

    def test_unauthenticated_transport_is_rejected(self):
        result = self.verify(transport_authenticated=False)
        self.assertEqual(result.reason, "UNAUTHENTICATED")

    def test_host_challenge_fields_must_match_signed_payload(self):
        altered = replace(self.challenge, session_id="session-other")
        result = self.verify(self.envelope(challenge=altered))
        self.assertEqual(result.reason, "CHALLENGE_MISMATCH")

    def test_revoked_enrollment_is_rejected_without_consuming_nonce(self):
        self.registry.record = replace(self.enrollment, active=False)
        rejected = self.verify()
        self.assertEqual(rejected.reason, "ENROLLMENT_NOT_ACTIVE")
        self.registry.record = self.enrollment
        self.assertEqual(self.verify().reason, "ADMITTED_NO_EXECUTION")

    def test_rotated_transport_generation_is_rejected_without_consuming_nonce(self):
        self.registry.record = replace(
            self.enrollment,
            transport_certificate_sha256="b" * 64,
            credential_generation=2,
        )
        rejected = self.verify()
        self.assertEqual(rejected.reason, "ENROLLMENT_CREDENTIAL_MISMATCH")
        self.registry.record = self.enrollment
        self.assertEqual(self.verify().reason, "ADMITTED_NO_EXECUTION")

    def test_rotated_consent_key_is_rejected_without_consuming_nonce(self):
        other = ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.registry.record = replace(self.enrollment, public_key_spki_der=other)
        rejected = self.verify()
        self.assertEqual(rejected.reason, "ENROLLMENT_KEY_MISMATCH")
        self.registry.record = self.enrollment
        self.assertEqual(self.verify().reason, "ADMITTED_NO_EXECUTION")

    def test_registry_failure_fails_closed_without_consuming_nonce(self):
        rejected = self.verify(enrollment_registry=_Registry(fail=True))
        self.assertEqual(rejected.reason, "ENROLLMENT_REGISTRY_UNAVAILABLE")
        self.assertEqual(self.verify().reason, "ADMITTED_NO_EXECUTION")

    def test_revocation_observed_after_nonce_reservation_fails_closed(self):
        revoked = replace(self.enrollment, active=False)
        racing = _Registry(sequence=[self.enrollment, revoked])
        rejected = self.verify(enrollment_registry=racing)
        self.assertEqual(rejected.reason, "ENROLLMENT_CHANGED_DURING_VERIFICATION")
        self.assertEqual(self.verify().reason, "REPLAY_OR_CAPACITY")

    def test_expired_and_not_yet_valid_challenges_are_rejected(self):
        self.assertEqual(
            self.verify(now_epoch_ms=self.challenge.expires_at_epoch_ms).reason,
            "CHALLENGE_EXPIRED",
        )
        self.assertEqual(
            self.verify(now_epoch_ms=self.challenge.issued_at_epoch_ms - 1).reason,
            "CHALLENGE_EXPIRED",
        )

    def test_challenge_ttl_over_30_seconds_is_rejected(self):
        long_challenge = replace(
            self.challenge,
            expires_at_epoch_ms=self.challenge.issued_at_epoch_ms + MAX_CAPABILITY_TTL_MS + 1,
        )
        result = self.verify(b"{}", challenge=long_challenge)
        self.assertEqual(result.reason, "INVALID_CHALLENGE")

    def test_wrong_signing_key_is_rejected(self):
        other = ec.generate_private_key(ec.SECP256R1())
        result = self.verify(self.envelope(signer=other))
        self.assertEqual(result.reason, "BAD_SIGNATURE")

    def test_tampered_signature_is_rejected(self):
        envelope = json.loads(self.envelope())
        envelope["signature"] = ("A" if envelope["signature"][0] != "A" else "B") + envelope["signature"][1:]
        result = self.verify(json.dumps(envelope, separators=(",", ":")).encode())
        self.assertEqual(result.reason, "BAD_SIGNATURE")

    def test_rsa_and_wrong_curve_keys_are_rejected(self):
        rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        rsa_der = rsa_key.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.assertEqual(self.verify(trusted_public_key_spki_der=rsa_der).reason, "INVALID_TRUSTED_KEY")
        p384 = ec.generate_private_key(ec.SECP384R1()).public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.assertEqual(self.verify(trusted_public_key_spki_der=p384).reason, "INVALID_TRUSTED_KEY")

    def test_invalid_or_untrusted_key_bytes_are_rejected(self):
        self.assertEqual(self.verify(trusted_public_key_spki_der=b"bad").reason, "INVALID_TRUSTED_KEY")
        self.assertEqual(self.verify(trusted_public_key_spki_der=b"").reason, "INVALID_TRUSTED_KEY")
        self.assertEqual(self.verify(trusted_public_key_spki_der=b"x" * 513).reason, "INVALID_TRUSTED_KEY")

    def test_duplicate_json_keys_are_rejected(self):
        result = self.verify(b'{"payload":{"version":1,"version":1},"signature":"AAAAAAAA"}')
        self.assertEqual(result.reason, "INVALID_ENVELOPE")

    def test_extra_envelope_or_payload_fields_are_rejected(self):
        outer = json.loads(self.envelope())
        outer["extra"] = True
        self.assertEqual(
            self.verify(json.dumps(outer, separators=(",", ":")).encode()).reason,
            "INVALID_ENVELOPE",
        )
        outer = json.loads(self.envelope())
        outer["payload"]["extra"] = True
        self.assertEqual(
            self.verify(json.dumps(outer, separators=(",", ":")).encode()).reason,
            "INVALID_ENVELOPE",
        )

    def test_malformed_json_utf8_and_oversized_envelopes_are_rejected(self):
        self.assertEqual(self.verify(b"\xff").reason, "INVALID_ENVELOPE")
        self.assertEqual(self.verify(b"{" + b" " * 4096).reason, "INVALID_ENVELOPE")
        self.assertEqual(self.verify(b"x" * 4097).reason, "INVALID_ENVELOPE")

    def test_ledger_window_must_cover_maximum_capability_ttl(self):
        short = DurableReplayLedger(os.path.join(self.temp.name, "short.sqlite"), ttl_seconds=29)
        self.assertEqual(self.verify(ledger=short).reason, "REPLAY_WINDOW_TOO_SHORT")

    def test_ledger_failure_fails_closed(self):
        self.ledger.path = os.path.join(self.temp.name, "missing", "ledger.sqlite")
        self.assertEqual(self.verify().reason, "LEDGER_UNAVAILABLE")

    def test_bool_timestamp_or_version_cannot_masquerade_as_integer(self):
        outer = json.loads(self.envelope())
        outer["payload"]["version"] = True
        result = self.verify(json.dumps(outer, separators=(",", ":")).encode())
        self.assertEqual(result.reason, "CHALLENGE_MISMATCH")

    def test_invalid_action_or_short_nonce_challenge_is_rejected(self):
        bad_action = replace(self.challenge, action="open_app")
        self.assertEqual(
            self.verify(b"{}", challenge=bad_action).reason,
            "INVALID_CHALLENGE",
        )
        short_nonce = replace(self.challenge, nonce="short")
        self.assertEqual(
            self.verify(b"{}", challenge=short_nonce).reason,
            "INVALID_CHALLENGE",
        )


if __name__ == "__main__":
    unittest.main()
