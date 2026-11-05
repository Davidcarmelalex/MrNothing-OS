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
import sqlite3
from typing import Any, Protocol

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from core.command_admission import DurableReplayLedger


SCREEN_ACTIONS = frozenset({"read_screen", "navigate", "scroll"})
MAX_CAPABILITY_TTL_MS = 30_000
MAX_ENVELOPE_BYTES = 4_096
MAX_PUBLIC_KEY_DER_BYTES = 512
MAX_SIGNATURE_DER_BYTES = 72
CONSENT_REPLAY_NAMESPACE = "consent-v1:"
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
    """Trusted paired enrollment registry; never sourced from request input."""

    def lookup_active_device(self, device_id: str) -> object | None:
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


def _enrollment_mismatch_reason(
    registry: OwnerConsentEnrollmentRegistry,
    *,
    challenge: ConsentChallenge,
    trusted_public_key_spki_der: bytes,
    transport_certificate_sha256: str,
    credential_generation: int,
) -> str | None:
    """Compare the live paired enrollment with the authenticated session snapshot."""
    try:
        record = registry.lookup_active_device(challenge.device_id)
    except Exception:
        return "ENROLLMENT_REGISTRY_UNAVAILABLE"
    if record is None:
        return "ENROLLMENT_NOT_ACTIVE"
    try:
        owner_id = record.owner_id
        device_id = record.device_id
        active = record.active
        current_key = record.public_key_spki_der
        current_fingerprint = record.transport_certificate_sha256
        current_generation = record.credential_generation
    except Exception:
        return "ENROLLMENT_RECORD_INVALID"
    if type(active) is not bool:
        return "ENROLLMENT_RECORD_INVALID"
    if active is not True:
        return "ENROLLMENT_NOT_ACTIVE"
    if type(owner_id) is not str or type(device_id) is not str:
        return "ENROLLMENT_RECORD_INVALID"
    if owner_id != challenge.owner_id or device_id != challenge.device_id:
        return "ENROLLMENT_IDENTITY_MISMATCH"
    if (
        type(current_fingerprint) is not str
        or _FINGERPRINT_RE.fullmatch(current_fingerprint) is None
        or current_fingerprint != transport_certificate_sha256
        or type(current_generation) is not int
        or not 1 <= current_generation <= MAX_CREDENTIAL_GENERATION
        or current_generation != credential_generation
    ):
        return "ENROLLMENT_CREDENTIAL_MISMATCH"
    if type(current_key) is not bytes:
        return "ENROLLMENT_RECORD_INVALID"
    if not hmac.compare_digest(current_key, trusted_public_key_spki_der):
        return "ENROLLMENT_KEY_MISMATCH"
    return None


def verify_and_consume(
    envelope: bytes,
    *,
    challenge: ConsentChallenge,
    trusted_public_key_spki_der: bytes,
    transport_authenticated: bool,
    enrollment_registry: OwnerConsentEnrollmentRegistry,
    transport_certificate_sha256: str,
    credential_generation: int,
    ledger: DurableReplayLedger,
    now_epoch_ms: int,
) -> ConsentAdmissionResult:
    """Verify one owner-signed capability and atomically consume its host nonce.

    Challenge, key, transport-session snapshot, registry and time must come
    from the trusted host layer, never an LLM or request payload. The active
    paired enrollment is checked after signature verification and again after
    nonce reservation. A change observed during verification fails closed; the
    nonce may be consumed on that race. This function never executes a command.
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
    if not callable(getattr(enrollment_registry, "lookup_active_device", None)):
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
    if not isinstance(ledger, DurableReplayLedger):
        return ConsentAdmissionResult(False, "LEDGER_UNAVAILABLE")
    if type(ledger.ttl_seconds) is not int or ledger.ttl_seconds < MAX_CAPABILITY_TTL_MS // 1000:
        return ConsentAdmissionResult(False, "REPLAY_WINDOW_TOO_SHORT")

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
    if (not isinstance(public_key, ec.EllipticCurvePublicKey)
            or public_key.curve.name != "secp256r1"):
        return ConsentAdmissionResult(False, "INVALID_TRUSTED_KEY")

    try:
        public_key.verify(
            signature, canonical_payload(challenge), ec.ECDSA(hashes.SHA256())
        )
    except InvalidSignature:
        return ConsentAdmissionResult(False, "BAD_SIGNATURE")
    except (ValueError, TypeError, UnsupportedAlgorithm):
        return ConsentAdmissionResult(False, "BAD_SIGNATURE")

    enrollment_reason = _enrollment_mismatch_reason(
        enrollment_registry,
        challenge=challenge,
        trusted_public_key_spki_der=trusted_public_key_spki_der,
        transport_certificate_sha256=transport_certificate_sha256,
        credential_generation=credential_generation,
    )
    if enrollment_reason is not None:
        return ConsentAdmissionResult(False, enrollment_reason)

    try:
        if not ledger.reserve(
            CONSENT_REPLAY_NAMESPACE + challenge.device_id,
            challenge.nonce, now_epoch_ms // 1000
        ):
            return ConsentAdmissionResult(False, "REPLAY_OR_CAPACITY")
    except sqlite3.Error:
        return ConsentAdmissionResult(False, "LEDGER_UNAVAILABLE")

    enrollment_reason = _enrollment_mismatch_reason(
        enrollment_registry,
        challenge=challenge,
        trusted_public_key_spki_der=trusted_public_key_spki_der,
        transport_certificate_sha256=transport_certificate_sha256,
        credential_generation=credential_generation,
    )
    if enrollment_reason is not None:
        return ConsentAdmissionResult(False, "ENROLLMENT_CHANGED_DURING_VERIFICATION")

    return ConsentAdmissionResult(True, "ADMITTED_NO_EXECUTION")
