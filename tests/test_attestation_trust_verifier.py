import base64
import hashlib
import json
import unittest
from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.x509.oid import NameOID

from core.attestation_trust_verifier import (
    ManifestVerificationError,
    verify_trust_manifest,
)

NOW = datetime(2026, 11, 5, 3, 0, tzinfo=timezone.utc)


def make_ca_der(*, ca=True, key_cert_sign=True, include_key_usage=True):
    ca_key = Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Synthetic Test Root")])
    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime(2025, 1, 1))
        .not_valid_after(datetime(2035, 1, 1))
        .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
    )
    if include_key_usage:
        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=key_cert_sign,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
    cert = builder.sign(ca_key, algorithm=None)
    return cert.public_bytes(serialization.Encoding.DER)


def build_manifest(signer, *, root_der=None, bundle_version=8,
                   not_before="2026-11-04T00:00:00Z",
                   not_after="2027-11-04T00:00:00Z",
                   signing_key_id="release-key-1"):
    root_der = make_ca_der() if root_der is None else root_der
    unsigned = {
        "schema": "mrnothing.android-attestation-trust-bundle",
        "schema_version": 1,
        "bundle_version": bundle_version,
        "issued_at": "2026-11-01T00:00:00Z",
        "not_before": not_before,
        "not_after": not_after,
        "signing_key_id": signing_key_id,
        "roots": [{
            "id": "test-root",
            "certificate_der": base64.b64encode(root_der).decode("ascii"),
            "sha256": hashlib.sha256(root_der).hexdigest(),
        }],
    }
    canonical = json.dumps(
        unsigned, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    signature = signer.sign(canonical)
    document = dict(unsigned)
    document["signature"] = {
        "algorithm": "Ed25519",
        "value": base64.b64encode(signature).decode("ascii"),
    }
    return json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class AttestationTrustVerifierTests(unittest.TestCase):
    def setUp(self):
        self.signer = Ed25519PrivateKey.generate()
        self.public_bytes = self.signer.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        self.raw = build_manifest(self.signer)

    def call_verify(self, raw=None, keys=None, version=7, now=NOW):
        return verify_trust_manifest(
            self.raw if raw is None else raw,
            pinned_update_keys={"release-key-1": self.public_bytes} if keys is None else keys,
            current_version=version,
            now=now,
        )

    def test_valid_signature_and_ca_shape_are_accepted(self):
        result = self.call_verify()
        self.assertEqual(result.signing_key_id, "release-key-1")
        self.assertEqual(result.manifest.bundle_version, 8)
        self.assertEqual(result.signing_key_sha256, hashlib.sha256(self.public_bytes).hexdigest())

    def test_wrong_update_key_is_rejected(self):
        wrong = Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(keys={"release-key-1": wrong})

    def test_unknown_key_id_is_rejected_without_fallback(self):
        raw = build_manifest(self.signer, signing_key_id="unlisted-key")
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(raw=raw)

    def test_tampered_payload_signature_is_rejected(self):
        document = json.loads(self.raw)
        document["bundle_version"] = 9
        raw = json.dumps(document, separators=(",", ":")).encode("utf-8")
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(raw=raw)

    def test_equal_version_is_rejected_as_replay(self):
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(version=8)

    def test_older_version_is_rejected_as_rollback(self):
        raw = build_manifest(self.signer, bundle_version=7)
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(raw=raw, version=8)

    def test_not_yet_valid_manifest_is_rejected(self):
        raw = build_manifest(self.signer, not_before="2027-01-01T00:00:00Z")
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(raw=raw)

    def test_expired_manifest_is_rejected(self):
        raw = build_manifest(
            self.signer,
            not_before="2026-11-01T00:00:00Z",
            not_after="2026-11-04T00:00:00Z",
        )
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(raw=raw)

    def test_naive_verification_time_is_rejected(self):
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(now=datetime(2026, 11, 5, 3, 0))

    def test_invalid_key_length_is_rejected(self):
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(keys={"release-key-1": b"short"})

    def test_invalid_der_is_rejected_after_signature(self):
        raw = build_manifest(self.signer, root_der=b"not an X.509 certificate")
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(raw=raw)

    def test_non_ca_certificate_is_rejected(self):
        raw = build_manifest(
            self.signer,
            root_der=make_ca_der(ca=False, key_cert_sign=False),
        )
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(raw=raw)

    def test_missing_key_usage_is_rejected(self):
        raw = build_manifest(
            self.signer,
            root_der=make_ca_der(include_key_usage=False),
        )
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(raw=raw)

    def test_ca_without_key_cert_sign_is_rejected(self):
        raw = build_manifest(
            self.signer,
            root_der=make_ca_der(key_cert_sign=False),
        )
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(raw=raw)

    def test_bool_current_version_is_rejected(self):
        with self.assertRaises(ManifestVerificationError):
            self.call_verify(version=True)


if __name__ == "__main__":
    unittest.main()
