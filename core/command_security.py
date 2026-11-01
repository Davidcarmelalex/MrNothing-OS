"""Authenticated command freshness and replay defense, independent of transport."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hmac
import hashlib
import json
import threading

@dataclass(frozen=True)
class SignedCommand:
    command_id: str
    issued_at: int
    action: str
    arguments: dict
    signature: str

def canonical_payload(command: SignedCommand) -> bytes:
    return json.dumps({
        "command_id": command.command_id,
        "issued_at": command.issued_at,
        "action": command.action,
        "arguments": command.arguments,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

def sign(command: SignedCommand, key: bytes) -> str:
    return hmac.new(key, canonical_payload(command), hashlib.sha256).hexdigest()

class ReplayGuard:
    """In-memory guard for one process; production requires durable shared storage."""
    def __init__(self, *, max_age_seconds: int = 60, max_entries: int = 10000):
        self.max_age_seconds = max_age_seconds
        self.max_entries = max_entries
        self._seen: dict[str, int] = {}
        self._lock = threading.Lock()

    def verify(self, command: SignedCommand, key: bytes, now: int | None = None) -> bool:
        if len(key) < 32 or not command.command_id or len(command.command_id) > 128:
            return False
        if not isinstance(command.arguments, dict):
            return False
        current = now if now is not None else int(datetime.now(timezone.utc).timestamp())
        if command.issued_at > current + 5 or current - command.issued_at > self.max_age_seconds:
            return False
        if not hmac.compare_digest(sign(command, key), command.signature):
            return False
        with self._lock:
            self._seen = {k: v for k, v in self._seen.items() if current - v <= self.max_age_seconds}
            if command.command_id in self._seen or len(self._seen) >= self.max_entries:
                return False
            self._seen[command.command_id] = current
        return True
