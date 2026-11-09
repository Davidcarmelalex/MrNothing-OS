"""SEC-014B: offline verifier for one-use owner-UI screen-action capabilities.

This is NOT a consent issuer, Android permission checker, or action executor.
Only a future trusted Android UI, using a protected key and owner-authenticated
flow, may sign capabilities. The key and verification context must never come
from a model, remote command, or user-supplied tool arguments.
"""
from dataclasses import dataclass
import hashlib
import hmac
import json
import secrets
import threading
import time


SCREEN_ACTIONS = frozenset({"read_screen", "navigate", "scroll"})
MAX_TTL_NS = 30_000_000_000
MAX_REVOKED_SESSIONS = 1024


@dataclass(frozen=True)
class ConsentCapability:
    version: int
    device_id: str
    owner_id: str
    session_id: str
    action: str
    nonce: str
    epoch: str
    issued_mono_ns: int
    expires_mono_ns: int
    signature: str


def _canonical(cap: ConsentCapability) -> bytes:
    return json.dumps({
        "version": cap.version,
        "device_id": cap.device_id,
        "owner_id": cap.owner_id,
        "session_id": cap.session_id,
        "action": cap.action,
        "nonce": cap.nonce,
        "epoch": cap.epoch,
        "issued_mono_ns": cap.issued_mono_ns,
        "expires_mono_ns": cap.expires_mono_ns,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _identifier(value: object) -> bool:
    return type(value) is str and 1 <= len(value) <= 128 and all(
        32 < ord(char) < 127 for char in value
    )


class ConsentVerifier:
    """In-memory, fail-closed capability consumption; never executes actions.

    A new random epoch rejects all prior-process capabilities after restart.
    Used nonces and revoked sessions are bounded. If the revocation registry
    fills, the verifier denies all capabilities for this epoch rather than
    silently dropping a revocation. Caller-supplied context is assumed to
    originate from a trusted host, not the LLM. The production Android trust
    boundary is NOT implemented here.
    """

    def __init__(self, *, device_id: str, owner_id: str,
                 owner_ui_verification_key: bytes, clock=None,
                 max_uses: int = 1024,
                 max_revoked_sessions: int = MAX_REVOKED_SESSIONS):
        if not _identifier(device_id) or not _identifier(owner_id):
            raise ValueError("invalid trusted device/owner identity")
        if type(owner_ui_verification_key) is not bytes or len(owner_ui_verification_key) < 32:
            raise ValueError("trusted UI key must be at least 32 bytes")
        if (type(max_uses) is not int or not 1 <= max_uses <= 100_000 or
            type(max_revoked_sessions) is not int or
            not 1 <= max_revoked_sessions <= 100_000):
            raise ValueError("invalid capacity")
        self.device_id = device_id
        self.owner_id = owner_id
        self._key = owner_ui_verification_key
        self._clock = clock if clock is not None else time.monotonic_ns
        self.epoch = secrets.token_hex(16)
        self._used: set[tuple[str, str]] = set()
        self._revoked: set[str] = set()
        self._max_uses = max_uses
        self._max_revoked_sessions = max_revoked_sessions
        # If a new revocation cannot be recorded, deny every capability in
        # this epoch rather than silently leaving that session authorized.
        self._revocation_overflow = False
        self._lock = threading.Lock()

    def revoke_session(self, session_id: str) -> bool:
        """Record revocation; False means capacity triggered epoch-wide denial."""
        if not _identifier(session_id):
            raise ValueError("invalid session")
        with self._lock:
            if session_id in self._revoked:
                return True
            if len(self._revoked) >= self._max_revoked_sessions:
                self._revocation_overflow = True
                return False
            self._revoked.add(session_id)
            return True

    def verify_and_consume(self, cap: ConsentCapability, *,
                           session_id: str, action: str) -> bool:
        """Return only admission evidence; does not grant Android permissions."""
        if type(cap) is not ConsentCapability:
            return False
        if (type(cap.version) is not int or cap.version != 1 or
            not all(_identifier(v) for v in (
                cap.device_id, cap.owner_id, cap.session_id, cap.action,
                cap.nonce, cap.epoch, session_id, action
            )) or
            not 16 <= len(cap.nonce) <= 128 or
            cap.action not in SCREEN_ACTIONS or action not in SCREEN_ACTIONS or
            cap.action != action or cap.device_id != self.device_id or
            cap.owner_id != self.owner_id or cap.session_id != session_id or
            cap.epoch != self.epoch or
            type(cap.issued_mono_ns) is not int or
            type(cap.expires_mono_ns) is not int or
            not 0 < cap.expires_mono_ns - cap.issued_mono_ns <= MAX_TTL_NS or
            type(cap.signature) is not str or len(cap.signature) != 64 or
            any(c not in "0123456789abcdef" for c in cap.signature)):
            return False
        now = self._clock()
        if type(now) is not int or not cap.issued_mono_ns <= now < cap.expires_mono_ns:
            return False
        expected = hmac.new(self._key, _canonical(cap), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, cap.signature):
            return False
        with self._lock:
            marker = (cap.session_id, cap.nonce)
            if (self._revocation_overflow or cap.session_id in self._revoked or
                marker in self._used or len(self._used) >= self._max_uses):
                return False
            # Re-check time inside the critical section to prevent late grants.
            now = self._clock()
            if type(now) is not int or not cap.issued_mono_ns <= now < cap.expires_mono_ns:
                return False
            self._used.add(marker)
            return True
