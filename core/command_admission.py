"""Fail-closed, transport-neutral admission of signed device commands.

This is a prototype admission gate, NOT a deployed remote-control endpoint.
The caller must authenticate the transport and select a unique key for the
authenticated device. No command is executed by this module.
"""
from contextlib import closing
from dataclasses import dataclass
import hmac
import math
import os
import sqlite3
import stat
import string
from pathlib import Path

from core.command_security import SignedCommand, canonical_payload, sign
from core.hermes_gateway import CommandEnvelope, validate


@dataclass(frozen=True)
class AdmissionResult:
    admitted: bool
    reason: str


MAX_CANONICAL_PAYLOAD_BYTES = 8192
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 4096
MAX_JSON_TEXT_CHARS = 16384
MAX_SQLITE_INTEGER = (1 << 63) - 1


def _is_strict_json_value(value: object) -> bool:
    """Accept only bounded JSON-native values, without invoking custom code."""
    pending: list[tuple[object, int]] = [(value, 0)]
    scheduled = 1
    text_characters = 0
    while pending:
        current, depth = pending.pop()
        if depth > MAX_JSON_DEPTH:
            return False
        current_type = type(current)
        if current_type is dict:
            if scheduled + len(current) > MAX_JSON_NODES:
                return False
            children = []
            for key, child in current.items():
                if type(key) is not str:
                    return False
                text_characters += len(key)
                if text_characters > MAX_JSON_TEXT_CHARS:
                    return False
                children.append((child, depth + 1))
            scheduled += len(children)
            pending.extend(children)
        elif current_type is list:
            if scheduled + len(current) > MAX_JSON_NODES:
                return False
            scheduled += len(current)
            pending.extend((child, depth + 1) for child in current)
        elif current_type is float:
            if not math.isfinite(current):
                return False
        elif current_type is str:
            text_characters += len(current)
            if text_characters > MAX_JSON_TEXT_CHARS:
                return False
        elif current is None or current_type in (bool, int):
            continue
        else:
            return False
    return True


class DurableReplayLedger:
    """SQLite-backed replay reservation surviving process restarts.

    One SQLite database is shared by workers on one host. This is not a
    distributed ledger; deployment across hosts requires coordinated storage.
    """

    def __init__(self, path: str | Path, *, ttl_seconds: int = 60, max_entries: int = 10000):
        if (type(ttl_seconds) is not int or ttl_seconds < 1
                or type(max_entries) is not int or max_entries < 1
                or ttl_seconds > MAX_SQLITE_INTEGER):
            raise ValueError("invalid ledger limits")
        raw_path = os.fspath(path)
        if (type(raw_path) is not str or not raw_path.strip()
                or raw_path == ":memory:" or raw_path.startswith("file:")):
            raise ValueError("replay ledger requires a durable filesystem path")
        self.path = str(Path(raw_path).absolute())
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._file_identity = self._prepare_file()
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS seen ("
                    "device_id TEXT NOT NULL, command_id TEXT NOT NULL, seen_at INTEGER NOT NULL,"
                    "PRIMARY KEY (device_id, command_id))"
                )
                db.execute("CREATE INDEX IF NOT EXISTS seen_age ON seen (seen_at)")
                # The high-water mark survives TTL pruning and process restarts.
                # On legacy ledgers, seed from the latest still-retained nonce.
                clock_table_exists = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='ledger_clock'"
                ).fetchone() is not None
                db.execute(
                    "CREATE TABLE IF NOT EXISTS ledger_clock ("
                    "id INTEGER PRIMARY KEY CHECK (id=1), max_now INTEGER NOT NULL)"
                )
                if not clock_table_exists:
                    # Only a genuinely legacy database may initialize the
                    # watermark. Never repair a deleted row on restart.
                    db.execute(
                        "INSERT INTO ledger_clock (id,max_now) "
                        "SELECT 1, MAX(COALESCE((SELECT MAX(seen_at) FROM seen),0),0)"
                    )
                row = db.execute(
                    "SELECT max_now FROM ledger_clock WHERE id=1"
                ).fetchone()
                latest_nonce = db.execute(
                    "SELECT COALESCE(MAX(seen_at),0) FROM seen"
                ).fetchone()[0]
                if (row is None or type(row[0]) is not int
                        or not 0 <= row[0] <= MAX_SQLITE_INTEGER
                        or type(latest_nonce) is not int
                        or not 0 <= latest_nonce <= row[0]):
                    raise sqlite3.DatabaseError("replay ledger clock watermark inconsistent")
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

    def _parent_is_safe(self) -> bool:
        """Reject directories where other users can replace the ledger path."""
        if os.name != "posix":
            return True
        # SQLite creates rollback/WAL/shared-memory sidecars beside the DB.
        # Sticky directories protect the DB inode but not unclaimed sidecar
        # names, so the immediate parent must be private to this process UID.
        # Ancestors may be trusted sticky directories (e.g. /tmp), but must
        # not be untrusted, nonsticky-writable or symlink components.
        directory = os.path.dirname(self.path)
        immediate_parent = True
        while True:
            try:
                info = os.lstat(directory)
            except OSError:
                return False
            writable_by_others = bool(info.st_mode & 0o022)
            sticky_protected = bool(info.st_mode & stat.S_ISVTX)
            trusted_directory_owner = info.st_uid in (os.geteuid(), 0)
            if (immediate_parent and (
                    info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) & 0o077)):
                return False
            if (not stat.S_ISDIR(info.st_mode)
                    or not trusted_directory_owner
                    or (writable_by_others and not sticky_protected)):
                return False
            parent = os.path.dirname(directory)
            if parent == directory:
                return True
            directory = parent
            immediate_parent = False

    def _prepare_file(self) -> tuple[int, int]:
        """Create a private ledger before SQLite opens it; reject unsafe files."""
        if not self._parent_is_safe():
            raise ValueError("replay ledger parent directory is unsafe")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(self.path, flags, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(fd)
        try:
            info = os.stat(self.path, follow_symlinks=False)
        except OSError as error:
            raise ValueError("replay ledger file unavailable") from error
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("replay ledger must be a regular non-symlink file")
        if os.name == "posix" and (
            stat.S_IMODE(info.st_mode) & 0o077
            or info.st_uid != os.geteuid()
            or info.st_nlink != 1
        ):
            raise ValueError("replay ledger file must be owner-only and unlinked elsewhere")
        return (info.st_dev, info.st_ino)

    def _verify_file(self) -> None:
        """Deny reuse if the file is deleted, replaced, or made accessible to others."""
        try:
            info = os.stat(self.path, follow_symlinks=False)
        except OSError as error:
            raise sqlite3.OperationalError("replay ledger file unavailable") from error
        if (not stat.S_ISREG(info.st_mode)
                or (info.st_dev, info.st_ino) != self._file_identity
                or not self._parent_is_safe()
                or (os.name == "posix" and (
                    stat.S_IMODE(info.st_mode) & 0o077
                    or info.st_uid != os.geteuid()
                    or info.st_nlink != 1
                ))):
            raise sqlite3.OperationalError("replay ledger file identity or permissions changed")

    def _connect(self):
        self._verify_file()
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        try:
            self._verify_file()
            return db
        except Exception:
            db.close()
            raise

    def reserve(self, device_id: str, command_id: str, now: int) -> bool:
        """Reserve once atomically; database failures propagate to fail closed."""
        if type(now) is not int or not 0 <= now <= MAX_SQLITE_INTEGER:
            raise sqlite3.DataError("replay ledger timestamp outside SQLite INTEGER range")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT max_now FROM ledger_clock WHERE id=1"
                ).fetchone()
                # Revalidate in the write transaction on every admission.
                # Another writer could corrupt the clock after initialization.
                latest_nonce = db.execute(
                    "SELECT COALESCE(MAX(seen_at),0) FROM seen"
                ).fetchone()[0]
                if (row is None or type(row[0]) is not int
                        or not 0 <= row[0] <= MAX_SQLITE_INTEGER
                        or type(latest_nonce) is not int
                        or not 0 <= latest_nonce <= row[0]):
                    raise sqlite3.DatabaseError("replay ledger clock watermark inconsistent")
                if now < row[0]:
                    raise sqlite3.DataError("replay ledger clock rollback")
                # Clock and nonce reservation commit together. Rejected requests
                # roll back both, preserving the last accepted time.
                db.execute("UPDATE ledger_clock SET max_now=? WHERE id=1", (now,))
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
    if (type(command.issued_at) is not int or type(now) is not int
            or not 0 <= command.issued_at <= MAX_SQLITE_INTEGER
            or not 0 <= now <= MAX_SQLITE_INTEGER):
        return AdmissionResult(False, "INVALID_TIMESTAMP")
    if type(command.action) is not str or not (1 <= len(command.action) <= 128):
        return AdmissionResult(False, "INVALID_PAYLOAD")
    if type(command.arguments) is not dict:
        return AdmissionResult(False, "INVALID_PAYLOAD")
    if not isinstance(command.signature, str) or len(command.signature) != 64:
        return AdmissionResult(False, "INVALID_SIGNATURE")
    if any(ch not in string.hexdigits.lower() for ch in command.signature):
        return AdmissionResult(False, "INVALID_SIGNATURE")
    if command.issued_at > now + 5 or now - command.issued_at > ledger.ttl_seconds:
        return AdmissionResult(False, "EXPIRED_OR_FUTURE")
    try:
        # Python tuples, non-string object keys, custom containers and unbounded
        # object graphs are not valid wire JSON and must fail before signing.
        if not _is_strict_json_value(command.arguments):
            return AdmissionResult(False, "INVALID_PAYLOAD")
        if len(canonical_payload(command)) > MAX_CANONICAL_PAYLOAD_BYTES:
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
