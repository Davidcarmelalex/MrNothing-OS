"""SEC-023A synthetic-only canonical schema and AAD negative fixtures."""
import base64
import json
import unittest

from core.memory_vault_schema import (
    EnvelopeError, MAX_CIPHERTEXT_BYTES, canonical_aad,
    encode_envelope, parse_envelope, preflight_record,
)


def b64(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def fixture():
    return {
        "format_version": 1,
        "vault_id": b64(bytes(range(16))),
        "record_id": b64(bytes(range(16, 32))),
        "generation": 4,
        "created_at": 1_800_000_000,
        "expires_at": 1_800_086_400,
        "key_version": 2,
        "nonce": b64(bytes(range(12))),
        "ciphertext": b64(b"synthetic encrypted bytes, not actual AEAD"),
        "tag": b64(bytes(range(16))),
    }


APP_ID = "a" * 64
OWNER = "user:0"


class MemoryVaultSchemaTests(unittest.TestCase):
    def test_canonical_round_trip_and_deterministic_vector(self):
        record = fixture()
        raw = encode_envelope(record)
        self.assertEqual(parse_envelope(raw), record)
        self.assertEqual(raw, encode_envelope(dict(reversed(list(record.items())))))
        self.assertEqual(raw, json.dumps(record, sort_keys=True, separators=(",", ":")).encode())

    def test_noncanonical_json_and_duplicate_keys_rejected(self):
        raw = encode_envelope(fixture())
        for candidate in (b" " + raw, raw + b"\n", json.dumps(fixture()).encode(),
                          raw.replace(b'"tag":', b'"tag":"bogus","tag":', 1)):
            with self.subTest(candidate=candidate[:40]), self.assertRaises(EnvelopeError):
                parse_envelope(candidate)

    def test_unknown_missing_nested_and_boolean_integer_rejected(self):
        for change in ("extra", "missing", "nested", "boolean"):
            obj = fixture()
            if change == "extra":
                obj["untrusted"] = "x"
            elif change == "missing":
                del obj["tag"]
            elif change == "nested":
                obj["generation"] = {"x": 4}
            else:
                obj["generation"] = True
            with self.subTest(change=change), self.assertRaises(EnvelopeError):
                encode_envelope(obj)

    def test_invalid_utf8_and_oversized_bytes_rejected(self):
        for raw in (b"\xff", b"", b" " * 100001, "text", bytearray(b"{}")):
            with self.subTest(raw=type(raw)), self.assertRaises(EnvelopeError):
                parse_envelope(raw)

    def test_noncanonical_base64_and_wrong_binary_lengths_rejected(self):
        for field, value in (
            ("vault_id", "AAAA"), ("record_id", "AAAA"), ("nonce", "AAAA"),
            ("tag", "AAAA"), ("ciphertext", "a"), ("nonce", "AAAAAAAAAAAAAAA="),
            ("nonce", "AAAAAAAAAAAAAAA+"), ("ciphertext", b64(b"x" * (MAX_CIPHERTEXT_BYTES + 1))),
        ):
            obj = fixture()
            obj[field] = value
            with self.subTest(field=field, value=value[:12]), self.assertRaises(EnvelopeError):
                encode_envelope(obj)

    def test_timestamps_ttl_and_generation_bounds(self):
        for field, value in (
            ("created_at", 0), ("expires_at", 1_800_000_000),
            ("expires_at", 1_800_000_000 + 91 * 86400),
            ("generation", 0), ("generation", 2**63),
            ("key_version", -1), ("format_version", 2),
        ):
            obj = fixture()
            obj[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(EnvelopeError):
                encode_envelope(obj)

    def test_aad_canonical_vector_binds_trusted_identity(self):
        obj = fixture()
        aad = canonical_aad(obj, owner_profile_id=OWNER, application_identity=APP_ID)
        expected = {
            "application_identity": APP_ID, "format_version": 1,
            "generation": 4, "key_version": 2, "owner_profile_id": OWNER,
            "record_id": obj["record_id"], "vault_id": obj["vault_id"],
        }
        self.assertEqual(aad, json.dumps(expected, sort_keys=True, separators=(",", ":")).encode())
        self.assertNotEqual(aad, canonical_aad(obj, owner_profile_id="user:10", application_identity=APP_ID))
        self.assertNotEqual(aad, canonical_aad(obj, owner_profile_id=OWNER, application_identity="b" * 64))
        changed = dict(obj, generation=5)
        self.assertNotEqual(aad, canonical_aad(changed, owner_profile_id=OWNER, application_identity=APP_ID))

    def test_aad_rejects_untrusted_identity_formats(self):
        for owner, app in ((True, APP_ID), ("user/0", APP_ID), (OWNER, "A" * 64),
                           (OWNER, "a" * 63), (OWNER, None)):
            with self.subTest(owner=owner, app=app), self.assertRaises(EnvelopeError):
                canonical_aad(fixture(), owner_profile_id=owner, application_identity=app)

    def test_preflight_rejects_swaps_replay_and_nonce_reuse(self):
        obj = fixture()
        args = dict(expected_vault_id=obj["vault_id"], expected_record_id=obj["record_id"],
                    last_accepted_generation=3, seen_key_nonces=set(), trusted_now=1_800_000_010,
                    owner_profile_id=OWNER, application_identity=APP_ID)
        self.assertEqual(preflight_record(obj, **args), canonical_aad(
            obj, owner_profile_id=OWNER, application_identity=APP_ID))
        for override in (
            {"expected_vault_id": b64(b"Z" * 16)},
            {"expected_record_id": b64(b"Y" * 16)},
            {"last_accepted_generation": 4},
            {"last_accepted_generation": 5},
            {"seen_key_nonces": {(2, obj["nonce"])}},
        ):
            with self.subTest(override=override), self.assertRaises(EnvelopeError):
                preflight_record(obj, **(args | override))

    def test_preflight_rejects_expired_future_and_untrusted_clock(self):
        obj = fixture()
        args = dict(expected_vault_id=obj["vault_id"], expected_record_id=obj["record_id"],
                    last_accepted_generation=3, seen_key_nonces=set(),
                    owner_profile_id=OWNER, application_identity=APP_ID)
        for trusted_now in (obj["expires_at"], obj["expires_at"] + 1,
                            obj["created_at"] - 301, True, 0):
            with self.subTest(trusted_now=trusted_now), self.assertRaises(EnvelopeError):
                preflight_record(obj, trusted_now=trusted_now, **args)

    def test_preflight_never_mutates_ledger_or_claims_tag_verification(self):
        obj = fixture()
        seen = {(1, "unrelated")}
        before = seen.copy()
        preflight_record(obj, expected_vault_id=obj["vault_id"],
                         expected_record_id=obj["record_id"], last_accepted_generation=3,
                         seen_key_nonces=seen, trusted_now=1_800_000_010, owner_profile_id=OWNER,
                         application_identity=APP_ID)
        self.assertEqual(seen, before)
        tampered = dict(obj, tag=b64(b"Z" * 16))
        # Deliberately schema-valid: AEAD tag verification belongs to SEC-023D.
        self.assertEqual(parse_envelope(encode_envelope(tampered)), tampered)


if __name__ == "__main__":
    unittest.main()
