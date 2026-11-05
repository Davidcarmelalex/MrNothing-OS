"""AGENT-004E: synthetic end-to-end owner-consent flow; never executes actions."""
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
import tempfile
import unittest
from dataclasses import replace

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from core.command_admission import DurableReplayLedger
from core.owner_consent_issuer import (
    AuthenticatedOwnerSession,
    EnrolledOwnerDevice,
    issue_owner_consent_challenge,
)
from core.owner_consent_protocol import canonical_payload, verify_and_consume


NOW = 1_700_000_000_000
NONCE = "0123456789abcdef0123456789abcdef"


class _Registry:
    def __init__(self, record=None, *, fail=False):
        self.record = record
        self.fail = fail

    def lookup_active_device(self, device_id):
        if self.fail:
            raise OSError("synthetic registry failure")
        if self.record is None or self.record.device_id != device_id:
            return None
        return self.record


class OwnerConsentFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger_path = os.path.join(self.temp.name, "consent-replay.sqlite")
        self.ledger = DurableReplayLedger(self.ledger_path, ttl_seconds=60)
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_der = self.private_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.record = EnrolledOwnerDevice(
            owner_id="owner-1",
            device_id="pixel9pro-1",
            public_key_spki_der=self.public_der,
            transport_certificate_sha256="a" * 64,
            credential_generation=1,
        )
        self.session = AuthenticatedOwnerSession(
            owner_id="owner-1",
            device_id="pixel9pro-1",
            session_id="session-1",
            authenticated_at_epoch_ms=NOW - 1_000,
            expires_at_epoch_ms=NOW + 60_000,
            transport_certificate_sha256="a" * 64,
            credential_generation=1,
        )
        self.issued = self.issue()

    def tearDown(self):
        self.temp.cleanup()

    def issue(self, *, session=None, record=None, registry=None, nonce=NONCE):
        selected_session = self.session if session is None and hasattr(self, "session") else session
        if selected_session is None:
            raise AssertionError("test session was not initialized")
        selected_registry = registry if registry is not None else _Registry(
            self.record if record is None and hasattr(self, "record") else record
        )
        return issue_owner_consent_challenge(
            selected_session,
            action="read_screen",
            registry=selected_registry,
            now_epoch_ms=NOW,
            nonce_factory=lambda _size: nonce,
        )

    def envelope(self, challenge, *, signer=None):
        signing_key = self.private_key if signer is None else signer
        signature_der = signing_key.sign(
            canonical_payload(challenge),
            ec.ECDSA(hashes.SHA256()),
        )
        signature = base64.urlsafe_b64encode(signature_der).rstrip(b"=").decode("ascii")
        payload = json.loads(canonical_payload(challenge).decode("ascii"))
        return json.dumps(
            {"payload": payload, "signature": signature},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")

    def verify(self, envelope, *, issued=None, ledger=None, now=NOW + 1,
               authenticated=True, registry=None):
        capability = self.issued if issued is None else issued
        return verify_and_consume(
            envelope,
            challenge=capability.capability.challenge,
            trusted_public_key_spki_der=capability.capability.trusted_public_key_spki_der,
            transport_authenticated=authenticated,
            enrollment_registry=_Registry(self.record) if registry is None else registry,
            transport_certificate_sha256=self.session.transport_certificate_sha256,
            credential_generation=self.session.credential_generation,
            ledger=self.ledger if ledger is None else ledger,
            now_epoch_ms=now,
        )

    def test_issuer_signer_verifier_flow_admits_without_execution(self):
        self.assertTrue(self.issued.issued)
        challenge = self.issued.capability.challenge
        result = self.verify(self.envelope(challenge))
        self.assertTrue(result.admitted)
        self.assertEqual(result.reason, "ADMITTED_NO_EXECUTION")

    def test_replay_remains_rejected_after_sqlite_ledger_reopen(self):
        challenge = self.issued.capability.challenge
        signed = self.envelope(challenge)
        self.assertTrue(self.verify(signed).admitted)
        reopened = DurableReplayLedger(self.ledger_path, ttl_seconds=60)
        result = self.verify(signed, ledger=reopened)
        self.assertFalse(result.admitted)
        self.assertEqual(result.reason, "REPLAY_OR_CAPACITY")

    def test_concurrent_replay_admits_exactly_once(self):
        signed = self.envelope(self.issued.capability.challenge)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.verify(signed), range(16)))
        self.assertEqual(sum(result.admitted for result in results), 1)
        self.assertTrue(all(
            result.reason in {"ADMITTED_NO_EXECUTION", "REPLAY_OR_CAPACITY"}
            for result in results
        ))

    def test_tampered_signature_does_not_consume_the_valid_challenge(self):
        signed = json.loads(self.envelope(self.issued.capability.challenge))
        original = signed["signature"]
        signed["signature"] = ("A" if original[0] != "A" else "B") + original[1:]
        tampered = json.dumps(signed, separators=(",", ":")).encode("ascii")
        rejected = self.verify(tampered)
        self.assertFalse(rejected.admitted)
        self.assertEqual(rejected.reason, "BAD_SIGNATURE")
        self.assertTrue(self.verify(self.envelope(self.issued.capability.challenge)).admitted)

    def test_wrong_private_key_does_not_admit(self):
        wrong_key = ec.generate_private_key(ec.SECP256R1())
        rejected = self.verify(self.envelope(
            self.issued.capability.challenge, signer=wrong_key
        ))
        self.assertFalse(rejected.admitted)
        self.assertEqual(rejected.reason, "BAD_SIGNATURE")
        self.assertTrue(self.verify(self.envelope(self.issued.capability.challenge)).admitted)

    def test_unauthenticated_transport_is_rejected_without_consuming_nonce(self):
        signed = self.envelope(self.issued.capability.challenge)
        rejected = self.verify(signed, authenticated=False)
        self.assertFalse(rejected.admitted)
        self.assertEqual(rejected.reason, "UNAUTHENTICATED")
        self.assertTrue(self.verify(signed).admitted)

    def test_revocation_after_challenge_issuance_blocks_verification(self):
        signed = self.envelope(self.issued.capability.challenge)
        self.record = replace(self.record, active=False)
        rejected = self.verify(signed)
        self.assertFalse(rejected.admitted)
        self.assertEqual(rejected.reason, "ENROLLMENT_NOT_ACTIVE")
        self.record = replace(self.record, active=True)
        self.assertTrue(self.verify(signed).admitted)

    def test_credential_rotation_after_issuance_blocks_old_session(self):
        signed = self.envelope(self.issued.capability.challenge)
        self.record = replace(
            self.record,
            transport_certificate_sha256="b" * 64,
            credential_generation=2,
        )
        rejected = self.verify(signed)
        self.assertFalse(rejected.admitted)
        self.assertEqual(rejected.reason, "ENROLLMENT_CREDENTIAL_MISMATCH")

    def test_session_expiry_caps_challenge_and_verifier_window(self):
        short_session = replace(
            self.session,
            session_id="short-session",
            expires_at_epoch_ms=NOW + 500,
        )
        issued = self.issue(session=short_session, nonce="fedcba9876543210fedcba9876543210")
        self.assertTrue(issued.issued)
        challenge = issued.capability.challenge
        self.assertEqual(challenge.expires_at_epoch_ms, short_session.expires_at_epoch_ms)
        signed = self.envelope(challenge)
        expired = self.verify(signed, issued=issued, now=challenge.expires_at_epoch_ms)
        self.assertFalse(expired.admitted)
        self.assertEqual(expired.reason, "CHALLENGE_EXPIRED")
        valid = self.verify(signed, issued=issued, now=challenge.expires_at_epoch_ms - 1)
        self.assertTrue(valid.admitted)

    def test_owner_device_mismatch_is_rejected_before_challenge_issuance(self):
        wrong_record = replace(self.record, owner_id="owner-other")
        result = self.issue(record=wrong_record, nonce="11111111111111111111111111111111")
        self.assertFalse(result.issued)
        self.assertEqual(result.reason, "OWNER_DEVICE_MISMATCH")

    def test_registry_failure_fails_closed_before_challenge_issuance(self):
        result = self.issue(
            registry=_Registry(fail=True),
            nonce="22222222222222222222222222222222",
        )
        self.assertFalse(result.issued)
        self.assertEqual(result.reason, "REGISTRY_UNAVAILABLE")

    def test_replay_ledger_failure_fails_closed(self):
        signed = self.envelope(self.issued.capability.challenge)
        self.ledger.path = os.path.join(self.temp.name, "missing", "ledger.sqlite")
        result = self.verify(signed)
        self.assertFalse(result.admitted)
        self.assertEqual(result.reason, "LEDGER_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
