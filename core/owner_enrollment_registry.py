"""SEC-017: signed, durable owner/device credential enrollment registry.

The registry is an offline host-side trust boundary. It accepts only short-lived
Ed25519-signed enrollment statements from one externally pinned authority key.
It implements both AGENT-004C's consent-key lookup and AGENT-004D's transport
certificate lookup over one SQLite row, so the two credentials share an owner,
device, generation and active state.

This module creates no listener, does not enroll from request/model input, and
never grants Android permissions or executes commands.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from core.owner_consent_issuer import EnrolledOwnerDevice
from core.owner_consent_transport import EnrolledTransportCertificate


SCHEMA_NAME = "mrnothing.owner-device-enrollment"
SCHEMA_VERSION = 1  # Signed enrollment-statement protocol version.
DATABASE_SCHEMA_VERSION = 2  # Adds atomic enrollment-aware consent replay state.
MAX_ENROLLMENT_ENVELOPE_BYTES = 4_096
MAX_ENROLLMENT_TTL_MS = 300_000
MAX_EPOCH_MS = (1 << 63) - 1
MAX_DEVICES = 5_000
MAX_HISTORY_ROWS = 8_000
MAX_DATABASE_BYTES = 4 * 1024 * 1024
MAX_CONSENT_REPLAY_ROWS = 10_000
_SQLITE_TIMEOUT_SECONDS = 5.0
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PAYLOAD_KEYS = frozenset({
    "schema", "version", "operation", "authority_key_id", "enrollment_id",
    "owner_id", "device_id", "credential_generation", "issued_at_epoch_ms",
    "expires_at_epoch_ms", "transport_certificate_sha256",
    "consent_public_key_spki_der", "consent_public_key_sha256",
})


class EnrollmentRegistryError(RuntimeError):
    """Persistent enrollment state is unavailable, invalid or rejected."""


class EnrollmentOutcomeUnknown(EnrollmentRegistryError):
    """A COMMIT acknowledgement was lost; reconcile durable state before retrying."""

    reconciliation_required = True

    def __init__(
        self,
        *,
        operation: str,
        owner_id: str,
        device_id: str,
        enrollment_id: str,
        credential_generation: int,
        envelope_sha256: str,
    ) -> None:
        super().__init__(
            "enrollment COMMIT outcome is unknown; reconcile durable history before retrying"
        )
        self.operation = operation
        self.owner_id = owner_id
        self.device_id = device_id
        self.enrollment_id = enrollment_id
        self.credential_generation = credential_generation
        self.envelope_sha256 = envelope_sha256


ENROLLMENT_OUTCOME_APPLIED = "APPLIED"
ENROLLMENT_OUTCOME_NOT_OBSERVED = "NOT_OBSERVED"
ENROLLMENT_OUTCOME_UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class EnrollmentReconciliation:
    """Read-only durable-state observation; it never authorizes automatic retry."""

    status: str
    reason: str
    operation: str
    owner_id: str
    device_id: str
    enrollment_id: str
    credential_generation: int
    envelope_sha256: str
    automatic_retry_permitted: bool = False


class EnrollmentStatementError(ValueError):
    """An enrollment statement failed strict parsing or signature validation."""


class EnrollmentConflict(EnrollmentRegistryError):
    """An enrollment would violate identity, generation or uniqueness rules."""


@dataclass(frozen=True)
class EnrollmentResult:
    operation: str
    owner_id: str
    device_id: str
    credential_generation: int
    active: bool
    envelope_sha256: str


@dataclass(frozen=True)
class EnrollmentHistoryEntry:
    enrollment_id: str
    owner_id: str
    device_id: str
    operation: str
    credential_generation: int
    transport_certificate_sha256: str
    consent_public_key_sha256: str
    envelope_sha256: str
    applied_at_epoch_ms: int


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EnrollmentStatementError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise EnrollmentStatementError("non-finite JSON value")


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("ascii")


def _decode_base64url(value: object, *, expected_length: int | None = None) -> bytes:
    if type(value) is not str or not value or "=" in value:
        raise EnrollmentStatementError("invalid base64url value")
    if re.fullmatch(r"[A-Za-z0-9_-]+", value) is None:
        raise EnrollmentStatementError("invalid base64url alphabet")
    try:
        raw = base64.urlsafe_b64decode(
            value + ("=" * ((4 - len(value) % 4) % 4))
        )
    except (ValueError, base64.binascii.Error) as exc:
        raise EnrollmentStatementError("invalid base64url encoding") from exc
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") != value:
        raise EnrollmentStatementError("non-canonical base64url encoding")
    if expected_length is not None and len(raw) != expected_length:
        raise EnrollmentStatementError("invalid decoded length")
    return raw


def _validate_p256_spki(value: object) -> tuple[bytes, str]:
    raw = _decode_base64url(value)
    if not 1 <= len(raw) <= 512:
        raise EnrollmentStatementError("consent public key size invalid")
    try:
        key = serialization.load_der_public_key(raw)
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        raise EnrollmentStatementError("consent public key is malformed") from exc
    if not isinstance(key, ec.EllipticCurvePublicKey) or key.curve.name != "secp256r1":
        raise EnrollmentStatementError("consent public key must be P-256")
    canonical = key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    if canonical != raw:
        raise EnrollmentStatementError("consent public key DER is not canonical")
    return raw, hashlib.sha256(raw).hexdigest()


def _validate_signed_statement(
    envelope: bytes,
    *,
    authority_key: ed25519.Ed25519PublicKey,
    authority_key_id: str,
    now_epoch_ms: int,
) -> dict[str, Any]:
    if type(envelope) is not bytes or not 1 <= len(envelope) <= MAX_ENROLLMENT_ENVELOPE_BYTES:
        raise EnrollmentStatementError("enrollment envelope size/type invalid")
    if type(now_epoch_ms) is not int or not 0 <= now_epoch_ms <= MAX_EPOCH_MS:
        raise EnrollmentStatementError("invalid trusted clock")
    try:
        document = json.loads(
            envelope.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise EnrollmentStatementError("invalid enrollment JSON") from exc
    if type(document) is not dict or set(document) != {"payload", "signature"}:
        raise EnrollmentStatementError("invalid enrollment envelope fields")
    payload = document["payload"]
    if type(payload) is not dict or set(payload) != _PAYLOAD_KEYS:
        raise EnrollmentStatementError("invalid enrollment payload fields")
    if payload["schema"] != SCHEMA_NAME or type(payload["schema"]) is not str:
        raise EnrollmentStatementError("unsupported enrollment schema")
    if type(payload["version"]) is not int or payload["version"] != SCHEMA_VERSION:
        raise EnrollmentStatementError("unsupported enrollment schema version")
    if type(payload["operation"]) is not str or payload["operation"] not in {
        "enroll", "rotate", "revoke"
    }:
        raise EnrollmentStatementError("unsupported enrollment operation")
    for name in ("authority_key_id", "enrollment_id", "owner_id", "device_id"):
        value = payload[name]
        if type(value) is not str or _IDENTIFIER_RE.fullmatch(value) is None:
            raise EnrollmentStatementError(f"invalid {name}")
    if payload["authority_key_id"] != authority_key_id:
        raise EnrollmentStatementError("untrusted enrollment authority key id")
    generation = payload["credential_generation"]
    issued = payload["issued_at_epoch_ms"]
    expires = payload["expires_at_epoch_ms"]
    if type(generation) is not int or not 1 <= generation <= MAX_EPOCH_MS:
        raise EnrollmentStatementError("invalid credential generation")
    if type(issued) is not int or type(expires) is not int:
        raise EnrollmentStatementError("invalid enrollment timestamps")
    if not (0 <= issued < expires <= MAX_EPOCH_MS):
        raise EnrollmentStatementError("enrollment timestamp outside signed 64-bit range")
    if expires - issued > MAX_ENROLLMENT_TTL_MS:
        raise EnrollmentStatementError("enrollment statement lifetime exceeds five minutes")
    if not issued <= now_epoch_ms < expires:
        raise EnrollmentStatementError("enrollment statement is not currently valid")
    fingerprint = payload["transport_certificate_sha256"]
    key_digest = payload["consent_public_key_sha256"]
    if type(fingerprint) is not str or _SHA256_RE.fullmatch(fingerprint) is None:
        raise EnrollmentStatementError("invalid transport certificate fingerprint")
    if type(key_digest) is not str or _SHA256_RE.fullmatch(key_digest) is None:
        raise EnrollmentStatementError("invalid consent public-key digest")

    spki_text = payload["consent_public_key_spki_der"]
    if payload["operation"] == "revoke":
        if spki_text is not None:
            raise EnrollmentStatementError("revocation must not introduce a public key")
        spki = None
    else:
        spki, actual_digest = _validate_p256_spki(spki_text)
        if actual_digest != key_digest:
            raise EnrollmentStatementError("consent public-key digest mismatch")

    signature = _decode_base64url(document["signature"], expected_length=64)
    try:
        authority_key.verify(signature, _canonical_payload(payload))
    except InvalidSignature as exc:
        raise EnrollmentStatementError("invalid enrollment authority signature") from exc
    return {
        "payload": payload,
        "spki": spki,
        "fingerprint": fingerprint,
        "key_digest": key_digest,
        "envelope_sha256": hashlib.sha256(envelope).hexdigest(),
    }


class SQLiteOwnerEnrollmentRegistry:
    """One durable record implements both AGENT-004C and AGENT-004D registries.

    The Ed25519 authority public key is an external pin supplied by trusted
    configuration. The matching private key must remain offline. First creation
    is explicit; missing/corrupt databases are never silently recreated.
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        authority_public_key_spki_der: bytes,
        authority_key_id: str,
        timeout_seconds: float = _SQLITE_TIMEOUT_SECONDS,
    ) -> None:
        if not isinstance(path, (str, os.PathLike)) or not os.fspath(path):
            raise EnrollmentRegistryError("persistent database path is required")
        if type(authority_key_id) is not str or _IDENTIFIER_RE.fullmatch(authority_key_id) is None:
            raise EnrollmentRegistryError("invalid authority key id")
        if type(timeout_seconds) not in (int, float) or not 0.05 <= timeout_seconds <= 30:
            raise EnrollmentRegistryError("invalid SQLite timeout")
        if type(authority_public_key_spki_der) is not bytes or not 1 <= len(authority_public_key_spki_der) <= 256:
            raise EnrollmentRegistryError("invalid authority public key")
        try:
            authority = serialization.load_der_public_key(authority_public_key_spki_der)
        except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
            raise EnrollmentRegistryError("invalid authority public key") from exc
        if not isinstance(authority, ed25519.Ed25519PublicKey):
            raise EnrollmentRegistryError("enrollment authority must use Ed25519")
        canonical = authority.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if canonical != authority_public_key_spki_der:
            raise EnrollmentRegistryError("authority public key DER is not canonical")
        self.path = Path(path).absolute()
        self.authority_key_id = authority_key_id
        self._authority_key = authority
        self.timeout_seconds = float(timeout_seconds)

    def initialize(self, *, explicit_first_install: bool = False) -> None:
        """Create the schema only during explicit trusted first-time provisioning."""
        parent = self.path.parent
        if parent.is_symlink() or not parent.is_dir():
            raise EnrollmentRegistryError("database parent must be an existing real directory")
        if self.path.exists() or self.path.is_symlink():
            db = self._connect()
            try:
                self._validate_schema(db)
                return
            finally:
                db.close()
        if explicit_first_install is not True:
            raise EnrollmentRegistryError("explicit first-install authorization required")
        flags = os.O_CREAT | os.O_EXCL | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(self.path, flags, 0o600)
            os.close(fd)
        except FileExistsError:
            db = self._connect()
            try:
                self._validate_schema(db)
                return
            finally:
                db.close()
        except OSError as exc:
            raise EnrollmentRegistryError("secure database creation failed") from exc

        db = None
        try:
            db = self._connect()
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            if db.execute("PRAGMA user_version").fetchone()[0] != 0:
                raise EnrollmentRegistryError("new database has unexpected schema version")
            tables = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            if tables:
                raise EnrollmentRegistryError("new database is not empty")
            db.execute("""
                CREATE TABLE owner_device (
                    owner_id TEXT NOT NULL,
                    device_id TEXT NOT NULL PRIMARY KEY,
                    transport_certificate_sha256 TEXT NOT NULL UNIQUE
                        CHECK(length(transport_certificate_sha256) = 64),
                    consent_public_key_spki_der BLOB NOT NULL
                        CHECK(typeof(consent_public_key_spki_der) = 'blob'
                              AND length(consent_public_key_spki_der) BETWEEN 1 AND 512),
                    consent_public_key_sha256 TEXT NOT NULL UNIQUE
                        CHECK(length(consent_public_key_sha256) = 64),
                    credential_generation INTEGER NOT NULL
                        CHECK(typeof(credential_generation) = 'integer'
                              AND credential_generation >= 1),
                    active INTEGER NOT NULL CHECK(active IN (0, 1)),
                    enrollment_id TEXT NOT NULL UNIQUE,
                    updated_at_epoch_ms INTEGER NOT NULL
                        CHECK(typeof(updated_at_epoch_ms) = 'integer'
                              AND updated_at_epoch_ms >= 0)
                )
            """)
            db.execute("""
                CREATE TABLE owner_device_history (
                    enrollment_id TEXT NOT NULL PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    operation TEXT NOT NULL CHECK(operation IN ('enroll', 'rotate', 'revoke')),
                    credential_generation INTEGER NOT NULL
                        CHECK(typeof(credential_generation) = 'integer'
                              AND credential_generation >= 1),
                    transport_certificate_sha256 TEXT NOT NULL,
                    consent_public_key_sha256 TEXT NOT NULL,
                    envelope_sha256 TEXT NOT NULL CHECK(length(envelope_sha256) = 64),
                    applied_at_epoch_ms INTEGER NOT NULL
                        CHECK(typeof(applied_at_epoch_ms) = 'integer'
                              AND applied_at_epoch_ms >= 0),
                    UNIQUE(device_id, credential_generation)
                )
            """)
            db.execute("""
                CREATE TABLE owner_consent_replay (
                    device_id TEXT NOT NULL,
                    nonce TEXT NOT NULL
                        CHECK(length(nonce) = 32 AND nonce NOT GLOB '*[^0-9a-f]*'),
                    consumed_at_epoch_ms INTEGER NOT NULL
                        CHECK(typeof(consumed_at_epoch_ms) = 'integer'
                              AND consumed_at_epoch_ms >= 0),
                    PRIMARY KEY(device_id, nonce),
                    FOREIGN KEY(device_id) REFERENCES owner_device(device_id)
                )
            """)
            db.execute("CREATE INDEX owner_device_active ON owner_device(active, device_id)")
            db.execute("CREATE INDEX owner_history_device ON owner_device_history(device_id, credential_generation)")
            db.execute("CREATE INDEX owner_consent_replay_age ON owner_consent_replay(consumed_at_epoch_ms)")
            db.execute("PRAGMA user_version=2")
            db.execute("COMMIT")
            os.chmod(self.path, 0o600)
            self._check_file()
        except Exception as exc:
            if db is not None and db.in_transaction:
                db.execute("ROLLBACK")
            if isinstance(exc, EnrollmentRegistryError):
                raise
            raise EnrollmentRegistryError("database schema initialization failed") from exc
        finally:
            if db is not None:
                db.close()


    def migrate_v1_to_v2(self, *, explicit_migration: bool = False) -> bool:
        """Explicitly add atomic consent replay state to an existing v1 registry.

        This migration is additive and preserves all enrollment/history rows.
        It is never performed implicitly during ordinary lookup or startup.
        Returns True when a migration occurred and False when already at v2.
        """
        if explicit_migration is not True:
            raise EnrollmentRegistryError("explicit v1-to-v2 migration authorization required")
        db = self._connect()
        try:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            tables = {
                row[0] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            if version == DATABASE_SCHEMA_VERSION and tables == {
                "owner_device", "owner_device_history", "owner_consent_replay"
            }:
                self._validate_schema(db)
                return False
            if version != 1 or tables != {"owner_device", "owner_device_history"}:
                raise EnrollmentRegistryError("database is not a recognized v1 enrollment registry")
            check = db.execute("PRAGMA quick_check(1)").fetchone()
            if check is None or check[0] != "ok":
                raise EnrollmentRegistryError("v1 enrollment database integrity check failed")
            db.execute("BEGIN IMMEDIATE")
            if db.execute("PRAGMA user_version").fetchone()[0] != 1:
                raise EnrollmentRegistryError("enrollment schema changed during migration")
            current_tables = {
                row[0] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            if current_tables != {"owner_device", "owner_device_history"}:
                raise EnrollmentRegistryError("v1 enrollment schema changed during migration")
            db.execute("""
                CREATE TABLE owner_consent_replay (
                    device_id TEXT NOT NULL,
                    nonce TEXT NOT NULL
                        CHECK(length(nonce) = 32 AND nonce NOT GLOB '*[^0-9a-f]*'),
                    consumed_at_epoch_ms INTEGER NOT NULL
                        CHECK(typeof(consumed_at_epoch_ms) = 'integer'
                              AND consumed_at_epoch_ms >= 0),
                    PRIMARY KEY(device_id, nonce),
                    FOREIGN KEY(device_id) REFERENCES owner_device(device_id)
                )
            """)
            db.execute(
                "CREATE INDEX owner_consent_replay_age "
                "ON owner_consent_replay(consumed_at_epoch_ms)"
            )
            db.execute("PRAGMA user_version=2")
            db.execute("COMMIT")
            self._validate_schema(db)
            return True
        except EnrollmentRegistryError:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
        except sqlite3.Error as exc:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise EnrollmentRegistryError("v1-to-v2 enrollment migration failed") from exc
        finally:
            db.close()

    def _check_file(self) -> None:
        try:
            info = self.path.lstat()
        except OSError as exc:
            raise EnrollmentRegistryError("enrollment database is missing") from exc
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise EnrollmentRegistryError("enrollment database must be a regular non-symlink file")
        if os.name == "posix" and stat.S_IMODE(info.st_mode) & 0o077:
            raise EnrollmentRegistryError("enrollment database permissions are too broad")
        if info.st_size > MAX_DATABASE_BYTES:
            raise EnrollmentRegistryError("enrollment database exceeds size limit")

    def _connect(self) -> sqlite3.Connection:
        self._check_file()
        uri = self.path.as_uri() + "?mode=rw"
        try:
            db = sqlite3.connect(
                uri, uri=True, timeout=self.timeout_seconds, isolation_level=None
            )
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("PRAGMA synchronous=FULL")
            return db
        except sqlite3.Error as exc:
            raise EnrollmentRegistryError("cannot open enrollment database") from exc

    @staticmethod
    def _validate_schema(db: sqlite3.Connection) -> None:
        try:
            if db.execute("PRAGMA user_version").fetchone()[0] != DATABASE_SCHEMA_VERSION:
                raise EnrollmentRegistryError("unsupported enrollment database schema")
            tables = {
                row[0] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            if tables != {"owner_device", "owner_device_history", "owner_consent_replay"}:
                raise EnrollmentRegistryError("unexpected enrollment database tables")
            result = db.execute("PRAGMA quick_check(1)").fetchone()
            if result is None or result[0] != "ok":
                raise EnrollmentRegistryError("enrollment database integrity check failed")
        except sqlite3.Error as exc:
            raise EnrollmentRegistryError("enrollment database schema check failed") from exc

    def apply_signed_enrollment(
        self, envelope: bytes, *, now_epoch_ms: int
    ) -> EnrollmentResult:
        """Atomically apply an offline-authority-signed enroll/rotate/revoke statement."""
        parsed = _validate_signed_statement(
            envelope,
            authority_key=self._authority_key,
            authority_key_id=self.authority_key_id,
            now_epoch_ms=now_epoch_ms,
        )
        payload = parsed["payload"]
        operation = payload["operation"]
        owner_id = payload["owner_id"]
        device_id = payload["device_id"]
        generation = payload["credential_generation"]
        fingerprint = parsed["fingerprint"]
        key_digest = parsed["key_digest"]
        spki = parsed["spki"]
        db = self._connect()
        try:
            self._validate_schema(db)
            db.execute("BEGIN IMMEDIATE")
            current = db.execute(
                "SELECT owner_id, transport_certificate_sha256, consent_public_key_sha256, "
                "credential_generation, active FROM owner_device WHERE device_id=?",
                (device_id,),
            ).fetchone()
            if operation == "enroll":
                if current is not None or generation != 1:
                    raise EnrollmentConflict("initial enrollment requires a new device at generation 1")
                count = db.execute("SELECT COUNT(*) FROM owner_device").fetchone()[0]
                if count >= MAX_DEVICES:
                    raise EnrollmentConflict("enrollment registry capacity reached")
            elif operation == "rotate":
                if current is None or current[0] != owner_id:
                    raise EnrollmentConflict("rotation requires the existing owner/device")
                if generation != current[3] + 1:
                    raise EnrollmentConflict("credential generation must advance exactly once")
                if fingerprint == current[1] or key_digest == current[2]:
                    raise EnrollmentConflict("rotation must replace both bound credentials")
            elif operation == "revoke":
                if current is None or current[0] != owner_id or current[4] != 1:
                    raise EnrollmentConflict("revocation requires an active matching owner/device")
                if generation != current[3] + 1:
                    raise EnrollmentConflict("revocation generation must advance exactly once")
                if fingerprint != current[1] or key_digest != current[2] or spki is not None:
                    raise EnrollmentConflict("revocation must identify the current credential pair")
            history_count = db.execute(
                "SELECT COUNT(*) FROM owner_device_history"
            ).fetchone()[0]
            if history_count >= MAX_HISTORY_ROWS:
                raise EnrollmentConflict("enrollment history capacity reached")
            duplicate_id = db.execute(
                "SELECT 1 FROM owner_device_history WHERE enrollment_id=?",
                (payload["enrollment_id"],),
            ).fetchone()
            if duplicate_id:
                raise EnrollmentConflict("enrollment statement has already been applied")
            if operation != "revoke":
                duplicate = db.execute(
                    "SELECT device_id FROM owner_device WHERE "
                    "(transport_certificate_sha256=? OR consent_public_key_sha256=?) "
                    "AND device_id<>?",
                    (fingerprint, key_digest, device_id),
                ).fetchone()
                if duplicate:
                    raise EnrollmentConflict("credential is already bound to another device")
                if current is None:
                    db.execute("""
                        INSERT INTO owner_device (
                            owner_id, device_id, transport_certificate_sha256,
                            consent_public_key_spki_der, consent_public_key_sha256,
                            credential_generation, active, enrollment_id, updated_at_epoch_ms
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """, (
                        owner_id, device_id, fingerprint, spki, key_digest,
                        generation, payload["enrollment_id"], now_epoch_ms,
                    ))
                else:
                    db.execute("""
                        UPDATE owner_device SET
                            transport_certificate_sha256=?,
                            consent_public_key_spki_der=?,
                            consent_public_key_sha256=?,
                            credential_generation=?, active=1,
                            enrollment_id=?, updated_at_epoch_ms=?
                        WHERE device_id=? AND owner_id=?
                    """, (
                        fingerprint, spki, key_digest, generation,
                        payload["enrollment_id"], now_epoch_ms, device_id, owner_id,
                    ))
            else:
                db.execute("""
                    UPDATE owner_device SET active=0, credential_generation=?,
                        enrollment_id=?, updated_at_epoch_ms=?
                    WHERE device_id=? AND owner_id=? AND active=1
                """, (
                    generation, payload["enrollment_id"], now_epoch_ms,
                    device_id, owner_id,
                ))
            db.execute("""
                INSERT INTO owner_device_history (
                    enrollment_id, owner_id, device_id, operation,
                    credential_generation, transport_certificate_sha256,
                    consent_public_key_sha256, envelope_sha256, applied_at_epoch_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payload["enrollment_id"], owner_id, device_id, operation,
                generation, fingerprint, key_digest, parsed["envelope_sha256"],
                now_epoch_ms,
            ))
            try:
                db.execute("COMMIT")
            except Exception as exc:
                unknown = EnrollmentOutcomeUnknown(
                    operation=operation,
                    owner_id=owner_id,
                    device_id=device_id,
                    enrollment_id=payload["enrollment_id"],
                    credential_generation=generation,
                    envelope_sha256=parsed["envelope_sha256"],
                )
                if db.in_transaction:
                    try:
                        db.execute("ROLLBACK")
                    except Exception as rollback_exc:
                        raise unknown from rollback_exc
                    if isinstance(exc, sqlite3.IntegrityError):
                        raise EnrollmentConflict(
                            "enrollment uniqueness or generation constraint failed"
                        ) from exc
                    raise EnrollmentRegistryError(
                        "enrollment COMMIT failed and the transaction was rolled back"
                    ) from exc
                raise unknown from exc
            return EnrollmentResult(
                operation, owner_id, device_id, generation,
                operation != "revoke", parsed["envelope_sha256"],
            )
        except EnrollmentOutcomeUnknown:
            raise
        except EnrollmentRegistryError:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
        except sqlite3.IntegrityError as exc:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise EnrollmentConflict("enrollment uniqueness or generation constraint failed") from exc
        except sqlite3.Error as exc:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise EnrollmentRegistryError("enrollment transaction failed") from exc
        finally:
            db.close()

    def reconcile_outcome_unknown(
        self, outcome: EnrollmentOutcomeUnknown
    ) -> EnrollmentReconciliation:
        """Reconcile one ambiguous commit from a validated read-only DB snapshot.

        APPLIED means the exact signed statement is present in durable history
        and the current owner/device row agrees with the latest history entry.
        NOT_OBSERVED means the exact history row is absent and the prior state
        is still coherent. Neither result authorizes an automatic retry.
        Any mismatch or storage/integrity failure is UNRESOLVED.
        """
        if not isinstance(outcome, EnrollmentOutcomeUnknown):
            raise TypeError("EnrollmentOutcomeUnknown is required")

        operation = outcome.operation
        owner_id = outcome.owner_id
        device_id = outcome.device_id
        enrollment_id = outcome.enrollment_id
        generation = outcome.credential_generation
        envelope_sha256 = outcome.envelope_sha256
        if (
            type(operation) is not str or operation not in {"enroll", "rotate", "revoke"}
            or type(owner_id) is not str or _IDENTIFIER_RE.fullmatch(owner_id) is None
            or type(device_id) is not str or _IDENTIFIER_RE.fullmatch(device_id) is None
            or type(enrollment_id) is not str
            or _IDENTIFIER_RE.fullmatch(enrollment_id) is None
            or type(generation) is not int or not 1 <= generation <= MAX_EPOCH_MS
            or type(envelope_sha256) is not str
            or _SHA256_RE.fullmatch(envelope_sha256) is None
        ):
            raise ValueError("invalid enrollment outcome metadata")

        def result(status: str, reason: str) -> EnrollmentReconciliation:
            return EnrollmentReconciliation(
                status=status,
                reason=reason,
                operation=operation,
                owner_id=owner_id,
                device_id=device_id,
                enrollment_id=enrollment_id,
                credential_generation=generation,
                envelope_sha256=envelope_sha256,
                automatic_retry_permitted=False,
            )

        db = None
        try:
            db = self._connect()
            db.execute("PRAGMA query_only=ON")
            db.execute("BEGIN")
            self._validate_schema(db)
            history = db.execute(
                "SELECT owner_id, device_id, operation, credential_generation, "
                "envelope_sha256 FROM owner_device_history WHERE enrollment_id=?",
                (enrollment_id,),
            ).fetchone()
            current = db.execute(
                "SELECT owner_id, device_id, transport_certificate_sha256, "
                "consent_public_key_sha256, credential_generation, active, enrollment_id "
                "FROM owner_device WHERE device_id=?",
                (device_id,),
            ).fetchone()
            latest = db.execute(
                "SELECT enrollment_id, owner_id, device_id, operation, "
                "credential_generation, transport_certificate_sha256, "
                "consent_public_key_sha256 FROM owner_device_history "
                "WHERE device_id=? ORDER BY credential_generation DESC LIMIT 1",
                (device_id,),
            ).fetchone()
            latest_count = db.execute(
                "SELECT COUNT(*) FROM owner_device_history "
                "WHERE device_id=? AND credential_generation=("
                "SELECT MAX(credential_generation) FROM owner_device_history WHERE device_id=?"
                ")",
                (device_id, device_id),
            ).fetchone()[0]

            latest_matches_current = (
                current is not None
                and latest is not None
                and latest_count == 1
                and current[0] == latest[1]
                and current[1] == latest[2]
                and current[2] == latest[5]
                and current[3] == latest[6]
                and current[4] == latest[4]
                and current[5] == (0 if latest[3] == "revoke" else 1)
                and current[6] == latest[0]
            )

            if history is not None:
                exact_history = (
                    history[0] == owner_id
                    and history[1] == device_id
                    and history[2] == operation
                    and history[3] == generation
                    and history[4] == envelope_sha256
                )
                if not exact_history:
                    status, reason = (
                        ENROLLMENT_OUTCOME_UNRESOLVED,
                        "HISTORY_METADATA_MISMATCH",
                    )
                elif (
                    not latest_matches_current
                    or current[0] != owner_id
                    or current[4] < generation
                ):
                    status, reason = (
                        ENROLLMENT_OUTCOME_UNRESOLVED,
                        "CURRENT_STATE_MISMATCH",
                    )
                else:
                    status, reason = (
                        ENROLLMENT_OUTCOME_APPLIED,
                        "MATCHING_HISTORY_AND_CURRENT_STATE",
                    )
            elif operation == "enroll" and current is None and latest is None:
                status, reason = (
                    ENROLLMENT_OUTCOME_NOT_OBSERVED,
                    "NO_HISTORY_AND_NO_DEVICE_ROW",
                )
            elif (
                operation in {"rotate", "revoke"}
                and latest_matches_current
                and current[0] == owner_id
                and current[4] == generation - 1
                and current[5] == 1
            ):
                status, reason = (
                    ENROLLMENT_OUTCOME_NOT_OBSERVED,
                    "NO_HISTORY_AND_PRIOR_STATE_MATCH",
                )
            else:
                status, reason = (
                    ENROLLMENT_OUTCOME_UNRESOLVED,
                    "NO_MATCHING_HISTORY_OR_COHERENT_PRIOR_STATE",
                )

            db.execute("COMMIT")
            return result(status, reason)
        except (EnrollmentRegistryError, sqlite3.Error, OSError):
            if db is not None and db.in_transaction:
                try:
                    db.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
            return result(
                ENROLLMENT_OUTCOME_UNRESOLVED,
                "DATABASE_UNAVAILABLE_OR_INVALID",
            )
        finally:
            if db is not None:
                try:
                    db.close()
                except sqlite3.Error:
                    pass

    def lookup_active_device(self, device_id: str) -> EnrolledOwnerDevice | None:
        if type(device_id) is not str or _IDENTIFIER_RE.fullmatch(device_id) is None:
            return None
        db = self._connect()
        try:
            self._validate_schema(db)
            row = db.execute("""
                SELECT owner_id, device_id, consent_public_key_spki_der,
                       transport_certificate_sha256, credential_generation
                FROM owner_device WHERE device_id=? AND active=1
            """, (device_id,)).fetchone()
            if row is None:
                return None
            return EnrolledOwnerDevice(
                owner_id=row[0], device_id=row[1],
                public_key_spki_der=bytes(row[2]), active=True,
                transport_certificate_sha256=row[3],
                credential_generation=row[4],
            )
        except sqlite3.Error as exc:
            raise EnrollmentRegistryError("consent-key lookup failed") from exc
        finally:
            db.close()

    def lookup_active_certificate(
        self, certificate_sha256: str
    ) -> EnrolledTransportCertificate | None:
        if type(certificate_sha256) is not str or _SHA256_RE.fullmatch(certificate_sha256) is None:
            return None
        db = self._connect()
        try:
            self._validate_schema(db)
            row = db.execute("""
                SELECT owner_id, device_id, transport_certificate_sha256,
                       credential_generation
                FROM owner_device
                WHERE transport_certificate_sha256=? AND active=1
            """, (certificate_sha256,)).fetchone()
            if row is None:
                return None
            return EnrolledTransportCertificate(
                owner_id=row[0], device_id=row[1],
                certificate_sha256=row[2], active=True,
                credential_generation=row[3],
            )
        except sqlite3.Error as exc:
            raise EnrollmentRegistryError("transport-certificate lookup failed") from exc
        finally:
            db.close()


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
        """Atomically revalidate the paired enrollment and reserve one consent nonce.

        Enrollment rotation/revocation and this operation serialize on the same
        SQLite writer lock. A successful result is ordered before any later
        rotation/revocation commit; a rotation/revocation committed first is
        observed and rejected. This method never executes an action.
        """
        if (
            type(owner_id) is not str or _IDENTIFIER_RE.fullmatch(owner_id) is None
            or type(device_id) is not str or _IDENTIFIER_RE.fullmatch(device_id) is None
            or type(nonce) is not str or re.fullmatch(r"[0-9a-f]{32}", nonce) is None
            or type(transport_certificate_sha256) is not str
            or _SHA256_RE.fullmatch(transport_certificate_sha256) is None
            or type(credential_generation) is not int
            or not 1 <= credential_generation <= MAX_EPOCH_MS
            or type(now_epoch_ms) is not int
            or not 0 <= now_epoch_ms <= MAX_EPOCH_MS
            or type(consent_public_key_spki_der) is not bytes
            or not 1 <= len(consent_public_key_spki_der) <= 512
        ):
            return "INVALID_ADMISSION_CONTEXT"
        try:
            public_key = serialization.load_der_public_key(consent_public_key_spki_der)
        except (ValueError, TypeError, UnsupportedAlgorithm):
            return "INVALID_ADMISSION_CONTEXT"
        if not isinstance(public_key, ec.EllipticCurvePublicKey) or public_key.curve.name != "secp256r1":
            return "INVALID_ADMISSION_CONTEXT"
        canonical_key = public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if canonical_key != consent_public_key_spki_der:
            return "INVALID_ADMISSION_CONTEXT"

        db = self._connect()
        try:
            self._validate_schema(db)
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("""
                SELECT owner_id, consent_public_key_spki_der,
                       transport_certificate_sha256, credential_generation, active
                FROM owner_device WHERE device_id=?
            """, (device_id,)).fetchone()
            if row is None or row[4] != 1:
                db.execute("ROLLBACK")
                return "ENROLLMENT_NOT_ACTIVE"
            if row[0] != owner_id:
                db.execute("ROLLBACK")
                return "ENROLLMENT_IDENTITY_MISMATCH"
            if (
                row[2] != transport_certificate_sha256
                or row[3] != credential_generation
            ):
                db.execute("ROLLBACK")
                return "ENROLLMENT_CREDENTIAL_MISMATCH"
            if type(row[1]) is not bytes or not hmac.compare_digest(
                bytes(row[1]), consent_public_key_spki_der
            ):
                db.execute("ROLLBACK")
                return "ENROLLMENT_KEY_MISMATCH"

            # Never evict replay records using wall-clock time. A forward clock
            # jump followed by rollback could otherwise make a still-valid
            # capability reusable. Capacity exhaustion fails closed.
            if db.execute(
                "SELECT 1 FROM owner_consent_replay WHERE device_id=? AND nonce=?",
                (device_id, nonce),
            ).fetchone():
                db.execute("ROLLBACK")
                return "REPLAY_OR_CAPACITY"
            count = db.execute("SELECT COUNT(*) FROM owner_consent_replay").fetchone()[0]
            if count >= MAX_CONSENT_REPLAY_ROWS:
                db.execute("ROLLBACK")
                return "REPLAY_OR_CAPACITY"
            db.execute(
                "INSERT INTO owner_consent_replay(device_id, nonce, consumed_at_epoch_ms) "
                "VALUES (?, ?, ?)",
                (device_id, nonce, now_epoch_ms),
            )
            db.execute("COMMIT")
            return "ADMITTED"
        except EnrollmentRegistryError:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
        except sqlite3.IntegrityError:
            if db.in_transaction:
                db.execute("ROLLBACK")
            return "REPLAY_OR_CAPACITY"
        except sqlite3.Error as exc:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise EnrollmentRegistryError("atomic consent admission failed") from exc
        finally:
            db.close()

    @contextmanager
    def hold_active_enrollment_for_dispatch(
        self,
        *,
        owner_id: str,
        device_id: str,
        transport_certificate_sha256: str,
        credential_generation: int,
        consent_public_key_sha256: str,
    ) -> Iterator[str]:
        """Hold the enrollment writer lock across a separate ledger claim.

        Every signed rotation/revocation uses BEGIN IMMEDIATE on this same
        database. While this context is held, no new enrollment generation
        can commit. The caller must commit DISPATCH_STARTED in its separate
        reservation database before leaving the context. This is a local
        single-host lock-coupling guarantee, not a distributed transaction.
        """
        if (
            type(owner_id) is not str or _IDENTIFIER_RE.fullmatch(owner_id) is None
            or type(device_id) is not str or _IDENTIFIER_RE.fullmatch(device_id) is None
            or type(transport_certificate_sha256) is not str
            or _SHA256_RE.fullmatch(transport_certificate_sha256) is None
            or type(credential_generation) is not int
            or not 1 <= credential_generation <= MAX_EPOCH_MS
            or type(consent_public_key_sha256) is not str
            or _SHA256_RE.fullmatch(consent_public_key_sha256) is None
        ):
            yield "INVALID_ADMISSION_CONTEXT"
            return

        db = None
        try:
            db = self._connect()
            # Acquire the writer lock before reading current enrollment. The
            # same lock serializes apply_signed_enrollment rotation/revocation.
            db.execute("BEGIN IMMEDIATE")
            self._validate_schema(db)
            row = db.execute(
                "SELECT owner_id, transport_certificate_sha256, "
                "consent_public_key_sha256, credential_generation, active "
                "FROM owner_device WHERE device_id=?",
                (device_id,),
            ).fetchone()
            if row is None:
                reason = "DEVICE_NOT_ENROLLED"
            elif row[4] != 1:
                reason = "DEVICE_NOT_ACTIVE"
            elif row[0] != owner_id:
                reason = "OWNER_DEVICE_MISMATCH"
            elif (
                row[1] != transport_certificate_sha256
                or row[3] != credential_generation
            ):
                reason = "ENROLLMENT_CREDENTIAL_MISMATCH"
            elif row[2] != consent_public_key_sha256:
                reason = "ENROLLMENT_KEY_MISMATCH"
            else:
                reason = "ENROLLMENT_ACTIVE"

            try:
                yield reason
                db.execute("COMMIT")
            except BaseException:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise
        except EnrollmentRegistryError:
            if db is not None and db.in_transaction:
                db.execute("ROLLBACK")
            raise
        except sqlite3.Error as exc:
            if db is not None and db.in_transaction:
                db.execute("ROLLBACK")
            raise EnrollmentRegistryError(
                "dispatch enrollment lock failed"
            ) from exc
        finally:
            if db is not None:
                db.close()

    def history(self, device_id: str) -> tuple[EnrollmentHistoryEntry, ...]:
        if type(device_id) is not str or _IDENTIFIER_RE.fullmatch(device_id) is None:
            raise ValueError("invalid device id")
        db = self._connect()
        try:
            self._validate_schema(db)
            rows = db.execute("""
                SELECT enrollment_id, owner_id, device_id, operation,
                       credential_generation, transport_certificate_sha256,
                       consent_public_key_sha256, envelope_sha256, applied_at_epoch_ms
                FROM owner_device_history WHERE device_id=?
                ORDER BY credential_generation
            """, (device_id,)).fetchall()
            return tuple(EnrollmentHistoryEntry(*row) for row in rows)
        except sqlite3.Error as exc:
            raise EnrollmentRegistryError("enrollment history lookup failed") from exc
        finally:
            db.close()
