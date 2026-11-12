"""Synthetic SEC-016 test material. Never production trust material."""
import base64
import hashlib
import json
from datetime import datetime

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.x509.oid import NameOID


def make_ca_der():
    ca_key = Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Synthetic Test Root")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name).issuer_name(name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime(2025, 1, 1))
        .not_valid_after(datetime(2035, 1, 1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=False, content_commitment=False,
                key_encipherment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=True, crl_sign=True,
                encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, algorithm=None)
    )
    return cert.public_bytes(serialization.Encoding.DER)


def build_manifest(signer, *, bundle_version, root_der=None):
    root_der = make_ca_der() if root_der is None else root_der
    unsigned = {
        "schema": "mrnothing.android-attestation-trust-bundle",
        "schema_version": 1,
        "bundle_version": bundle_version,
        "issued_at": "2026-11-01T00:00:00Z",
        "not_before": "2026-11-04T00:00:00Z",
        "not_after": "2027-11-04T00:00:00Z",
        "signing_key_id": "release-key-1",
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
    document = dict(unsigned)
    document["signature"] = {
        "algorithm": "Ed25519",
        "value": base64.b64encode(signer.sign(canonical)).decode("ascii"),
    }
    return json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
