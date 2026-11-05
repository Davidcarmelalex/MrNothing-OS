"""Deterministic adversarial corpus for the AGENT-004A consent envelope parser.

All keys, identities, challenges and signatures are synthetic. These tests never
grant permissions or execute device actions.
"""
import base64
import json
import os
import tempfile
import unittest

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from core.command_admission import DurableReplayLedger
from core.owner_consent_issuer import EnrolledOwnerDevice
from core.owner_consent_protocol import (
    ConsentChallenge,
    MAX_ENVELOPE_BYTES,
    canonical_payload,
    verify_and_consume,
)


class _Registry:
    def __init__(self, record):
        self.record = record

    def lookup_active_device(self, device_id):
        if self.record is None or self.record.device_id != device_id:
            return None
        return self.record


class OwnerConsentParserMutationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = self._new_ledger("default.sqlite")
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
        self.registry = _Registry(EnrolledOwnerDevice(
            owner_id="owner-1", device_id="pixel9pro-1",
            public_key_spki_der=self.public_der, active=True,
            transport_certificate_sha256=self.transport_fingerprint,
            credential_generation=1,
        ))

    def tearDown(self):
        self.temp.cleanup()

    def _new_ledger(self, name):
        return DurableReplayLedger(
            os.path.join(self.temp.name, name), ttl_seconds=60
        )

    def _payload(self):
        return {
            "version": self.challenge.version,
            "device_id": self.challenge.device_id,
            "owner_id": self.challenge.owner_id,
            "session_id": self.challenge.session_id,
            "action": self.challenge.action,
            "nonce": self.challenge.nonce,
            "issued_at_epoch_ms": self.challenge.issued_at_epoch_ms,
            "expires_at_epoch_ms": self.challenge.expires_at_epoch_ms,
        }

    def _outer(self):
        signature = self.private_key.sign(
            canonical_payload(self.challenge), ec.ECDSA(hashes.SHA256())
        )
        encoded = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
        return {"payload": self._payload(), "signature": encoded}

    @staticmethod
    def _encode(outer):
        return json.dumps(
            outer, separators=(",", ":"), ensure_ascii=True, allow_nan=True
        ).encode("ascii")

    def _verify(self, envelope, *, ledger=None):
        return verify_and_consume(
            envelope,
            challenge=self.challenge,
            trusted_public_key_spki_der=self.public_der,
            transport_authenticated=True,
            enrollment_registry=self.registry,
            transport_certificate_sha256=self.transport_fingerprint,
            credential_generation=1,
            ledger=self.ledger if ledger is None else ledger,
            now_epoch_ms=self.now,
        )

    def test_valid_json_whitespace_and_exact_size_boundary(self):
        outer = self._outer()
        pretty = json.dumps(outer, indent=2, ensure_ascii=True).encode("ascii")
        self.assertEqual(self._verify(pretty).reason, "ADMITTED_NO_EXECUTION")

        compact = self._encode(self._outer())
        self.assertLess(len(compact), MAX_ENVELOPE_BYTES)
        exact_limit = compact + b" " * (MAX_ENVELOPE_BYTES - len(compact))
        self.assertEqual(len(exact_limit), MAX_ENVELOPE_BYTES)
        result = self._verify(exact_limit, ledger=self._new_ledger("max.sqlite"))
        self.assertEqual(result.reason, "ADMITTED_NO_EXECUTION")

    def test_malformed_outer_framing_corpus_fails_closed(self):
        valid = self._encode(self._outer())
        deeply_nested = b"[" * 1100 + b"0" + b"]" * 1100
        corpus = (
            b"",
            b" ",
            b"\x00",
            b"\xff",
            b"\xef\xbb\xbf" + valid,
            b"[]",
            b"null",
            b"true",
            b"0",
            b'{"payload":{},"signature":"AAAAAAAA","signature":"BBBBBBBB"}',
            b'{"payload":{"version":1,"version":1},"signature":"AAAAAAAA"}',
            b'{"payload":NaN,"signature":"AAAAAAAA"}',
            b'{"payload":{},"signature":"AAAAAAAA","extra":0}',
            b'{"payload":{},"signature":7}',
            b'{"payload":[],"signature":"AAAAAAAA"}',
            deeply_nested,
            b" " * (MAX_ENVELOPE_BYTES + 1),
            bytearray(valid),
            memoryview(valid),
        )
        for index, envelope in enumerate(corpus):
            with self.subTest(index=index):
                result = self._verify(envelope)
                self.assertFalse(result.admitted)
                self.assertEqual(result.reason, "INVALID_ENVELOPE")

    def test_payload_type_confusion_and_field_set_mutations_fail_closed(self):
        mutations = (
            ("version", True),
            ("version", 1.0),
            ("device_id", ["pixel9pro-1"]),
            ("owner_id", None),
            ("session_id", 1),
            ("action", "navigate"),
            ("nonce", "f" * 32),
            ("issued_at_epoch_ms", self.challenge.issued_at_epoch_ms + 1),
            ("expires_at_epoch_ms", 10**1000),
        )
        for field, value in mutations:
            with self.subTest(field=field, value_type=type(value).__name__):
                outer = self._outer()
                outer["payload"][field] = value
                result = self._verify(self._encode(outer))
                self.assertFalse(result.admitted)

        missing = self._outer()
        del missing["payload"]["owner_id"]
        self.assertEqual(self._verify(self._encode(missing)).reason, "INVALID_ENVELOPE")

        extra = self._outer()
        extra["payload"]["unexpected"] = "value"
        self.assertEqual(self._verify(self._encode(extra)).reason, "INVALID_ENVELOPE")

        outer_extra = self._outer()
        outer_extra["unexpected"] = "value"
        self.assertEqual(self._verify(self._encode(outer_extra)).reason, "INVALID_ENVELOPE")

    def test_non_finite_json_numbers_fail_closed(self):
        for field in ("issued_at_epoch_ms", "expires_at_epoch_ms"):
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(field=field, value=value):
                    outer = self._outer()
                    outer["payload"][field] = value
                    result = self._verify(self._encode(outer))
                    self.assertFalse(result.admitted)
                    self.assertEqual(result.reason, "INVALID_ENVELOPE")

    def test_signature_encoding_and_der_mutations_fail_closed(self):
        invalid_values = (
            "",
            "A" * 8,
            "A" * 97,
            "A" * 128,
            "A" * 8 + "=",
            "A" * 8 + "+",
            "A" * 8 + "/",
            "A" * 8 + " ",
            "é" * 8,
            None,
        )
        for index, value in enumerate(invalid_values):
            with self.subTest(index=index):
                outer = self._outer()
                outer["signature"] = value
                self.assertFalse(self._verify(self._encode(outer)).admitted)

        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        canonical = base64.urlsafe_b64encode(b"12345678").rstrip(b"=").decode("ascii")
        last_index = alphabet.index(canonical[-1])
        self.assertEqual(last_index & 0x0F, 0)
        noncanonical_pad_bits = canonical[:-1] + alphabet[last_index | 1]
        outer = self._outer()
        outer["signature"] = noncanonical_pad_bits
        self.assertEqual(
            self._verify(self._encode(outer)).reason,
            "INVALID_SIGNATURE_ENCODING",
        )

        malformed_der = base64.urlsafe_b64encode(b"not-der!").rstrip(b"=").decode("ascii")
        outer = self._outer()
        outer["signature"] = malformed_der
        self.assertFalse(self._verify(self._encode(outer)).admitted)

    def test_every_signature_character_mutation_fails_without_consuming_nonce(self):
        original = self._outer()
        signature = original["signature"]
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

        for index, char in enumerate(signature):
            replacement = alphabet[(alphabet.index(char) + 1) % len(alphabet)]
            mutated = dict(original)
            mutated["signature"] = signature[:index] + replacement + signature[index + 1:]
            with self.subTest(signature_character=index):
                self.assertFalse(self._verify(self._encode(mutated)).admitted)

        # Every mutation above must fail before the one-use nonce is reserved.
        valid = self._verify(self._encode(original))
        self.assertEqual(valid.reason, "ADMITTED_NO_EXECUTION")


if __name__ == "__main__":
    unittest.main()
