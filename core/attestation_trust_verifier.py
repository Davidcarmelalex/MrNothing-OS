"""Cryptographic authentication for SEC-016 trust-manifest envelopes.

A successful result authenticates the manifest with an out-of-band pinned
Ed25519 update key and checks that listed certificates are CA-shaped X.509
objects. It does NOT establish an Android attestation PKIX path, validate
KeyDescription/verified boot, persist anti-rollback state, or authorize actions.
"""
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.x509 import ExtensionNotFound

from core.attestation_trust_manifest import ParsedTrustManifest, parse_trust_manifest


class ManifestVerificationError(ValueError):
    """A structurally valid manifest failed cryptographic/policy verification."""


@dataclass(frozen=True)
class AuthenticatedTrustManifest:
    """A signed manifest authenticated by an externally pinned update key.

    Root certificates have only been parsed and checked for CA constraints and
    keyCertSign. This object is NOT a PKIX path-validation or Android attestation
    trust decision and must not authorize device actions.
    """

    manifest: ParsedTrustManifest
    signing_key_id: str
    signing_key_sha256: str
    authenticated_at: datetime


def _validate_ca_certificate(der: bytes, root_id: str) -> None:
    try:
        certificate = x509.load_der_x509_certificate(der)
    except (TypeError, ValueError) as exc:
        raise ManifestVerificationError(f"root {root_id} is not valid X.509 DER") from exc

    if certificate.public_bytes(serialization.Encoding.DER) != der:
        raise ManifestVerificationError(f"root {root_id} is not canonical DER")

    try:
        constraints = certificate.extensions.get_extension_for_class(
            x509.BasicConstraints
        ).value
    except ExtensionNotFound as exc:
        raise ManifestVerificationError(
            f"root {root_id} lacks BasicConstraints"
        ) from exc
    if not constraints.ca:
        raise ManifestVerificationError(f"root {root_id} is not a CA certificate")

    try:
        usage = certificate.extensions.get_extension_for_class(x509.KeyUsage).value
    except ExtensionNotFound as exc:
        raise ManifestVerificationError(f"root {root_id} lacks KeyUsage") from exc
    if not usage.key_cert_sign:
        raise ManifestVerificationError(
            f"root {root_id} does not permit certificate signing"
        )


def verify_trust_manifest(
    raw: bytes,
    *,
    pinned_update_keys: Mapping[str, bytes],
    current_version: int,
    now: datetime,
) -> AuthenticatedTrustManifest:
    """Authenticate a trust manifest using only caller-pinned Ed25519 keys.

    pinned_update_keys must come from a trusted configuration channel that is
    independent of the manifest. Values are raw 32-byte Ed25519 public keys.
    current_version is a caller-supplied durable version snapshot; this
    function checks monotonicity but does not persist or atomically advance it.
    now must be timezone-aware. No network or device operation is performed.
    """
    if not isinstance(pinned_update_keys, Mapping):
        raise ManifestVerificationError("pinned update-key map is required")
    if type(current_version) is not int or current_version < 0:
        raise ManifestVerificationError("current version must be a non-negative integer")
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ManifestVerificationError("verification time must be timezone-aware")

    authenticated_at = now.astimezone(timezone.utc)
    now_utc_naive = authenticated_at.replace(tzinfo=None)
    manifest = parse_trust_manifest(raw)

    if manifest.bundle_version <= current_version:
        raise ManifestVerificationError("manifest version is a rollback or replay")
    if not (manifest.not_before <= now_utc_naive < manifest.not_after):
        raise ManifestVerificationError("manifest is outside its validity interval")

    public_key_bytes = pinned_update_keys.get(manifest.signing_key_id)
    if type(public_key_bytes) is not bytes or len(public_key_bytes) != 32:
        raise ManifestVerificationError("unknown or invalid pinned update key")
    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(manifest.signature, manifest.canonical_payload)
    except (InvalidSignature, ValueError) as exc:
        raise ManifestVerificationError("manifest signature verification failed") from exc

    # Parse root certificates only after the signed envelope has authenticated.
    for root in manifest.roots:
        _validate_ca_certificate(root.certificate_der, root.root_id)

    return AuthenticatedTrustManifest(
        manifest=manifest,
        signing_key_id=manifest.signing_key_id,
        signing_key_sha256=hashlib.sha256(public_key_bytes).hexdigest(),
        authenticated_at=authenticated_at,
    )
