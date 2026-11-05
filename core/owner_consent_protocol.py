"""AGENT-004A: bounded P-256 owner-consent capability verification.

This is a verifier primitive, not an issuer, Android permission checker, or
action executor. The trusted host must create the challenge, bind it to an
authenticated device/owner record, and provide the enrolled P-256 public key.
The Android signer and production enrollment/command integration are separate
gates. Never source challenge fields or the verification key from an LLM.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hmac
import json
import re
from typing import Any, Protocol

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec



SCREEN_ACTIONS = frozenset({"read_screen", "navigate", "scroll"})
MAX_CAPABILITY_TTL_MS = 30_000
MAX_ENVELOPE_BYTES = 4_096
MAX_PUBLIC_KEY_DER_BYTES = 512
MAX_SIGNATURE_DER_BYTES = 72
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_SIGNATURE_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_CREDENTIAL_GENERATION = (1 << 63) - 1

_PAYLOAD_KEYS = frozenset({
    "version",
    "device_id",
    "owner_id",
    "session_id",
    "action",
    "nonce",
    "issued_at_epoch_ms",
    "expires_at_epoch_ms",
})


@dataclass(frozen=True)
class ConsentChallenge:
    """Trusted host-issued challenge; never construct from model/tool input."""
    device_id: str
    owner_id: str
    session_id: str
    action: str
    nonce: str
    issued_at_epoch_ms: int
    expires_at_epoch_ms: int
    version: int = 1


@dataclass(frozen=True)
class ConsentAdmissionResult:
    admitted: bool
    reason: str


class OwnerConsentEnrollmentRegistry(Protocol):
    """Trusted registry that atomically validates enrollment and consumes a nonce."""

    def consume_consent_nonce(
        self,
        *,
        owner_id: str,
        device_id: str,
        nonce: str,
        transport_certificate_sha256: str,
        credential_generation: int,
        consent_public_key_spki_der: bytes,
        now_epoch_ms: int,
    ) -> str:
        ...


def _identifier(value: object, *, minimum: int = 1) -> bool:
    return (
        type(value) is str
        and minimum <= len(value) <= 128
        and _IDENTIFIER_RE.fullmatch(value) is not None
    )


def _valid_challenge(challenge: object) -> bool:
    if type(challenge) is not ConsentChallenge:
        return False
    if type(challenge.version) is not int or challenge.version != 1:
        return False
    if not all(_identifier(value) for value in (
        challenge.device_id, challenge.owner_id, challenge.session_id,
        challenge.nonce,
    )):
        return False
    if len(challenge.nonce) < 32:
        return False
    if type(challenge.action) is not str or challenge.action not in SCREEN_ACTIONS:
        return False
    if (type(challenge.issued_at_epoch_ms) is not int
            or type(challenge.expires_at_epoch_ms) is not int):
        return False
    ttl = challenge.expires_at_epoch_ms - challenge.issued_at_epoch_ms
    return 0 < ttl <= MAX_CAPABILITY_TTL_MS and challenge.issued_at_epoch_ms >= 0


def canonical_payload(challenge: ConsentChallenge) -> bytes:
    """Return the cross-platform canonical JSON bytes (sorted keys, ASCII)."""
    if not _valid_challenge(challenge):
        raise ValueError("invalid consent challenge")
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
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("ascii")


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-finite JSON number")


def _decode_envelope(envelope: bytes) -> tuple[dict[str, Any], str] | None:
    if type(envelope) is not bytes or not 1 <= len(envelope) <= MAX_ENVELOPE_BYTES:
        return None
    try:
        decoded = json.loads(
            envelope.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError):
        return None
    if type(decoded) is not dict or set(decoded) != {"payload", "signature"}:
        return None
    payload = decoded["payload"]
    signature = decoded["signature"]
    if type(payload) is not dict or set(payload) != _PAYLOAD_KEYS:
        return None
    if type(signature) is not str or _SIGNATURE_RE.fullmatch(signature) is None:
        return None
    return payload, signature


def _payload_matches_challenge(payload: dict[str, Any], challenge: ConsentChallenge) -> bool:
    expected = {
        "version": challenge.version,
        "device_id": challenge.device_id,
        "owner_id": challenge.owner_id,
        "session_id": challenge.session_id,
        "action": challenge.action,
        "nonce": challenge.nonce,
        "issued_at_epoch_ms": challenge.issued_at_epoch_ms,
        "expires_at_epoch_ms": challenge.expires_at_epoch_ms,
    }
    if set(payload) != set(expected):
        return False
    for key, expected_value in expected.items():
        value = payload[key]
        if type(value) is not type(expected_value) or value != expected_value:
            return False
    return True


def _decode_signature(signature: str) -> bytes | None:
    try:
        padded = signature + ("=" * ((4 - len(signature) % 4) % 4))
        raw = base64.b64decode(padded.encode("ascii"), altchars=b"-_", validate=True)
    except (ValueError, UnicodeEncodeError):
        return None
    if not 8 <= len(raw) <= MAX_SIGNATURE_DER_BYTES:
        return None
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") != signature:
        return None
    return raw


def verify_and_consume(
    envelope: bytes,
    *,
    challenge: ConsentChallenge,
    trusted_public_key_spki_der: bytes,
    transport_authenticated: bool,
    enrollment_registry: OwnerConsentEnrollmentRegistry,
    transport_certificate_sha256: str,
    credential_generation: int,
    now_epoch_ms: int,
) -> ConsentAdmissionResult:
    """Verify a signed capability and atomically bind enrollment to nonce use.

    The paired enrollment comparison and nonce insertion occur under the
    enrollment database's single BEGIN IMMEDIATE transaction. Rotation or
    revocation therefore serializes before or after admission; there is no
    separate-database check/consume/check window. This function never executes
    a command. Transport-session object binding remains a separate gate.
    """
    if transport_authenticated is not True:
        return ConsentAdmissionResult(False, "UNAUTHENTICATED")
    if (
        type(transport_certificate_sha256) is not str
        or _FINGERPRINT_RE.fullmatch(transport_certificate_sha256) is None
        or type(credential_generation) is not int
        or not 1 <= credential_generation <= MAX_CREDENTIAL_GENERATION
    ):
        return ConsentAdmissionResult(False, "INVALID_TRANSPORT_BINDING")
    if not callable(getattr(enrollment_registry, "consume_consent_nonce", None)):
        return ConsentAdmissionResult(False, "ENROLLMENT_REGISTRY_INVALID")
    if not _valid_challenge(challenge):
        return ConsentAdmissionResult(False, "INVALID_CHALLENGE")
    if type(now_epoch_ms) is not int:
        return ConsentAdmissionResult(False, "INVALID_CLOCK")
    if not challenge.issued_at_epoch_ms <= now_epoch_ms < challenge.expires_at_epoch_ms:
        return ConsentAdmissionResult(False, "CHALLENGE_EXPIRED")
    if type(trusted_public_key_spki_der) is not bytes or not (
        1 <= len(trusted_public_key_spki_der) <= MAX_PUBLIC_KEY_DER_BYTES
    ):
        return ConsentAdmissionResult(False, "INVALID_TRUSTED_KEY")

    parsed = _decode_envelope(envelope)
    if parsed is None:
        return ConsentAdmissionResult(False, "INVALID_ENVELOPE")
    payload, signature_text = parsed
    if not _payload_matches_challenge(payload, challenge):
        return ConsentAdmissionResult(False, "CHALLENGE_MISMATCH")

    signature = _decode_signature(signature_text)
    if signature is None:
        return ConsentAdmissionResult(False, "INVALID_SIGNATURE_ENCODING")

    try:
        public_key = serialization.load_der_public_key(trusted_public_key_spki_der)
    except (ValueError, TypeError, UnsupportedAlgorithm):
        return ConsentAdmissionResult(False, "INVALID_TRUSTED_KEY")
    if (
        not isinstance(public_key, ec.EllipticCurvePublicKey)
        or public_key.curve.name != "secp256r1"
    ):
        return ConsentAdmissionResult(False, "INVALID_TRUSTED_KEY")

    try:
        public_key.verify(
            signature, canonical_payload(challenge), ec.ECDSA(hashes.SHA256())
        )
    except InvalidSignature:
        return ConsentAdmissionResult(False, "BAD_SIGNATURE")
    except (ValueError, TypeError, UnsupportedAlgorithm):
        return ConsentAdmissionResult(False, "BAD_SIGNATURE")

    try:
        admission = enrollment_registry.consume_consent_nonce(
            owner_id=challenge.owner_id,
            device_id=challenge.device_id,
            nonce=challenge.nonce,
            transport_certificate_sha256=transport_certificate_sha256,
            credential_generation=credential_generation,
            consent_public_key_spki_der=trusted_public_key_spki_der,
            now_epoch_ms=now_epoch_ms,
        )
    except Exception:
        return ConsentAdmissionResult(False, "ENROLLMENT_REGISTRY_UNAVAILABLE")
    if admission == "ADMITTED":
        return ConsentAdmissionResult(True, "ADMITTED_NO_EXECUTION")
    if type(admission) is not str:
        return ConsentAdmissionResult(False, "ENROLLMENT_REGISTRY_INVALID")
    if admission in {
        "INVALID_ADMISSION_CONTEXT",
        "ENROLLMENT_NOT_ACTIVE",
        "ENROLLMENT_IDENTITY_MISMATCH",
        "ENROLLMENT_CREDENTIAL_MISMATCH",
        "ENROLLMENT_KEY_MISMATCH",
        "REPLAY_OR_CAPACITY",
    }:
        return ConsentAdmissionResult(False, admission)
    return ConsentAdmissionResult(False, "ENROLLMENT_REGISTRY_INVALID")
