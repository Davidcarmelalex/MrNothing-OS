"""Strict structural preflight for signed Android attestation trust manifests.

This module parses an untrusted envelope only. It does not verify Ed25519,
parse X.509 certificates, establish PKIX trust, or authorize device actions.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


MAX_MANIFEST_BYTES = 262_144
MAX_JSON_DEPTH = 12
MAX_JSON_NODES = 1_024
MAX_JSON_TEXT_CHARS = 65_536
MAX_ROOTS = 8
MAX_CERTIFICATE_BYTES = 16_384
MAX_TOTAL_CERTIFICATE_BYTES = 65_536

_SCHEMA = "mrnothing.android-attestation-trust-bundle"
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")
_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class ManifestError(ValueError):
    """An untrusted trust-bundle envelope failed structural preflight."""


@dataclass(frozen=True)
class TrustRootEntry:
    root_id: str
    certificate_der: bytes
    sha256: str


@dataclass(frozen=True)
class ParsedTrustManifest:
    """Parsed but UNVERIFIED manifest fields.

    canonical_payload excludes the detached signature object. A caller must
    verify it with an independently pinned update-signing key before trusting
    any root entry. This data class is not an authorization result.
    """

    schema_version: int
    bundle_version: int
    issued_at: datetime
    not_before: datetime
    not_after: datetime
    signing_key_id: str
    roots: tuple[TrustRootEntry, ...]
    signature: bytes
    canonical_payload: bytes

    def is_newer_than(self, current_version: int) -> bool:
        """Return whether this version advances persisted anti-rollback state."""
        if type(current_version) is not int or current_version < 0:
            raise ValueError("current version must be a non-negative integer")
        return self.bundle_version > current_version


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ManifestError("non-finite JSON numbers are forbidden")


def _check_text(value: str) -> None:
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise ManifestError("invalid Unicode scalar value") from exc


def _check_json_budget(value: Any) -> None:
    pending = [(value, 0)]
    nodes = 0
    text_characters = 0
    while pending:
        current, depth = pending.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            raise ManifestError("JSON structural budget exceeded")
        kind = type(current)
        if kind is dict:
            for key, child in current.items():
                if type(key) is not str:
                    raise ManifestError("object keys must be strings")
                _check_text(key)
                text_characters += len(key)
                pending.append((child, depth + 1))
        elif kind is list:
            pending.extend((child, depth + 1) for child in current)
        elif kind is str:
            _check_text(current)
            text_characters += len(current)
        elif current is None or kind in (bool, int):
            if kind is int and abs(current) > (2**63 - 1):
                raise ManifestError("integer outside signed 64-bit range")
        else:
            # Floats are deliberately excluded from the signed representation.
            raise ManifestError("unsupported JSON value")
        if text_characters > MAX_JSON_TEXT_CHARS:
            raise ManifestError("JSON text budget exceeded")


def _exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != expected:
        raise ManifestError(f"{label} has missing or unknown fields")
    return value


def _identifier(value: Any, label: str) -> str:
    if type(value) is not str or not _IDENTIFIER.fullmatch(value):
        raise ManifestError(f"invalid {label}")
    return value


def _timestamp(value: Any, label: str) -> datetime:
    if type(value) is not str:
        raise ManifestError(f"invalid {label}")
    try:
        parsed = datetime.strptime(value, _TIMESTAMP_FORMAT)
    except ValueError as exc:
        raise ManifestError(f"invalid {label}") from exc
    if parsed.strftime(_TIMESTAMP_FORMAT) != value:
        raise ManifestError(f"non-canonical {label}")
    return parsed


def _decode_canonical_base64(value: Any, label: str) -> bytes:
    if type(value) is not str:
        raise ManifestError(f"invalid {label} encoding")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ManifestError(f"invalid {label} base64") from exc
    if base64.b64encode(decoded).decode("ascii") != value:
        raise ManifestError(f"non-canonical {label} base64")
    return decoded


def parse_trust_manifest(raw: bytes) -> ParsedTrustManifest:
    """Parse an untrusted envelope; this function does not establish trust."""
    if type(raw) is not bytes or not raw or len(raw) > MAX_MANIFEST_BYTES:
        raise ManifestError("manifest size or input type invalid")
    try:
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ManifestError("invalid manifest JSON") from exc

    _check_json_budget(document)
    top = _exact_keys(
        document,
        {
            "schema",
            "schema_version",
            "bundle_version",
            "issued_at",
            "not_before",
            "not_after",
            "signing_key_id",
            "roots",
            "signature",
        },
        "manifest",
    )
    if type(top["schema"]) is not str or top["schema"] != _SCHEMA:
        raise ManifestError("unsupported schema")
    if type(top["schema_version"]) is not int or top["schema_version"] != 1:
        raise ManifestError("unsupported schema version")
    if type(top["bundle_version"]) is not int or top["bundle_version"] < 1:
        raise ManifestError("invalid bundle version")

    issued_at = _timestamp(top["issued_at"], "issued_at")
    not_before = _timestamp(top["not_before"], "not_before")
    not_after = _timestamp(top["not_after"], "not_after")
    if not (issued_at <= not_before < not_after):
        raise ManifestError("invalid manifest time interval")

    signing_key_id = _identifier(top["signing_key_id"], "signing key id")
    roots_value = top["roots"]
    if type(roots_value) is not list or not (1 <= len(roots_value) <= MAX_ROOTS):
        raise ManifestError("invalid root count")

    roots: list[TrustRootEntry] = []
    root_ids: set[str] = set()
    fingerprints: set[str] = set()
    total_der_bytes = 0
    for value in roots_value:
        root = _exact_keys(value, {"id", "certificate_der", "sha256"}, "root")
        root_id = _identifier(root["id"], "root id")
        if root_id in root_ids:
            raise ManifestError("duplicate root id")
        root_ids.add(root_id)

        certificate_der = _decode_canonical_base64(
            root["certificate_der"], "certificate"
        )
        if not certificate_der or len(certificate_der) > MAX_CERTIFICATE_BYTES:
            raise ManifestError("empty or oversized certificate")
        total_der_bytes += len(certificate_der)
        if total_der_bytes > MAX_TOTAL_CERTIFICATE_BYTES:
            raise ManifestError("aggregate certificate budget exceeded")

        fingerprint = root["sha256"]
        if type(fingerprint) is not str or not _FINGERPRINT.fullmatch(fingerprint):
            raise ManifestError("invalid root fingerprint")
        if hashlib.sha256(certificate_der).hexdigest() != fingerprint:
            raise ManifestError("root fingerprint mismatch")
        if fingerprint in fingerprints:
            raise ManifestError("duplicate root fingerprint")
        fingerprints.add(fingerprint)
        roots.append(TrustRootEntry(root_id, certificate_der, fingerprint))

    signature_object = _exact_keys(
        top["signature"], {"algorithm", "value"}, "signature"
    )
    if (
        type(signature_object["algorithm"]) is not str
        or signature_object["algorithm"] != "Ed25519"
    ):
        raise ManifestError("unsupported signature algorithm")
    signature = _decode_canonical_base64(
        signature_object["value"], "signature"
    )
    if len(signature) != 64:
        raise ManifestError("invalid Ed25519 signature length")

    unsigned_document = dict(document)
    del unsigned_document["signature"]
    canonical_payload = json.dumps(
        unsigned_document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    return ParsedTrustManifest(
        schema_version=1,
        bundle_version=top["bundle_version"],
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        signing_key_id=signing_key_id,
        roots=tuple(roots),
        signature=signature,
        canonical_payload=canonical_payload,
    )
