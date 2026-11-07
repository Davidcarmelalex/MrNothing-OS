"""AGENT-004H durable final-action reservation state machine.

Storage only: this module does not authenticate transports, verify owner consent,
query Android permissions, or execute actions. Trusted adapters must construct
requests from retained verifier-created capability records.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
from typing import Callable, Iterator

_IDENTIFIER = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_ACTION = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_NONCE = re.compile(r"^[0-9a-f]{32}$")
_OUTCOME = re.compile(r"^[A-Z0-9_]{1,64}$")
_ALLOWED_ACTIONS = frozenset({"read_screen", "navigate", "scroll"})
_DOMAIN = b"mrnothing-action-reservation-v1\x00"
_MAX_I64 = (1 << 63) - 1
_MAX_TTL_MS = 30_000
_SCHEMA_VERSION = 1

RESERVED = "RESERVED"
DISPATCH_STARTED = "DISPATCH_STARTED"
COMPLETED = "COMPLETED"
FAILED_NO_EFFECT = "FAILED_NO_EFFECT"
CANCELLED = "CANCELLED"
UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"


class ReservationStoreUnavailable(RuntimeError):
    """Storage failed; callers must deny dispatch and must not use a memory fallback."""


@dataclass(frozen=True)
class ActionReservationRequest:
    owner_id: str
    device_id: str
    session_id: str
    capability_nonce: str
    protocol_version: int
    action_id: str
    arguments_sha256: str
    issued_at_epoch_ms: int
    expires_at_epoch_ms: int
    transport_certificate_sha256: str
    credential_generation: int
    consent_public_key_sha256: str


@dataclass(frozen=True)
class ReservationDecision:
    """A storage transition result; applied never means action authorization."""

    applied: bool
    reason: str
    idempotency_key: str
    state: str | None
    created: bool = False


@dataclass(frozen=True)
class ActionReservationRecord:
    idempotency_key: str
    owner_id: str
    device_id: str
    session_id: str
    capability_nonce: str
    protocol_version: int
    action_id: str
    arguments_sha256: str
    issued_at_epoch_ms: int
    expires_at_epoch_ms: int
    transport_certificate_sha256: str
    credential_generation: int
    consent_public_key_sha256: str
    state: str
    outcome_code: str | None
    outcome_sha256: str | None
    created_at_epoch_ms: int
    updated_at_epoch_ms: int


def _identifier(value: object) -> bool:
    return type(value) is str and _IDENTIFIER.fullmatch(value) is not None


def _binding(request: object) -> dict[str, object] | None:
    if type(request) is not ActionReservationRequest:
        return None
    if not all(_identifier(v) for v in (
        request.owner_id, request.device_id, request.session_id
    )):
        return None
    if type(request.capability_nonce) is not str or _NONCE.fullmatch(
        request.capability_nonce
    ) is None:
        return None
    if type(request.protocol_version) is not int or request.protocol_version not in (1, 2):
        return None
    if (
        type(request.action_id) is not str
        or _ACTION.fullmatch(request.action_id) is None
        or request.action_id not in _ALLOWED_ACTIONS
        or (request.protocol_version == 1 and request.action_id != "read_screen")
    ):
        return None
    for digest in (
        request.arguments_sha256,
        request.transport_certificate_sha256,
        request.consent_public_key_sha256,
    ):
        if type(digest) is not str or _SHA256.fullmatch(digest) is None:
            return None
    if (
        type(request.credential_generation) is not int
        or not 1 <= request.credential_generation <= _MAX_I64
    ):
        return None
    if (
        type(request.issued_at_epoch_ms) is not int
        or type(request.expires_at_epoch_ms) is not int
        or not 0 <= request.issued_at_epoch_ms < request.expires_at_epoch_ms <= _MAX_I64
        or request.expires_at_epoch_ms - request.issued_at_epoch_ms > _MAX_TTL_MS
    ):
        return None
    return {
        "owner_id": request.owner_id,
        "device_id": request.device_id,
        "session_id": request.session_id,
        "capability_nonce": request.capability_nonce,
        "protocol_version": request.protocol_version,
        "action_id": request.action_id,
        "arguments_sha256": request.arguments_sha256,
        "issued_at_epoch_ms": request.issued_at_epoch_ms,
        "expires_at_epoch_ms": request.expires_at_epoch_ms,
        "transport_certificate_sha256": request.transport_certificate_sha256,
        "credential_generation": request.credential_generation,
        "consent_public_key_sha256": request.consent_public_key_sha256,
    }


def derive_idempotency_key(request: ActionReservationRequest) -> str:
    binding = _binding(request)
    if binding is None:
        raise ValueError("invalid action reservation request")
    canonical = json.dumps(
        binding, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + canonical).hexdigest()


class DurableActionReservationLedger:
    """Atomic one-host action reservation ledger; not a distributed lock."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        max_entries: int = 100_000,
        clock_ms: Callable[[], int] | None = None,
        busy_timeout_ms: int = 5_000,
    ) -> None:
        if type(max_entries) is not int or not 1 <= max_entries <= 1_000_000:
            raise ValueError("invalid reservation capacity")
        if type(busy_timeout_ms) is not int or not 1 <= busy_timeout_ms <= 60_000:
            raise ValueError("invalid busy timeout")
        raw = os.fspath(path)
        if type(raw) is not str or not raw.strip() or raw == ":memory:" or raw.startswith("file:"):
            raise ValueError("a file-backed SQLite path is required")
        self.path = str(Path(raw).absolute())
        self.max_entries = max_entries
        self._clock_ms = clock_ms or (lambda: int(time.time() * 1000))
        self._busy_timeout_ms = busy_timeout_ms
        try:
            self._prepare_file()
        except ValueError:
            raise
        except OSError as error:
            raise ReservationStoreUnavailable("reservation path unavailable") from error
        self._initialize()

    def _prepare_file(self) -> None:
        path = Path(self.path)
        if path.is_symlink():
            raise ValueError("reservation database must not be a symlink")
        if path.exists():
            info = path.stat()
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("reservation database must be a regular file")
            if os.name == "posix" and stat.S_IMODE(info.st_mode) & 0o077:
                raise ValueError("reservation database permissions must be owner-only")
            return
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(self.path, flags, 0o600)
        except FileExistsError:
            if path.is_symlink() or not path.is_file():
                raise ValueError("unsafe reservation database path")
            info = path.stat()
            if os.name == "posix" and stat.S_IMODE(info.st_mode) & 0o077:
                raise ValueError("reservation database permissions must be owner-only")
        else:
            os.close(fd)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(
            self.path, timeout=self._busy_timeout_ms / 1000,
            isolation_level=None,
        )
        db.row_factory = sqlite3.Row
        db.execute(f"PRAGMA busy_timeout={self._busy_timeout_ms}")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        return db

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                try:
                    yield db
                    db.execute("COMMIT")
                except BaseException:
                    try:
                        db.execute("ROLLBACK")
                    except sqlite3.Error:
                        pass
                    raise
        except sqlite3.Error as error:
            raise ReservationStoreUnavailable("reservation database operation failed") from error

    def _now(self) -> int:
        try:
            value = self._clock_ms()
        except Exception as error:
            raise ReservationStoreUnavailable("reservation clock unavailable") from error
        if type(value) is not int or not 0 <= value <= _MAX_I64:
            raise ReservationStoreUnavailable("reservation clock invalid")
        return value

    def _initialize(self) -> None:
        try:
            with closing(self._connect()) as db:
                db.execute("PRAGMA journal_mode=WAL")
            with self._transaction() as db:
                version = db.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    db.execute("""
                        CREATE TABLE IF NOT EXISTS action_reservations (
                            idempotency_key TEXT PRIMARY KEY CHECK(length(idempotency_key)=64),
                            owner_id TEXT NOT NULL,
                            device_id TEXT NOT NULL,
                            session_id TEXT NOT NULL,
                            capability_nonce TEXT NOT NULL,
                            protocol_version INTEGER NOT NULL CHECK(protocol_version IN (1,2)),
                            action_id TEXT NOT NULL,
                            arguments_sha256 TEXT NOT NULL CHECK(length(arguments_sha256)=64),
                            issued_at_epoch_ms INTEGER NOT NULL,
                            expires_at_epoch_ms INTEGER NOT NULL,
                            transport_certificate_sha256 TEXT NOT NULL
                                CHECK(length(transport_certificate_sha256)=64),
                            credential_generation INTEGER NOT NULL CHECK(credential_generation>0),
                            consent_public_key_sha256 TEXT NOT NULL
                                CHECK(length(consent_public_key_sha256)=64),
                            state TEXT NOT NULL CHECK(state IN (
                                'RESERVED','DISPATCH_STARTED','COMPLETED',
                                'FAILED_NO_EFFECT','CANCELLED','UNKNOWN_OUTCOME'
                            )),
                            outcome_code TEXT,
                            outcome_sha256 TEXT,
                            created_at_epoch_ms INTEGER NOT NULL,
                            updated_at_epoch_ms INTEGER NOT NULL,
                            UNIQUE(owner_id,device_id,capability_nonce)
                        )
                    """)
                    db.execute(
                        "CREATE INDEX IF NOT EXISTS action_reservations_state "
                        "ON action_reservations(state,created_at_epoch_ms)"
                    )
                    db.execute("PRAGMA user_version=1")
                elif version != _SCHEMA_VERSION:
                    raise ValueError("unsupported reservation schema")
        except (sqlite3.Error, OSError) as error:
            raise ReservationStoreUnavailable("reservation database unavailable") from error

    @staticmethod
    def _record(row: sqlite3.Row | None) -> ActionReservationRecord | None:
        return None if row is None else ActionReservationRecord(**dict(row))

    def reserve(self, request: ActionReservationRequest) -> ReservationDecision:
        """Create one reservation. Duplicates are read-only and never dispatchable."""
        binding = _binding(request)
        if binding is None:
            return ReservationDecision(False, "INVALID_REQUEST", "", None)
        key = derive_idempotency_key(request)
        names = tuple(binding)
        with self._transaction() as db:
            row = db.execute(
                "SELECT * FROM action_reservations WHERE idempotency_key=?",
                (key,),
            ).fetchone()
            if row is None:
                row = db.execute(
                    "SELECT * FROM action_reservations "
                    "WHERE owner_id=? AND device_id=? AND capability_nonce=?",
                    (request.owner_id, request.device_id, request.capability_nonce),
                ).fetchone()

            # Read the clock only after acquiring the SQLite write transaction.
            # Waiting for another writer must not let an expired capability slip in.
            now = self._now()
            if now < request.issued_at_epoch_ms:
                return ReservationDecision(
                    False, "CAPABILITY_NOT_YET_VALID", key,
                    None if row is None else row["state"],
                )
            if now >= request.expires_at_epoch_ms:
                if row is not None and row["state"] == RESERVED:
                    db.execute(
                        "UPDATE action_reservations SET state=?,outcome_code=?,"
                        "outcome_sha256=NULL,updated_at_epoch_ms=? "
                        "WHERE idempotency_key=? AND state=?",
                        (FAILED_NO_EFFECT, "CAPABILITY_EXPIRED", now, row["idempotency_key"], RESERVED),
                    )
                    return ReservationDecision(
                        False, "CAPABILITY_EXPIRED", key, FAILED_NO_EFFECT,
                    )
                return ReservationDecision(
                    False, "CAPABILITY_EXPIRED", key,
                    None if row is None else row["state"],
                )
            if row is not None:
                same = row["idempotency_key"] == key and all(
                    row[name] == binding[name] for name in names
                )
                return ReservationDecision(
                    False, "IDEMPOTENT_REPLAY" if same else "IDEMPOTENCY_CONFLICT",
                    key, row["state"],
                )
            count = db.execute(
                "SELECT COUNT(*) FROM action_reservations"
            ).fetchone()[0]
            if count >= self.max_entries:
                return ReservationDecision(False, "CAPACITY_REACHED", key, None)
            columns = (
                "idempotency_key," + ",".join(names)
                + ",state,outcome_code,outcome_sha256,created_at_epoch_ms,updated_at_epoch_ms"
            )
            values = (
                key, *(binding[name] for name in names),
                RESERVED, None, None, now, now,
            )
            marks = ",".join("?" for _ in values)
            db.execute(
                f"INSERT INTO action_reservations ({columns}) VALUES ({marks})",
                values,
            )
        return ReservationDecision(True, "RESERVED", key, RESERVED, True)

    def claim_dispatch(self, key: str) -> ReservationDecision:
        """Atomically claim RESERVED once; no action is executed by this method."""
        if type(key) is not str or _SHA256.fullmatch(key) is None:
            return ReservationDecision(False, "INVALID_IDEMPOTENCY_KEY", "", None)
        with self._transaction() as db:
            row = db.execute(
                "SELECT state,issued_at_epoch_ms,expires_at_epoch_ms "
                "FROM action_reservations WHERE idempotency_key=?", (key,)
            ).fetchone()
            if row is None:
                return ReservationDecision(False, "RESERVATION_NOT_FOUND", key, None)
            if row["state"] != RESERVED:
                reason = "ALREADY_CLAIMED" if row["state"] == DISPATCH_STARTED else "TERMINAL_STATE"
                return ReservationDecision(False, reason, key, row["state"])

            # Re-read time under the write lock so queueing behind another writer
            # cannot move the claim past the signed capability's validity window.
            now = self._now()
            if now < row["issued_at_epoch_ms"]:
                return ReservationDecision(
                    False, "CAPABILITY_NOT_YET_VALID", key, RESERVED,
                )
            if now >= row["expires_at_epoch_ms"]:
                changed = db.execute(
                    "UPDATE action_reservations SET state=?,outcome_code=?,"
                    "outcome_sha256=NULL,updated_at_epoch_ms=? "
                    "WHERE idempotency_key=? AND state=?",
                    (FAILED_NO_EFFECT, "CAPABILITY_EXPIRED", now, key, RESERVED),
                ).rowcount
                if changed != 1:
                    return ReservationDecision(False, "CLAIM_RACE", key, None)
                return ReservationDecision(
                    False, "CAPABILITY_EXPIRED", key, FAILED_NO_EFFECT,
                )
            changed = db.execute(
                "UPDATE action_reservations SET state=?,updated_at_epoch_ms=? "
                "WHERE idempotency_key=? AND state=?",
                (DISPATCH_STARTED, now, key, RESERVED),
            ).rowcount
            if changed != 1:
                return ReservationDecision(False, "CLAIM_RACE", key, None)
        return ReservationDecision(True, "DISPATCH_CLAIMED", key, DISPATCH_STARTED)

    def _finish_before_dispatch(
        self, key: str, *, state: str, code: str, digest: str | None
    ) -> ReservationDecision:
        if type(key) is not str or _SHA256.fullmatch(key) is None:
            return ReservationDecision(False, "INVALID_IDEMPOTENCY_KEY", "", None)
        now = self._now()
        with self._transaction() as db:
            row = db.execute(
                "SELECT state,outcome_code,outcome_sha256 "
                "FROM action_reservations WHERE idempotency_key=?", (key,)
            ).fetchone()
            if row is None:
                return ReservationDecision(False, "RESERVATION_NOT_FOUND", key, None)
            if row["state"] == state:
                same = row["outcome_code"] == code and row["outcome_sha256"] == digest
                repeated_reason = (
                    "ALREADY_CANCELLED" if state == CANCELLED
                    else "DENIAL_ALREADY_RECORDED"
                )
                return ReservationDecision(
                    same, repeated_reason if same else "OUTCOME_CONFLICT", key, state,
                )
            if row["state"] != RESERVED:
                return ReservationDecision(False, "DISPATCH_ALREADY_STARTED", key, row["state"])
            db.execute(
                "UPDATE action_reservations SET state=?,outcome_code=?,"
                "outcome_sha256=?,updated_at_epoch_ms=? "
                "WHERE idempotency_key=? AND state=?",
                (state, code, digest, now, key, RESERVED),
            )
        return ReservationDecision(True, code, key, state)

    def cancel_before_dispatch(self, key: str) -> ReservationDecision:
        return self._finish_before_dispatch(
            key, state=CANCELLED, code="CANCELLED_BEFORE_DISPATCH", digest=None
        )

    def reject_before_dispatch(
        self, key: str, *, reason_code: str, evidence_sha256: str | None = None
    ) -> ReservationDecision:
        if type(key) is not str or _SHA256.fullmatch(key) is None:
            return ReservationDecision(False, "INVALID_IDEMPOTENCY_KEY", "", None)
        if type(reason_code) is not str or _OUTCOME.fullmatch(reason_code) is None:
            return ReservationDecision(False, "INVALID_OUTCOME_CODE", key, None)
        if evidence_sha256 is not None and (
            type(evidence_sha256) is not str or _SHA256.fullmatch(evidence_sha256) is None
        ):
            return ReservationDecision(False, "INVALID_OUTCOME_DIGEST", key, None)
        return self._finish_before_dispatch(
            key, state=FAILED_NO_EFFECT, code=reason_code, digest=evidence_sha256
        )

    def record_outcome(
        self, key: str, *, state: str, outcome_code: str,
        outcome_sha256: str | None = None,
    ) -> ReservationDecision:
        if type(key) is not str or _SHA256.fullmatch(key) is None:
            return ReservationDecision(False, "INVALID_IDEMPOTENCY_KEY", "", None)
        if type(state) is not str or state not in {
            COMPLETED, FAILED_NO_EFFECT, UNKNOWN_OUTCOME
        }:
            return ReservationDecision(False, "INVALID_OUTCOME_STATE", key, None)
        if type(outcome_code) is not str or _OUTCOME.fullmatch(outcome_code) is None:
            return ReservationDecision(False, "INVALID_OUTCOME_CODE", key, None)
        if outcome_sha256 is not None and (
            type(outcome_sha256) is not str or _SHA256.fullmatch(outcome_sha256) is None
        ):
            return ReservationDecision(False, "INVALID_OUTCOME_DIGEST", key, None)
        now = self._now()
        with self._transaction() as db:
            row = db.execute(
                "SELECT state,outcome_code,outcome_sha256 "
                "FROM action_reservations WHERE idempotency_key=?", (key,)
            ).fetchone()
            if row is None:
                return ReservationDecision(False, "RESERVATION_NOT_FOUND", key, None)
            if row["state"] == state:
                same = (
                    row["outcome_code"] == outcome_code
                    and row["outcome_sha256"] == outcome_sha256
                )
                return ReservationDecision(
                    same, "OUTCOME_ALREADY_RECORDED" if same else "OUTCOME_CONFLICT",
                    key, state,
                )
            if row["state"] != DISPATCH_STARTED:
                return ReservationDecision(False, "INVALID_STATE", key, row["state"])
            db.execute(
                "UPDATE action_reservations SET state=?,outcome_code=?,"
                "outcome_sha256=?,updated_at_epoch_ms=? "
                "WHERE idempotency_key=? AND state=?",
                (state, outcome_code, outcome_sha256, now, key, DISPATCH_STARTED),
            )
        return ReservationDecision(True, "OUTCOME_RECORDED", key, state)

    def get(self, key: str) -> ActionReservationRecord | None:
        if type(key) is not str or _SHA256.fullmatch(key) is None:
            return None
        try:
            with closing(self._connect()) as db:
                row = db.execute(
                    "SELECT * FROM action_reservations WHERE idempotency_key=?", (key,)
                ).fetchone()
                return self._record(row)
        except sqlite3.Error as error:
            raise ReservationStoreUnavailable("reservation read unavailable") from error
