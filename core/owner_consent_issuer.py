"""AGENT-004C: bounded host-side issuance of owner-consent challenges.

This module is a library boundary, not a network endpoint or identity provider.
The caller must create AuthenticatedOwnerSession only after validating the
transport peer and server-side session. The registry must return records from
a trusted enrollment process, never from request or model/tool input.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import secrets
from typing import Callable, Protocol

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from core.owner_consent_protocol import (
    ConsentChallenge,
    MAX_CAPABILITY_TTL_MS,
    SCREEN_ACTIONS,
    canonical_payload,
)

MAX_EPOCH_MS = (1 << 63) - 1
NONCE_BYTES = 16
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_NONCE_RE = re.compile(r"^[0-9a-f]{32}$")
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class AuthenticatedOwnerSession:
    """Assertion created by the trusted transport adapter, not from request JSON.

    This data class is not itself proof of authentication. Python callers can
    construct it; the network/session adapter is responsible for establishing
    its provenance before passing it to this module.
    """

    owner_id: str
    device_id: str
    session_id: str
    authenticated_at_epoch_ms: int
    expires_at_epoch_ms: int
    # Present when the session came from AGENT-004D's durable paired registry.
    transport_certificate_sha256: str | None = None
    credential_generation: int | None = None


@dataclass(frozen=True)
class EnrolledOwnerDevice:
    """Public-key record returned by a trusted enrollment registry."""

    owner_id: str
    device_id: str
    public_key_spki_der: bytes
    active: bool = True
    transport_certificate_sha256: str | None = None
    credential_generation: int | None = None


class OwnerConsentRegistry(Protocol):
    """Read-only interface to the host's trusted device enrollment registry."""

    def lookup_active_device(self, device_id: str) -> EnrolledOwnerDevice | None:
        ...


@dataclass(frozen=True)
class IssuedOwnerConsentChallenge:
    challenge: ConsentChallenge
    trusted_public_key_spki_der: bytes


@dataclass(frozen=True)
class ChallengeIssueResult:
    issued: bool
    reason: str
    capability: IssuedOwnerConsentChallenge | None = None


def _valid_identifier(value: object) -> bool:
    return (
        type(value) is str
        and _IDENTIFIER_RE.fullmatch(value) is not None
    )


def _trusted_p256_spki(value: object) -> bytes | None:
    if type(value) is not bytes or not 1 <= len(value) <= 512:
        return None
    try:
        public_key = serialization.load_der_public_key(value)
    except (ValueError, TypeError, UnsupportedAlgorithm):
        return None
    if (
        not isinstance(public_key, ec.EllipticCurvePublicKey)
        or public_key.curve.name != "secp256r1"
    ):
        return None
    canonical = public_key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return canonical if canonical == value else None


def issue_owner_consent_challenge(
    session: AuthenticatedOwnerSession,
    *,
    action: str,
    registry: OwnerConsentRegistry,
    now_epoch_ms: int,
    nonce_factory: Callable[[int], str] = secrets.token_hex,
) -> ChallengeIssueResult:
    """Issue one 128-bit-nonce, at-most-30-second owner-consent challenge.

    The session and registry are trusted host inputs. This function does not
    authenticate a socket, prove key attestation, persist enrollment, rate-limit
    callers, consume a nonce, grant Android permissions, or execute an action.
    The existing verifier's durable replay ledger consumes the nonce later.
    Challenge expiry is capped by the authenticated session's expiry.
    """
    if type(session) is not AuthenticatedOwnerSession:
        return ChallengeIssueResult(False, "INVALID_SESSION")
    if not all(_valid_identifier(value) for value in (
        session.owner_id, session.device_id, session.session_id
    )):
        return ChallengeIssueResult(False, "INVALID_SESSION")
    if (session.transport_certificate_sha256 is None) != (session.credential_generation is None):
        return ChallengeIssueResult(False, "INVALID_SESSION_CREDENTIAL_BINDING")
    if session.transport_certificate_sha256 is not None and (
        type(session.transport_certificate_sha256) is not str
        or _FINGERPRINT_RE.fullmatch(session.transport_certificate_sha256) is None
        or type(session.credential_generation) is not int
        or session.credential_generation < 1
    ):
        return ChallengeIssueResult(False, "INVALID_SESSION_CREDENTIAL_BINDING")
    if (
        type(session.authenticated_at_epoch_ms) is not int
        or type(session.expires_at_epoch_ms) is not int
        or session.authenticated_at_epoch_ms < 0
        or session.expires_at_epoch_ms <= session.authenticated_at_epoch_ms
        or session.expires_at_epoch_ms > MAX_EPOCH_MS
    ):
        return ChallengeIssueResult(False, "INVALID_SESSION_TIME")
    if type(now_epoch_ms) is not int or not 0 <= now_epoch_ms <= MAX_EPOCH_MS:
        return ChallengeIssueResult(False, "INVALID_CLOCK")
    if now_epoch_ms < session.authenticated_at_epoch_ms:
        return ChallengeIssueResult(False, "SESSION_NOT_YET_VALID")
    if now_epoch_ms >= session.expires_at_epoch_ms:
        return ChallengeIssueResult(False, "SESSION_EXPIRED")
    if type(action) is not str or action not in SCREEN_ACTIONS:
        return ChallengeIssueResult(False, "INVALID_ACTION")

    try:
        record = registry.lookup_active_device(session.device_id)
    except Exception:
        return ChallengeIssueResult(False, "REGISTRY_UNAVAILABLE")
    if type(record) is not EnrolledOwnerDevice:
        return ChallengeIssueResult(False, "DEVICE_NOT_ENROLLED")
    if record.device_id != session.device_id or record.owner_id != session.owner_id:
        return ChallengeIssueResult(False, "OWNER_DEVICE_MISMATCH")
    if session.transport_certificate_sha256 is not None and (
        record.transport_certificate_sha256 != session.transport_certificate_sha256
        or record.credential_generation != session.credential_generation
    ):
        return ChallengeIssueResult(False, "CREDENTIAL_GENERATION_CHANGED")
    if record.active is not True:
        return ChallengeIssueResult(False, "DEVICE_NOT_ACTIVE")
    trusted_key = _trusted_p256_spki(record.public_key_spki_der)
    if trusted_key is None:
        return ChallengeIssueResult(False, "INVALID_TRUSTED_KEY")

    try:
        nonce = nonce_factory(NONCE_BYTES)
    except Exception:
        return ChallengeIssueResult(False, "NONCE_SOURCE_FAILED")
    if type(nonce) is not str or _NONCE_RE.fullmatch(nonce) is None:
        return ChallengeIssueResult(False, "INVALID_NONCE")

    challenge = ConsentChallenge(
        device_id=session.device_id,
        owner_id=session.owner_id,
        session_id=session.session_id,
        action=action,
        nonce=nonce,
        issued_at_epoch_ms=now_epoch_ms,
        expires_at_epoch_ms=min(
            now_epoch_ms + MAX_CAPABILITY_TTL_MS,
            session.expires_at_epoch_ms,
        ),
        version=1,
    )
    try:
        canonical_payload(challenge)
    except (TypeError, ValueError, OverflowError):
        return ChallengeIssueResult(False, "INVALID_CHALLENGE")
    return ChallengeIssueResult(
        True,
        "ISSUED",
        IssuedOwnerConsentChallenge(challenge, trusted_key),
    )
