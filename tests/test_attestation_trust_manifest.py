import base64
import hashlib
import json
import unittest

from core.attestation_trust_manifest import (
    MAX_CERTIFICATE_BYTES,
    MAX_MANIFEST_BYTES,
    ManifestError,
    parse_trust_manifest,
)


def sample_manifest():
    # Intentionally not an X.509 certificate and never a production trust root.
    der = b"synthetic-only-not-a-real-certificate"
    return {
        "schema": "mrnothing.android-attestation-trust-bundle",
        "schema_version": 1,
        "bundle_version": 7,
        "issued_at": "2026-11-05T00:00:00Z",
        "not_before": "2026-11-05T00:00:00Z",
        "not_after": "2027-11-05T00:00:00Z",
        "signing_key_id": "release-key-1",
        "roots": [{
            "id": "android-root-test",
            "certificate_der": base64.b64encode(der).decode("ascii"),
            "sha256": hashlib.sha256(der).hexdigest(),
        }],
        "signature": {
            "algorithm": "Ed25519",
            "value": base64.b64encode(b"\x01" * 64).decode("ascii"),
        },
    }


class AttestationTrustManifestTests(unittest.TestCase):
    def raw(self, document=None):
        return json.dumps(
            sample_manifest() if document is None else document
        ).encode("utf-8")

    def test_valid_synthetic_envelope_is_parsed_but_not_verified(self):
        parsed = parse_trust_manifest(self.raw())
        self.assertEqual(parsed.bundle_version, 7)
        self.assertEqual(parsed.signing_key_id, "release-key-1")
        self.assertEqual(len(parsed.roots), 1)
        self.assertNotIn(b'"signature"', parsed.canonical_payload)

    def test_canonical_payload_is_independent_of_json_key_order(self):
        document = sample_manifest()
        reordered = dict(reversed(list(document.items())))
        self.assertEqual(
            parse_trust_manifest(self.raw(document)).canonical_payload,
            parse_trust_manifest(self.raw(reordered)).canonical_payload,
        )

    def test_duplicate_json_object_key_is_rejected(self):
        with self.assertRaises(ManifestError):
            parse_trust_manifest(b'{"schema":"one","schema":"two"}')

    def test_invalid_utf8_is_rejected(self):
        with self.assertRaises(ManifestError):
            parse_trust_manifest(b"\xff")

    def test_unpaired_unicode_surrogate_is_rejected(self):
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw().replace(
                b"release-key-1", b"release-\\ud800"
            ))

    def test_non_finite_json_number_is_rejected(self):
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw().replace(
                b'"bundle_version": 7', b'"bundle_version": NaN'
            ))

    def test_unknown_top_level_field_is_rejected(self):
        document = sample_manifest()
        document["unexpected"] = 1
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_boolean_bundle_version_is_rejected(self):
        document = sample_manifest()
        document["bundle_version"] = True
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_non_positive_bundle_version_is_rejected(self):
        document = sample_manifest()
        document["bundle_version"] = 0
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_unsupported_schema_version_is_rejected(self):
        document = sample_manifest()
        document["schema_version"] = 2
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_non_utc_timestamp_is_rejected(self):
        document = sample_manifest()
        document["issued_at"] = "2026-11-05T00:00:00+00:00"
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_invalid_time_interval_is_rejected(self):
        document = sample_manifest()
        document["not_before"] = "2028-01-01T00:00:00Z"
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_unknown_root_field_is_rejected(self):
        document = sample_manifest()
        document["roots"][0]["subject"] = "unverified metadata"
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_root_fingerprint_mismatch_is_rejected(self):
        document = sample_manifest()
        document["roots"][0]["sha256"] = "0" * 64
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_duplicate_root_id_is_rejected(self):
        document = sample_manifest()
        document["roots"].append(dict(document["roots"][0]))
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_duplicate_root_fingerprint_is_rejected(self):
        document = sample_manifest()
        second = dict(document["roots"][0])
        second["id"] = "second-root"
        document["roots"].append(second)
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_malformed_certificate_base64_is_rejected(self):
        document = sample_manifest()
        document["roots"][0]["certificate_der"] = "%%%="
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_oversized_certificate_is_rejected(self):
        document = sample_manifest()
        der = b"x" * (MAX_CERTIFICATE_BYTES + 1)
        document["roots"][0]["certificate_der"] = base64.b64encode(der).decode()
        document["roots"][0]["sha256"] = hashlib.sha256(der).hexdigest()
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_wrong_signature_length_is_rejected(self):
        document = sample_manifest()
        document["signature"]["value"] = base64.b64encode(b"x").decode()
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_unsupported_signature_algorithm_is_rejected(self):
        document = sample_manifest()
        document["signature"]["algorithm"] = "RSA"
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_empty_root_list_is_rejected(self):
        document = sample_manifest()
        document["roots"] = []
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_nine_roots_are_rejected(self):
        document = sample_manifest()
        root = document["roots"][0]
        document["roots"] = [
            dict(root, id=f"root-{index}") for index in range(9)
        ]
        with self.assertRaises(ManifestError):
            parse_trust_manifest(self.raw(document))

    def test_bundle_version_must_advance_persisted_state(self):
        parsed = parse_trust_manifest(self.raw())
        self.assertTrue(parsed.is_newer_than(6))
        self.assertFalse(parsed.is_newer_than(7))
        with self.assertRaises(ValueError):
            parsed.is_newer_than(True)

    def test_oversized_manifest_is_rejected(self):
        with self.assertRaises(ManifestError):
            parse_trust_manifest(b"x" * (MAX_MANIFEST_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
