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
from threading import RLock
from weakref import WeakKeyDictionary
from typing import Callable, Protocol

from cryptography import x509
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID

from core.owner_consent_issuer import (
    AuthenticatedOwnerSession,
    ChallengeIssueResult,
    EnrolledOwnerDevice,
    MAX_EPOCH_MS,
    OwnerConsentRegistry,
    issue_owner_consent_challenge,
)
from core.owner_consent_protocol import (
    ConsentAdmissionResult,
    ConsentChallenge,
    _verify_and_consume_bound,
)

OWNER_CONSENT_ALPN = "mrnothing-owner-consent/1"
MAX_PEER_CERT_DER_BYTES = 8_192
MAX_TRANSPORT_SESSION_TTL_MS = 30_000
MAX_OUTSTANDING_CHALLENGES_PER_SESSION = 64
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_ACTION_ARGUMENTS_DOMAIN = b"mrnothing-owner-action-arguments-v1\x00"
_NO_ARGUMENT_ACTIONS = frozenset({"read_screen"})


def _empty_action_arguments_digest(action: object) -> str | None:
    """Digest the only v1 action schema supported by the no-op capability path."""
    if type(action) is not str or action not in _NO_ARGUMENT_ACTIONS:
        return None
    return hashlib.sha256(
        _ACTION_ARGUMENTS_DOMAIN + action.encode("ascii") + b"\x00{}"
    ).hexdigest()


@dataclass(frozen=True)
class _IssuedChallenge:
    challenge: ConsentChallenge
    expires_monotonic_ns: int


class VerifiedOwnerActionCapability:
    """Opaque in-process handle; only its issuing adapter instance recognizes it."""

    __slots__ = ()


@dataclass(frozen=True)
class ActionCapabilityIssueResult:
    issued: bool
    reason: str
    capability: VerifiedOwnerActionCapability | None = None


@dataclass(frozen=True)
class ActionCapabilityAdmissionResult:
    admitted: bool
    reason: str


@dataclass(frozen=True)
class _IssuedActionCapability:
    capability: VerifiedOwnerActionCapability
    nonce: str
    owner_id: str
    device_id: str
    session_id: str
    action: str
    arguments_sha256: str
    transport_certificate_sha256: str
    credential_generation: int
    consent_public_key_sha256: str
    expires_monotonic_ns: int


@dataclass
class _PeerSessionState:
    session: AuthenticatedOwnerSession
    certificate_sha256: str
    credential_generation: int
    expires_monotonic_ns: int
    challenges: dict[str, _IssuedChallenge]
    capabilities: dict[int, _IssuedActionCapability]


@dataclass(frozen=True)
class EnrolledTransportCertificate:
    """Trusted registry mapping for one exact mTLS client leaf certificate."""

    owner_id: str
    device_id: str
    certificate_sha256: str
    active: bool = True
    credential_generation: int | None = None


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
        monotonic_ns: Callable[[], int] | None = None,
    ) -> None:
        self._server_context = server_context
        self._transport_registry = transport_registry
        self._consent_registry = consent_registry
        self._clock_ms = clock_ms or (lambda: int(time.time() * 1000))
        self._session_id_factory = session_id_factory
        self._nonce_factory = nonce_factory
        self._monotonic_ns = monotonic_ns or time.monotonic_ns
        self._sessions: WeakKeyDictionary[ssl.SSLSocket, _PeerSessionState] = WeakKeyDictionary()
        self._lock = RLock()

    def _current_peer_binding(self, peer: ssl.SSLSocket, now_epoch_ms: int):
        """Re-derive the current peer identity from this live TLS socket."""
        if type(peer) is not ssl.SSLSocket:
            return None, "INVALID_TLS_SOCKET"
        try:
            if peer.fileno() < 0:
                return None, "TLS_SOCKET_CLOSED"
            peer.getpeername()
        except OSError:
            return None, "TLS_SOCKET_CLOSED"

        context = peer.context
        if (
            context is not self._server_context
            or context.protocol != ssl.PROTOCOL_TLS_SERVER
            or context.verify_mode != ssl.CERT_REQUIRED
            or context.minimum_version < ssl.TLSVersion.TLSv1_2
        ):
            return None, "TLS_CONTEXT_NOT_STRICT"
        if peer.version() not in {"TLSv1.2", "TLSv1.3"}:
            return None, "TLS_VERSION_UNSUPPORTED"
        if peer.selected_alpn_protocol() != OWNER_CONSENT_ALPN:
            return None, "ALPN_MISMATCH"

        try:
            certificate_der = peer.getpeercert(binary_form=True)
        except (OSError, ssl.SSLError):
            return None, "PEER_CERT_UNAVAILABLE"
        if (
            type(certificate_der) is not bytes
            or not 1 <= len(certificate_der) <= MAX_PEER_CERT_DER_BYTES
        ):
            return None, "PEER_CERT_UNAVAILABLE"

        try:
            now = datetime.fromtimestamp(now_epoch_ms / 1000, tz=timezone.utc)
            certificate = x509.load_der_x509_certificate(certificate_der)
            not_before = certificate.not_valid_before_utc
            not_after = certificate.not_valid_after_utc
        except (ValueError, OverflowError, TypeError, UnsupportedAlgorithm):
            return None, "PEER_CERT_INVALID"
        if not not_before <= now < not_after:
            return None, "PEER_CERT_NOT_CURRENT"

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
            return None, "PEER_CERT_PROFILE_INVALID"
        if constraints.ca:
            return None, "PEER_CERT_CA_NOT_ALLOWED"
        if not key_usage.digital_signature:
            return None, "PEER_CERT_PROFILE_INVALID"
        if ExtendedKeyUsageOID.CLIENT_AUTH not in extended_usage:
            return None, "PEER_CERT_PROFILE_INVALID"

        try:
            public_key = certificate.public_key()
        except (ValueError, TypeError, UnsupportedAlgorithm):
            return None, "PEER_CERT_INVALID"
        if (
            not isinstance(public_key, ec.EllipticCurvePublicKey)
            or public_key.curve.name != "secp256r1"
        ):
            return None, "PEER_CERT_KEY_UNSUPPORTED"

        fingerprint = hashlib.sha256(certificate_der).hexdigest()
        if _FINGERPRINT_RE.fullmatch(fingerprint) is None:
            return None, "PEER_CERT_INVALID"
        try:
            enrolled = self._transport_registry.lookup_active_certificate(
                fingerprint
            )
        except Exception:
            return None, "TRANSPORT_REGISTRY_UNAVAILABLE"
        if type(enrolled) is not EnrolledTransportCertificate:
            return None, "TRANSPORT_CERT_NOT_ENROLLED"
        if (
            enrolled.certificate_sha256 != fingerprint
            or type(enrolled.active) is not bool
        ):
            return None, "TRANSPORT_REGISTRY_INVALID"
        if enrolled.active is not True:
            return None, "TRANSPORT_CERT_REVOKED"
        if (
            type(enrolled.owner_id) is not str
            or _IDENTIFIER_RE.fullmatch(enrolled.owner_id) is None
            or type(enrolled.device_id) is not str
            or _IDENTIFIER_RE.fullmatch(enrolled.device_id) is None
            or type(enrolled.credential_generation) is not int
            or enrolled.credential_generation < 1
        ):
            return None, "TRANSPORT_REGISTRY_INVALID"

        certificate_expiry_ms = int(not_after.timestamp() * 1000)
        return (enrolled, fingerprint, certificate_expiry_ms), None

    def _read_clocks(self):
        try:
            now_epoch_ms = self._clock_ms()
            now_monotonic_ns = self._monotonic_ns()
        except Exception:
            return None, "INVALID_CLOCK"
        if (
            type(now_epoch_ms) is not int
            or not 0 <= now_epoch_ms <= MAX_EPOCH_MS
            or type(now_monotonic_ns) is not int
            or now_monotonic_ns < 0
        ):
            return None, "INVALID_CLOCK"
        return (now_epoch_ms, now_monotonic_ns), None

    def issue_challenge(
        self, peer: ssl.SSLSocket, *, action: str,
        arguments: dict | None = None,
    ) -> ChallengeIssueResult:
        """Issue a challenge and retain it against this exact socket object.

        The per-connection session identifier is generated by this adapter.
        It is not accepted from request data and is not reused on a new
        SSLSocket, including a resumed TLS connection.
        """
        clocks, clock_error = self._read_clocks()
        if clock_error is not None:
            return ChallengeIssueResult(False, clock_error)
        now_epoch_ms, now_monotonic_ns = clocks
        with self._lock:
            binding, binding_error = self._current_peer_binding(peer, now_epoch_ms)
            if binding_error is not None:
                return ChallengeIssueResult(False, binding_error)
            enrolled, fingerprint, certificate_expiry_ms = binding

            state = self._sessions.get(peer)
            if state is None:
                try:
                    session_id = self._session_id_factory(16)
                except Exception:
                    return ChallengeIssueResult(False, "SESSION_ID_SOURCE_FAILED")
                if (
                    type(session_id) is not str
                    or _IDENTIFIER_RE.fullmatch(session_id) is None
                ):
                    return ChallengeIssueResult(False, "SESSION_ID_INVALID")
                session_expiry_ms = min(
                    now_epoch_ms + MAX_TRANSPORT_SESSION_TTL_MS,
                    certificate_expiry_ms,
                )
                if session_expiry_ms <= now_epoch_ms:
                    return ChallengeIssueResult(False, "SESSION_EXPIRED")
                session = AuthenticatedOwnerSession(
                    owner_id=enrolled.owner_id,
                    device_id=enrolled.device_id,
                    session_id=session_id,
                    authenticated_at_epoch_ms=now_epoch_ms,
                    expires_at_epoch_ms=session_expiry_ms,
                    transport_certificate_sha256=fingerprint,
                    credential_generation=enrolled.credential_generation,
                )
                state = _PeerSessionState(
                    session=session,
                    certificate_sha256=fingerprint,
                    credential_generation=enrolled.credential_generation,
                    expires_monotonic_ns=(
                        now_monotonic_ns
                        + (session_expiry_ms - now_epoch_ms) * 1_000_000
                    ),
                    challenges={},
                    capabilities={},
                )
            else:
                if now_monotonic_ns >= state.expires_monotonic_ns:
                    return ChallengeIssueResult(False, "TRANSPORT_SESSION_EXPIRED")
                if (
                    state.session.owner_id != enrolled.owner_id
                    or state.session.device_id != enrolled.device_id
                    or state.certificate_sha256 != fingerprint
                    or state.credential_generation != enrolled.credential_generation
                ):
                    return ChallengeIssueResult(False, "TRANSPORT_CREDENTIAL_CHANGED")
                if now_epoch_ms >= state.session.expires_at_epoch_ms:
                    return ChallengeIssueResult(False, "TRANSPORT_SESSION_EXPIRED")

            for nonce, issued in tuple(state.challenges.items()):
                if now_monotonic_ns >= issued.expires_monotonic_ns:
                    del state.challenges[nonce]
            if len(state.challenges) >= MAX_OUTSTANDING_CHALLENGES_PER_SESSION:
                return ChallengeIssueResult(False, "SESSION_CHALLENGE_CAPACITY")

            result = issue_owner_consent_challenge(
                state.session,
                action=action,
                registry=self._consent_registry,
                now_epoch_ms=now_epoch_ms,
                nonce_factory=self._nonce_factory,
                arguments=arguments,
            )
            if not result.issued:
                return result
            challenge = result.capability.challenge
            if challenge.nonce in state.challenges:
                return ChallengeIssueResult(False, "DUPLICATE_CHALLENGE_NONCE")
            remaining_ms = challenge.expires_at_epoch_ms - now_epoch_ms
            if remaining_ms <= 0:
                return ChallengeIssueResult(False, "CHALLENGE_EXPIRED")
            state.challenges[challenge.nonce] = _IssuedChallenge(
                challenge=challenge,
                expires_monotonic_ns=now_monotonic_ns + remaining_ms * 1_000_000,
            )
            self._sessions[peer] = state
            return result

    def verify_and_consume(
        self,
        peer: ssl.SSLSocket,
        envelope: bytes,
        challenge: ConsentChallenge,
    ) -> ConsentAdmissionResult:
        """Verify only a challenge issued on this exact live TLS socket.

        Callers cannot provide an authenticated boolean, certificate digest,
        credential generation, session identifier or verification key. All
        transport and enrollment context is re-derived from trusted adapter
        state and registries. A new or resumed TLS connection has a different
        SSLSocket object and cannot inherit a previous connection's challenges.
        """
        clocks, clock_error = self._read_clocks()
        if clock_error is not None:
            return ConsentAdmissionResult(False, clock_error)
        now_epoch_ms, now_monotonic_ns = clocks
        with self._lock:
            binding, binding_error = self._current_peer_binding(peer, now_epoch_ms)
            if binding_error is not None:
                return ConsentAdmissionResult(False, binding_error)
            enrolled, fingerprint, _certificate_expiry_ms = binding

            state = self._sessions.get(peer)
            if state is None:
                return ConsentAdmissionResult(False, "TRANSPORT_SESSION_NOT_ISSUED")
            if (
                now_monotonic_ns >= state.expires_monotonic_ns
                or now_epoch_ms >= state.session.expires_at_epoch_ms
            ):
                return ConsentAdmissionResult(False, "TRANSPORT_SESSION_EXPIRED")
            if (
                state.session.owner_id != enrolled.owner_id
                or state.session.device_id != enrolled.device_id
                or state.certificate_sha256 != fingerprint
                or state.credential_generation != enrolled.credential_generation
            ):
                return ConsentAdmissionResult(False, "TRANSPORT_CREDENTIAL_CHANGED")
            if type(challenge) is not ConsentChallenge or type(challenge.nonce) is not str:
                return ConsentAdmissionResult(False, "CHALLENGE_NOT_ISSUED_ON_SESSION")
            issued = state.challenges.get(challenge.nonce)
            if issued is None or issued.challenge != challenge:
                return ConsentAdmissionResult(False, "CHALLENGE_NOT_ISSUED_ON_SESSION")
            if now_monotonic_ns >= issued.expires_monotonic_ns:
                return ConsentAdmissionResult(False, "CHALLENGE_EXPIRED")
            if (
                challenge.owner_id != state.session.owner_id
                or challenge.device_id != state.session.device_id
                or challenge.session_id != state.session.session_id
                or challenge.issued_at_epoch_ms < state.session.authenticated_at_epoch_ms
                or challenge.expires_at_epoch_ms > state.session.expires_at_epoch_ms
            ):
                return ConsentAdmissionResult(False, "TRANSPORT_SESSION_MISMATCH")

            try:
                owner_record = self._consent_registry.lookup_active_device(
                    challenge.device_id
                )
            except Exception:
                return ConsentAdmissionResult(False, "ENROLLMENT_REGISTRY_UNAVAILABLE")
            if type(owner_record) is not EnrolledOwnerDevice:
                return ConsentAdmissionResult(False, "DEVICE_NOT_ENROLLED")
            if type(owner_record.active) is not bool:
                return ConsentAdmissionResult(False, "ENROLLMENT_REGISTRY_INVALID")
            if owner_record.active is not True:
                return ConsentAdmissionResult(False, "DEVICE_NOT_ACTIVE")
            if (
                owner_record.owner_id != state.session.owner_id
                or owner_record.device_id != state.session.device_id
            ):
                return ConsentAdmissionResult(False, "OWNER_DEVICE_MISMATCH")
            if (
                owner_record.transport_certificate_sha256 != fingerprint
                or owner_record.credential_generation != enrolled.credential_generation
            ):
                return ConsentAdmissionResult(False, "ENROLLMENT_CREDENTIAL_MISMATCH")
            if type(owner_record.public_key_spki_der) is not bytes:
                return ConsentAdmissionResult(False, "INVALID_TRUSTED_KEY")

            return _verify_and_consume_bound(
                envelope,
                challenge=challenge,
                trusted_public_key_spki_der=owner_record.public_key_spki_der,
                enrollment_registry=self._consent_registry,
                transport_certificate_sha256=fingerprint,
                credential_generation=enrolled.credential_generation,
                now_epoch_ms=now_epoch_ms,
            )


    def verify_and_issue_capability(
        self,
        peer: ssl.SSLSocket,
        envelope: bytes,
        challenge: ConsentChallenge,
        *,
        arguments: dict,
    ) -> ActionCapabilityIssueResult:
        """Mint an opaque one-use capability after live mTLS and signed consent.

        Protocol v1 is intentionally limited here to read_screen with exactly
        empty arguments. Actions requiring parameters need a new signed,
        owner-visible protocol version; they are not silently treated as empty.
        """
        if type(arguments) is not dict:
            return ActionCapabilityIssueResult(False, "INVALID_ARGUMENTS")
        if type(challenge) is not ConsentChallenge:
            return ActionCapabilityIssueResult(False, "INVALID_CHALLENGE")
        if challenge.version == 2:
            return ActionCapabilityIssueResult(
                False, "V2_CAPABILITY_NOT_INTEGRATED"
            )
        if arguments:
            return ActionCapabilityIssueResult(
                False, "ARGUMENTS_NOT_SUPPORTED_BY_V1"
            )
        arguments_digest = _empty_action_arguments_digest(challenge.action)
        if arguments_digest is None:
            return ActionCapabilityIssueResult(
                False, "ACTION_ARGUMENT_SCHEMA_UNAVAILABLE"
            )

        # RLock keeps verification and capability registration atomic relative
        # to other operations performed through this adapter instance.
        with self._lock:
            admission = self.verify_and_consume(peer, envelope, challenge)
            if not admission.admitted:
                return ActionCapabilityIssueResult(False, admission.reason)
            verified_public_key_sha256 = admission.verified_public_key_sha256
            if (
                type(verified_public_key_sha256) is not str
                or re.fullmatch(r"[0-9a-f]{64}", verified_public_key_sha256) is None
            ):
                return ActionCapabilityIssueResult(
                    False, "VERIFIED_KEY_BINDING_MISSING"
                )

            clocks, clock_error = self._read_clocks()
            if clock_error is not None:
                return ActionCapabilityIssueResult(False, clock_error)
            now_epoch_ms, now_monotonic_ns = clocks
            binding, binding_error = self._current_peer_binding(peer, now_epoch_ms)
            if binding_error is not None:
                return ActionCapabilityIssueResult(False, binding_error)
            enrolled, fingerprint, _certificate_expiry_ms = binding

            state = self._sessions.get(peer)
            if state is None:
                return ActionCapabilityIssueResult(
                    False, "TRANSPORT_SESSION_NOT_ISSUED"
                )
            issued = state.challenges.get(challenge.nonce)
            if issued is None or issued.challenge != challenge:
                return ActionCapabilityIssueResult(
                    False, "CHALLENGE_NOT_ISSUED_ON_SESSION"
                )
            expires_monotonic_ns = min(
                state.expires_monotonic_ns,
                issued.expires_monotonic_ns,
            )
            if (
                now_monotonic_ns >= expires_monotonic_ns
                or now_epoch_ms >= state.session.expires_at_epoch_ms
            ):
                return ActionCapabilityIssueResult(False, "CAPABILITY_EXPIRED")
            if (
                state.session.owner_id != enrolled.owner_id
                or state.session.device_id != enrolled.device_id
                or state.certificate_sha256 != fingerprint
                or state.credential_generation != enrolled.credential_generation
            ):
                return ActionCapabilityIssueResult(
                    False, "TRANSPORT_CREDENTIAL_CHANGED"
                )

            try:
                owner_record = self._consent_registry.lookup_active_device(
                    challenge.device_id
                )
            except Exception:
                return ActionCapabilityIssueResult(
                    False, "ENROLLMENT_REGISTRY_UNAVAILABLE"
                )
            if type(owner_record) is not EnrolledOwnerDevice:
                return ActionCapabilityIssueResult(False, "DEVICE_NOT_ENROLLED")
            if type(owner_record.active) is not bool:
                return ActionCapabilityIssueResult(
                    False, "ENROLLMENT_REGISTRY_INVALID"
                )
            if owner_record.active is not True:
                return ActionCapabilityIssueResult(False, "DEVICE_NOT_ACTIVE")
            if (
                owner_record.owner_id != state.session.owner_id
                or owner_record.device_id != state.session.device_id
            ):
                return ActionCapabilityIssueResult(
                    False, "OWNER_DEVICE_MISMATCH"
                )
            if (
                owner_record.transport_certificate_sha256 != fingerprint
                or type(owner_record.credential_generation) is not int
                or owner_record.credential_generation
                != enrolled.credential_generation
            ):
                return ActionCapabilityIssueResult(
                    False, "ENROLLMENT_CREDENTIAL_MISMATCH"
                )
            if (
                type(owner_record.public_key_spki_der) is not bytes
                or not 1 <= len(owner_record.public_key_spki_der) <= 512
            ):
                return ActionCapabilityIssueResult(False, "INVALID_TRUSTED_KEY")
            if (
                hashlib.sha256(owner_record.public_key_spki_der).hexdigest()
                != verified_public_key_sha256
            ):
                return ActionCapabilityIssueResult(
                    False, "ENROLLMENT_KEY_CHANGED_DURING_ADMISSION"
                )

            capability = VerifiedOwnerActionCapability()
            record = _IssuedActionCapability(
                capability=capability,
                nonce=challenge.nonce,
                owner_id=state.session.owner_id,
                device_id=state.session.device_id,
                session_id=state.session.session_id,
                action=challenge.action,
                arguments_sha256=arguments_digest,
                transport_certificate_sha256=fingerprint,
                credential_generation=enrolled.credential_generation,
                consent_public_key_sha256=verified_public_key_sha256,
                expires_monotonic_ns=expires_monotonic_ns,
            )
            state.capabilities[id(capability)] = record
            return ActionCapabilityIssueResult(
                True, "VERIFIED_ACTION_CAPABILITY_ISSUED", capability
            )

    def consume_action_capability(
        self,
        peer: ssl.SSLSocket,
        capability: VerifiedOwnerActionCapability,
        *,
        action: str,
        arguments: dict,
    ) -> ActionCapabilityAdmissionResult:
        """Consume once after revalidating the exact live peer and enrollment.

        This is admission evidence only. It does not check Android runtime
        permissions and does not execute or dispatch a device action.
        """
        if type(peer) is not ssl.SSLSocket:
            return ActionCapabilityAdmissionResult(False, "INVALID_TLS_SOCKET")
        if type(capability) is not VerifiedOwnerActionCapability:
            return ActionCapabilityAdmissionResult(False, "INVALID_CAPABILITY")
        if type(action) is not str:
            return ActionCapabilityAdmissionResult(False, "ACTION_MISMATCH")
        if type(arguments) is not dict:
            return ActionCapabilityAdmissionResult(False, "INVALID_ARGUMENTS")
        if arguments:
            return ActionCapabilityAdmissionResult(False, "ARGUMENTS_MISMATCH")

        with self._lock:
            state = self._sessions.get(peer)
            if state is None:
                return ActionCapabilityAdmissionResult(
                    False, "CAPABILITY_SESSION_NOT_FOUND"
                )
            capability_key = id(capability)
            record = state.capabilities.get(capability_key)
            if record is None or record.capability is not capability:
                return ActionCapabilityAdmissionResult(
                    False, "CAPABILITY_NOT_ACTIVE"
                )
            if action != record.action:
                return ActionCapabilityAdmissionResult(False, "ACTION_MISMATCH")
            arguments_digest = _empty_action_arguments_digest(action)
            if (
                arguments_digest is None
                or arguments_digest != record.arguments_sha256
            ):
                return ActionCapabilityAdmissionResult(
                    False, "ARGUMENTS_MISMATCH"
                )

            def discard() -> None:
                state.capabilities.pop(capability_key, None)
                state.challenges.pop(record.nonce, None)

            clocks, clock_error = self._read_clocks()
            if clock_error is not None:
                discard()
                return ActionCapabilityAdmissionResult(False, clock_error)
            now_epoch_ms, now_monotonic_ns = clocks
            if (
                now_monotonic_ns >= record.expires_monotonic_ns
                or now_monotonic_ns >= state.expires_monotonic_ns
                or now_epoch_ms >= state.session.expires_at_epoch_ms
            ):
                discard()
                return ActionCapabilityAdmissionResult(False, "CAPABILITY_EXPIRED")

            binding, binding_error = self._current_peer_binding(
                peer, now_epoch_ms
            )
            if binding_error is not None:
                if binding_error != "TRANSPORT_REGISTRY_UNAVAILABLE":
                    discard()
                return ActionCapabilityAdmissionResult(False, binding_error)
            enrolled, fingerprint, _certificate_expiry_ms = binding
            if (
                state.session.owner_id != record.owner_id
                or state.session.device_id != record.device_id
                or state.session.session_id != record.session_id
                or state.certificate_sha256 != record.transport_certificate_sha256
                or fingerprint != record.transport_certificate_sha256
                or enrolled.owner_id != record.owner_id
                or enrolled.device_id != record.device_id
            ):
                discard()
                return ActionCapabilityAdmissionResult(
                    False, "CAPABILITY_CONTEXT_MISMATCH"
                )
            if (
                state.credential_generation != record.credential_generation
                or enrolled.credential_generation != record.credential_generation
            ):
                discard()
                return ActionCapabilityAdmissionResult(
                    False, "TRANSPORT_CREDENTIAL_CHANGED"
                )
            issued = state.challenges.get(record.nonce)
            if (
                issued is None
                or issued.challenge.owner_id != record.owner_id
                or issued.challenge.device_id != record.device_id
                or issued.challenge.action != record.action
                or issued.challenge.session_id != record.session_id
                or now_epoch_ms >= issued.challenge.expires_at_epoch_ms
                or now_monotonic_ns >= issued.expires_monotonic_ns
            ):
                discard()
                return ActionCapabilityAdmissionResult(False, "CHALLENGE_EXPIRED")

            try:
                owner_record = self._consent_registry.lookup_active_device(
                    record.device_id
                )
            except Exception:
                return ActionCapabilityAdmissionResult(
                    False, "ENROLLMENT_REGISTRY_UNAVAILABLE"
                )
            if type(owner_record) is not EnrolledOwnerDevice:
                discard()
                return ActionCapabilityAdmissionResult(
                    False, "DEVICE_NOT_ENROLLED"
                )
            if type(owner_record.active) is not bool:
                discard()
                return ActionCapabilityAdmissionResult(
                    False, "ENROLLMENT_REGISTRY_INVALID"
                )
            if owner_record.active is not True:
                discard()
                return ActionCapabilityAdmissionResult(False, "DEVICE_NOT_ACTIVE")
            if (
                owner_record.owner_id != record.owner_id
                or owner_record.device_id != record.device_id
            ):
                discard()
                return ActionCapabilityAdmissionResult(
                    False, "OWNER_DEVICE_MISMATCH"
                )
            if (
                owner_record.transport_certificate_sha256
                != record.transport_certificate_sha256
                or type(owner_record.credential_generation) is not int
                or owner_record.credential_generation != record.credential_generation
            ):
                discard()
                return ActionCapabilityAdmissionResult(
                    False, "ENROLLMENT_CREDENTIAL_MISMATCH"
                )
            if (
                type(owner_record.public_key_spki_der) is not bytes
                or not 1 <= len(owner_record.public_key_spki_der) <= 512
            ):
                discard()
                return ActionCapabilityAdmissionResult(
                    False, "INVALID_TRUSTED_KEY"
                )
            if (
                hashlib.sha256(owner_record.public_key_spki_der).hexdigest()
                != record.consent_public_key_sha256
            ):
                discard()
                return ActionCapabilityAdmissionResult(
                    False, "ENROLLMENT_KEY_MISMATCH"
                )

            fresh_clocks, fresh_clock_error = self._read_clocks()
            if fresh_clock_error is not None:
                discard()
                return ActionCapabilityAdmissionResult(
                    False, fresh_clock_error
                )
            _fresh_epoch_ms, fresh_monotonic_ns = fresh_clocks
            if (
                fresh_monotonic_ns >= record.expires_monotonic_ns
                or fresh_monotonic_ns >= state.expires_monotonic_ns
            ):
                discard()
                return ActionCapabilityAdmissionResult(False, "CAPABILITY_EXPIRED")

            discard()
            return ActionCapabilityAdmissionResult(
                True, "CAPABILITY_CONSUMED_NO_EXECUTION"
            )

