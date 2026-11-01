"""Fail-closed, transport-neutral admission of signed device commands.

This is a prototype admission gate, NOT a deployed remote-control endpoint.
The caller must authenticate the transport and select a unique key for the
authenticated device. No command is executed by this module.
"""
from dataclasses import dataclass
import hmac
import json
import sqlite3
import string
from pathlib import Path

from core.command_security import SignedCommand, canonical_payload, sign
from core.hermes_gateway import CommandEnvelope, validate


@dataclass(frozen=True)
class AdmissionResult:
    admitted: bool
    reason: str


class DurableReplayLedger:
    """SQLite-backed replay reservation surviving process restarts.

    One SQLite database is shared by workers on one host. This is not a
    distributed ledger; deployment across hosts requires coordinated storage.
    """

    def __init__(self, path: str | Path, *, ttl_seconds: int = 60, max_entries: int = 10000):
        if ttl_seconds < 1 or max_entries < 1:
            raise ValueError("invalid ledger limits")
        self.path = str(path)
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS seen ("
                "device_id TEXT NOT NULL, command_id TEXT NOT NULL, seen_at INTEGER NOT NULL,"
                "PRIMARY KEY (device_id, command_id))"
            )
            db.execute("CREATE INDEX IF NOT EXISTS seen_age ON seen (seen_at)")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=5, isolation_level=None)

    def reserve(self, device_id: str, command_id: str, now: int) -> bool:
        """Reserve once atomically; database failures propagate to fail closed."""
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("DELETE FROM seen WHERE seen_at < ?", (now - self.ttl_seconds,))
                if db.execute("SELECT 1 FROM seen WHERE device_id=? AND command_id=?",
                              (device_id, command_id)).fetchone():
                    db.execute("ROLLBACK")
                    return False
                count = db.execute("SELECT COUNT(*) FROM seen").fetchone()[0]
                if count >= self.max_entries:
                    db.execute("ROLLBACK")
                    return False
                db.execute("INSERT INTO seen(device_id,command_id,seen_at) VALUES(?,?,?)",
                           (device_id, command_id, now))
                db.execute("COMMIT")
                return True
            except Exception:
                db.execute("ROLLBACK")
                raise


def admit_signed_command(
    command: SignedCommand,
    *,
    device_id: str,
    device_key: bytes,
    transport_authenticated: bool,
    ledger: DurableReplayLedger,
    now: int,
) -> AdmissionResult:
    """Verify identity, freshness, signature, policy and durable replay before admission.

    Device identity MUST come from the authenticated channel, never a model or
    untrusted payload. A unique secret per device is mandatory in this v1
    protocol; future protocols should also sign the device ID explicitly.
    """
    if not transport_authenticated:
        return AdmissionResult(False, "UNAUTHENTICATED")
    if not isinstance(device_id, str) or not (1 <= len(device_id) <= 128):
        return AdmissionResult(False, "INVALID_DEVICE")
    if any(ch not in string.ascii_letters + string.digits + "-_." for ch in device_id):
        return AdmissionResult(False, "INVALID_DEVICE")
    if not isinstance(device_key, bytes) or len(device_key) < 32:
        return AdmissionResult(False, "INVALID_DEVICE_KEY")
    if not isinstance(command, SignedCommand):
        return AdmissionResult(False, "INVALID_COMMAND")
    if not isinstance(command.command_id, str) or not (1 <= len(command.command_id) <= 128):
        return AdmissionResult(False, "INVALID_COMMAND_ID")
    if type(command.issued_at) is not int or type(now) is not int:
        return AdmissionResult(False, "INVALID_TIMESTAMP")
    if not isinstance(command.action, str) or not isinstance(command.arguments, dict):
        return AdmissionResult(False, "INVALID_PAYLOAD")
    if not isinstance(command.signature, str) or len(command.signature) != 64:
        return AdmissionResult(False, "INVALID_SIGNATURE")
    if any(ch not in string.hexdigits.lower() for ch in command.signature):
        return AdmissionResult(False, "INVALID_SIGNATURE")
    if command.issued_at > now + 5 or now - command.issued_at > ledger.ttl_seconds:
        return AdmissionResult(False, "EXPIRED_OR_FUTURE")
    try:
        # Strict JSON forbids NaN/Infinity and non-JSON arguments.
        json.dumps(command.arguments, allow_nan=False)
        if len(canonical_payload(command)) > 8192:
            return AdmissionResult(False, "PAYLOAD_TOO_LARGE")
        expected = sign(command, device_key)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return AdmissionResult(False, "INVALID_PAYLOAD")
    if not hmac.compare_digest(expected, command.signature):
        return AdmissionResult(False, "BAD_SIGNATURE")
    decision = validate(
        CommandEnvelope(command.command_id, command.action, command.arguments),
        authenticated=True,
    )
    if not decision.accepted:
        return AdmissionResult(False, decision.reason)
    try:
        if not ledger.reserve(device_id, command.command_id, now):
            return AdmissionResult(False, "REPLAY_OR_CAPACITY")
    except sqlite3.Error:
        return AdmissionResult(False, "LEDGER_UNAVAILABLE")
    return AdmissionResult(True, "ADMITTED_NO_EXECUTION")
