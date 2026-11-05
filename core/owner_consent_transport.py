"""AGENT-004D: mTLS peer-to-session adapter for owner-consent challenges.

This module does not create a listener or expose a network endpoint. A trusted
server accepts and completes an mTLS handshake elsewhere, then passes the
already-handshaken server-side SSLSocket to this adapter. The adapter verifies
the negotiated channel, leaf certificate profile and exact enrolled
certificate fingerprint before it creates a short-lived session internally.

TLS identity and the per-use owner-consent signing key are separate credentials.
A trusted enrollment ceremony must bind both to the same owner/device record.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
import secrets
import ssl
import time
from typing import Callable, Protocol

from cryptography import x509
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID

from core.owner_consent_issuer import (
    AuthenticatedOwnerSession,
    ChallengeIssueResult,
    MAX_EPOCH_MS,
    OwnerConsentRegistry,
    issue_owner_consent_challenge,
)

OWNER_CONSENT_ALPN = "mrnothing-owner-consent/1"
MAX_PEER_CERT_DER_BYTES = 8_192
MAX_TRANSPORT_SESSION_TTL_MS = 30_000
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class EnrolledTransportCertificate:
    """Trusted registry mapping for one exact mTLS client leaf certificate."""

    owner_id: str
    device_id: str
    certificate_sha256: str
    active: bool = True


class OwnerTransportRegistry(Protocol):
    """Trusted host registry; never implement from request or model/tool input."""

    def lookup_active_certificate(
        self, certificate_sha256: str
    ) -> EnrolledTransportCertificate | None:
        ...


def build_owner_consent_server_context(
    *,
    server_certificate_pem: str,
    server_private_key_pem: str,
    client_ca_bundle_pem: str,
) -> ssl.SSLContext:
    """Build a TLS server context with mandatory client certificates.

    The CA bundle must be a separately authenticated, narrowly scoped client
    enrollment CA bundle. This function deliberately does not load system
    default roots. The caller remains responsible for protecting the server
    private key and provisioning/rotating the CA bundle.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.options |= ssl.OP_NO_COMPRESSION
    context.load_cert_chain(
        certfile=server_certificate_pem,
        keyfile=server_private_key_pem,
    )
    context.load_verify_locations(cafile=client_ca_bundle_pem)
    context.set_alpn_protocols([OWNER_CONSENT_ALPN])
    return context


class OwnerConsentTlsAdapter:
    """Issue challenges only from a live, enrolled mTLS peer connection.

    The caller must pass an accepted server-side SSLSocket created with the
    exact server_context supplied here. No caller-supplied authenticated flag
    or AuthenticatedOwnerSession is accepted. Certificate enrollment status is
    looked up on every call so leaf-certificate revocation blocks new issues.
    """

    def __init__(
        self,
        *,
        server_context: ssl.SSLContext,
        transport_registry: OwnerTransportRegistry,
        consent_registry: OwnerConsentRegistry,
        clock_ms: Callable[[], int] | None = None,
        session_id_factory: Callable[[int], str] = secrets.token_hex,
        nonce_factory: Callable[[int], str] = secrets.token_hex,
    ) -> None:
        self._server_context = server_context
        self._transport_registry = transport_registry
        self._consent_registry = consent_registry
        self._clock_ms = clock_ms or (lambda: int(time.time() * 1000))
        self._session_id_factory = session_id_factory
        self._nonce_factory = nonce_factory

    def issue_challenge(
        self, peer: ssl.SSLSocket, *, action: str
    ) -> ChallengeIssueResult:
        """Authenticate the live TLS peer, then issue one bounded challenge."""
        if type(peer) is not ssl.SSLSocket:
            return ChallengeIssueResult(False, "INVALID_TLS_SOCKET")
        try:
            if peer.fileno() < 0:
                return ChallengeIssueResult(False, "TLS_SOCKET_CLOSED")
            peer.getpeername()
        except OSError:
            return ChallengeIssueResult(False, "TLS_SOCKET_CLOSED")

        context = peer.context
        if (
            context is not self._server_context
            or context.protocol != ssl.PROTOCOL_TLS_SERVER
            or context.verify_mode != ssl.CERT_REQUIRED
            or context.minimum_version < ssl.TLSVersion.TLSv1_2
        ):
            return ChallengeIssueResult(False, "TLS_CONTEXT_NOT_STRICT")
        if peer.version() not in {"TLSv1.2", "TLSv1.3"}:
            return ChallengeIssueResult(False, "TLS_VERSION_UNSUPPORTED")
        if peer.selected_alpn_protocol() != OWNER_CONSENT_ALPN:
            return ChallengeIssueResult(False, "ALPN_MISMATCH")

        try:
            certificate_der = peer.getpeercert(binary_form=True)
        except (OSError, ssl.SSLError):
            return ChallengeIssueResult(False, "PEER_CERT_UNAVAILABLE")
        if (
            type(certificate_der) is not bytes
            or not 1 <= len(certificate_der) <= MAX_PEER_CERT_DER_BYTES
        ):
            return ChallengeIssueResult(False, "PEER_CERT_UNAVAILABLE")

        try:
            now_epoch_ms = self._clock_ms()
        except Exception:
            return ChallengeIssueResult(False, "INVALID_CLOCK")
        if (
            type(now_epoch_ms) is not int
            or not 0 <= now_epoch_ms <= MAX_EPOCH_MS
        ):
            return ChallengeIssueResult(False, "INVALID_CLOCK")
        try:
            now = datetime.fromtimestamp(
                now_epoch_ms / 1000, tz=timezone.utc
            )
            certificate = x509.load_der_x509_certificate(certificate_der)
            not_before = certificate.not_valid_before_utc
            not_after = certificate.not_valid_after_utc
        except (ValueError, OverflowError, TypeError, UnsupportedAlgorithm):
            return ChallengeIssueResult(False, "PEER_CERT_INVALID")
        if not not_before <= now < not_after:
            return ChallengeIssueResult(False, "PEER_CERT_NOT_CURRENT")

        try:
            constraints = certificate.extensions.get_extension_for_class(
                x509.BasicConstraints
            ).value
            key_usage = certificate.extensions.get_extension_for_class(
                x509.KeyUsage
            ).value
            extended_usage = certificate.extensions.get_extension_for_class(
                x509.ExtendedKeyUsage
            ).value
        except x509.ExtensionNotFound:
            return ChallengeIssueResult(False, "PEER_CERT_PROFILE_INVALID")
        if constraints.ca:
            return ChallengeIssueResult(False, "PEER_CERT_CA_NOT_ALLOWED")
        if not key_usage.digital_signature:
            return ChallengeIssueResult(False, "PEER_CERT_PROFILE_INVALID")
        if ExtendedKeyUsageOID.CLIENT_AUTH not in extended_usage:
            return ChallengeIssueResult(False, "PEER_CERT_PROFILE_INVALID")

        try:
            public_key = certificate.public_key()
        except (ValueError, TypeError, UnsupportedAlgorithm):
            return ChallengeIssueResult(False, "PEER_CERT_INVALID")
        if (
            not isinstance(public_key, ec.EllipticCurvePublicKey)
            or public_key.curve.name != "secp256r1"
        ):
            return ChallengeIssueResult(False, "PEER_CERT_KEY_UNSUPPORTED")

        fingerprint = hashlib.sha256(certificate_der).hexdigest()
        if _FINGERPRINT_RE.fullmatch(fingerprint) is None:
            return ChallengeIssueResult(False, "PEER_CERT_INVALID")
        try:
            enrolled = self._transport_registry.lookup_active_certificate(
                fingerprint
            )
        except Exception:
            return ChallengeIssueResult(False, "TRANSPORT_REGISTRY_UNAVAILABLE")
        if type(enrolled) is not EnrolledTransportCertificate:
            return ChallengeIssueResult(False, "TRANSPORT_CERT_NOT_ENROLLED")
        if (
            enrolled.certificate_sha256 != fingerprint
            or type(enrolled.active) is not bool
        ):
            return ChallengeIssueResult(False, "TRANSPORT_REGISTRY_INVALID")
        if enrolled.active is not True:
            return ChallengeIssueResult(False, "TRANSPORT_CERT_REVOKED")
        if type(enrolled.credential_generation) is not int or enrolled.credential_generation < 1:
            return ChallengeIssueResult(False, "TRANSPORT_REGISTRY_INVALID")

        try:
            session_id = self._session_id_factory(16)
        except Exception:
            return ChallengeIssueResult(False, "SESSION_ID_SOURCE_FAILED")
        if type(session_id) is not str or not session_id:
            return ChallengeIssueResult(False, "SESSION_ID_INVALID")

        certificate_expiry_ms = int(not_after.timestamp() * 1000)
        session = AuthenticatedOwnerSession(
            owner_id=enrolled.owner_id,
            device_id=enrolled.device_id,
            session_id=session_id,
            authenticated_at_epoch_ms=now_epoch_ms,
            expires_at_epoch_ms=min(
                now_epoch_ms + MAX_TRANSPORT_SESSION_TTL_MS,
                certificate_expiry_ms,
            ),
            transport_certificate_sha256=fingerprint,
            credential_generation=enrolled.credential_generation,
        )
        return issue_owner_consent_challenge(
            session,
            action=action,
            registry=self._consent_registry,
            now_epoch_ms=now_epoch_ms,
            nonce_factory=self._nonce_factory,
        )
