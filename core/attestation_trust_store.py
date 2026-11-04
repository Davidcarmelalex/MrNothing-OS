"""Crash-safe, process-concurrent anti-rollback state for SEC-016 manifests.

The signed manifest bytes and monotonic version are committed in one SQLite
transaction. This protects against replay races and process crashes. It is not
a hardware-backed monotonic counter and cannot detect restoration of an older
copy of the entire app-private database.
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from core.attestation_trust_manifest import MAX_MANIFEST_BYTES, ManifestError
from core.attestation_trust_verifier import (
    AuthenticatedTrustManifest,
    ManifestVerificationError,
    verify_trust_manifest,
)


_SCHEMA_VERSION = 1
_TABLE = "trust_bundle_state"
_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_INITIAL_TIME = "1970-01-01T00:00:00Z"
_MAX_DATABASE_BYTES = 1_048_576


class TrustStoreError(RuntimeError):
    """Persistent trust state is missing, corrupt, busy, or rejects an update."""


@dataclass(frozen=True)
class TrustBundleState:
    bundle_version: int
    manifest_sha256: str
    manifest_bytes: bytes
    updated_at: str


@dataclass(frozen=True)
class CommittedTrustBundle:
    """A signature-authenticated manifest whose bytes/version were durably stored.

    This is not a PKIX/device-attestation result and does not authorize actions.
    """

    authenticated_manifest: AuthenticatedTrustManifest
    state: TrustBundleState


class SQLiteTrustVersionStore:
    """Private SQLite ledger with atomic verify-and-advance semantics.

    Call initialize() during trusted provisioning. Normal reads and updates
    never recreate a missing database. Place the file in an app-private
    directory. POSIX files must be owner-only (mode 0600); symlinks are refused.
    """

    def __init__(self, path: str | os.PathLike[str], *, timeout_seconds: float = 5.0):
        if not isinstance(path, (str, os.PathLike)):
            raise TrustStoreError("database path is required")
        raw_path = os.fspath(path)
        if not raw_path or raw_path == ":memory:":
            raise TrustStoreError("a persistent database file path is required")
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
            raise TrustStoreError("invalid SQLite timeout")
        if not 0.05 <= float(timeout_seconds) <= 30.0:
            raise TrustStoreError("SQLite timeout must be between 0.05 and 30 seconds")
        self.path = Path(raw_path)
        self.timeout_seconds = float(timeout_seconds)

    def initialize(self) -> TrustBundleState:
        """Create a new empty ledger without overwriting an existing file."""
        if self.path.exists() or self.path.is_symlink():
            return self.read_state()
        flags = os.O_CREAT | os.O_EXCL | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(self.path, flags, 0o600)
        except FileExistsError:
            # Another initializer won the race. Validate; never reset.
            return self.read_state()
        except OSError as exc:
            raise TrustStoreError("cannot securely create trust-state database") from exc
        else:
            os.close(descriptor)

        connection = None
        try:
            connection = self._connect_existing()
            connection.execute("BEGIN IMMEDIATE")
            if self._pragma_user_version(connection) != 0:
                raise TrustStoreError("new trust-state database has unexpected schema version")
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            if tables:
                raise TrustStoreError("new trust-state database is not empty")
            connection.execute(
                f"""
                CREATE TABLE {_TABLE} (
                    singleton INTEGER NOT NULL PRIMARY KEY CHECK(singleton = 1),
                    bundle_version INTEGER NOT NULL CHECK(
                        typeof(bundle_version) = 'integer' AND bundle_version >= 0
                    ),
                    manifest_sha256 TEXT NOT NULL CHECK(
                        (bundle_version = 0 AND manifest_sha256 = '') OR
                        (bundle_version > 0 AND length(manifest_sha256) = 64)
                    ),
                    manifest_bytes BLOB NOT NULL CHECK(
                        typeof(manifest_bytes) = 'blob' AND
                        ((bundle_version = 0 AND length(manifest_bytes) = 0) OR
                         (bundle_version > 0 AND length(manifest_bytes) BETWEEN 1 AND {MAX_MANIFEST_BYTES}))
                    ),
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                f"INSERT INTO {_TABLE} "
                "(singleton, bundle_version, manifest_sha256, manifest_bytes, updated_at) "
                "VALUES (1, 0, '', X'', ?)",
                (_INITIAL_TIME,),
            )
            connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
            connection.execute("COMMIT")
            return TrustBundleState(0, "", b"", _INITIAL_TIME)
        except TrustStoreError:
            self._rollback(connection)
            raise
        except (sqlite3.DatabaseError, OSError) as exc:
            self._rollback(connection)
            raise TrustStoreError("trust-state database initialization failed") from exc
        finally:
            if connection is not None:
                connection.close()

    def read_state(self) -> TrustBundleState:
        """Read and validate the existing ledger; never initialize or repair it."""
        connection = self._connect_existing()
        try:
            connection.execute("BEGIN")
            state = self._read_state_in_transaction(connection)
            connection.execute("COMMIT")
            return state
        except TrustStoreError:
            self._rollback(connection)
            raise
        except (sqlite3.DatabaseError, OSError) as exc:
            self._rollback(connection)
            raise TrustStoreError("trust-state database read failed") from exc
        finally:
            connection.close()

    def load_committed(
        self,
        *,
        pinned_update_keys: Mapping[str, bytes],
        now: datetime,
    ) -> CommittedTrustBundle:
        """Re-authenticate the stored signed manifest before it is reused."""
        state = self.read_state()
        if state.bundle_version == 0 or not state.manifest_bytes:
            raise TrustStoreError("no authenticated trust manifest has been committed")
        try:
            authenticated = verify_trust_manifest(
                state.manifest_bytes,
                pinned_update_keys=pinned_update_keys,
                current_version=state.bundle_version - 1,
                now=now,
            )
        except (ManifestVerificationError, ManifestError, TypeError, ValueError) as exc:
            raise TrustStoreError("stored trust manifest could not be re-authenticated") from exc
        if (
            authenticated.manifest.bundle_version != state.bundle_version
            or hashlib.sha256(state.manifest_bytes).hexdigest() != state.manifest_sha256
        ):
            raise TrustStoreError("stored trust manifest does not match committed state")
        return CommittedTrustBundle(authenticated, state)

    def verify_and_commit(
        self,
        raw_manifest: bytes,
        *,
        pinned_update_keys: Mapping[str, bytes],
        now: datetime,
    ) -> CommittedTrustBundle:
        """Verify and atomically persist the signed manifest and its version.

        The SQLite write lock is acquired before reading the current version.
        Signature/policy verification, manifest-byte persistence and the
        compare-and-swap version update occur within the same transaction.
        A failed verification or failed commit leaves the previous state
        unchanged and returns no authenticated result.
        """
        connection = self._connect_existing()
        try:
            connection.execute("BEGIN IMMEDIATE")
            current = self._read_state_in_transaction(connection)
            try:
                authenticated = verify_trust_manifest(
                    raw_manifest,
                    pinned_update_keys=pinned_update_keys,
                    current_version=current.bundle_version,
                    now=now,
                )
            except (ManifestVerificationError, ManifestError, TypeError, ValueError) as exc:
                raise TrustStoreError("trust manifest verification rejected") from exc

            digest = hashlib.sha256(raw_manifest).hexdigest()
            updated_at = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            cursor = connection.execute(
                f"""
                UPDATE {_TABLE}
                SET bundle_version = ?, manifest_sha256 = ?, manifest_bytes = ?, updated_at = ?
                WHERE singleton = 1 AND bundle_version = ?
                """,
                (
                    authenticated.manifest.bundle_version,
                    digest,
                    sqlite3.Binary(raw_manifest),
                    updated_at,
                    current.bundle_version,
                ),
            )
            if cursor.rowcount != 1:
                raise TrustStoreError("anti-rollback compare-and-swap failed")
            connection.execute("COMMIT")
            state = TrustBundleState(
                authenticated.manifest.bundle_version, digest, raw_manifest, updated_at
            )
            return CommittedTrustBundle(authenticated, state)
        except TrustStoreError:
            self._rollback(connection)
            raise
        except (sqlite3.DatabaseError, OSError) as exc:
            self._rollback(connection)
            raise TrustStoreError("trust-state transaction failed closed") from exc
        finally:
            connection.close()

    def _connect_existing(self) -> sqlite3.Connection:
        try:
            metadata = self.path.lstat()
        except OSError as exc:
            raise TrustStoreError("trust-state database is missing or inaccessible") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise TrustStoreError("trust-state path must be a regular non-symlink file")
        if metadata.st_size > _MAX_DATABASE_BYTES:
            raise TrustStoreError("trust-state database exceeds its size limit")
        if os.name == "posix" and stat.S_IMODE(metadata.st_mode) & 0o077:
            raise TrustStoreError("trust-state database permissions must be owner-only")
        try:
            # mode=rw prevents a deletion race between lstat() and connect()
            # from silently creating a fresh version-zero ledger.
            database_uri = self.path.absolute().as_uri() + "?mode=rw"
            connection = sqlite3.connect(
                database_uri,
                uri=True,
                timeout=self.timeout_seconds,
                isolation_level=None,
            )
            connection.execute(f"PRAGMA busy_timeout = {int(self.timeout_seconds * 1000)}")
            connection.execute("PRAGMA synchronous = FULL")
            return connection
        except (sqlite3.DatabaseError, OSError) as exc:
            raise TrustStoreError("cannot open trust-state database") from exc

    @staticmethod
    def _pragma_user_version(connection: sqlite3.Connection) -> int:
        row = connection.execute("PRAGMA user_version").fetchone()
        if not row or type(row[0]) is not int:
            raise TrustStoreError("trust-state schema version is unreadable")
        return row[0]

    def _read_state_in_transaction(self, connection: sqlite3.Connection) -> TrustBundleState:
        check = connection.execute("PRAGMA quick_check(1)").fetchone()
        if not check or check[0] != "ok":
            raise TrustStoreError("trust-state database integrity check failed")
        if self._pragma_user_version(connection) != _SCHEMA_VERSION:
            raise TrustStoreError("unsupported or uninitialized trust-state schema")
        columns = connection.execute(f"PRAGMA table_info({_TABLE})").fetchall()
        expected = [
            ("singleton", "INTEGER", 1, 1),
            ("bundle_version", "INTEGER", 1, 0),
            ("manifest_sha256", "TEXT", 1, 0),
            ("manifest_bytes", "BLOB", 1, 0),
            ("updated_at", "TEXT", 1, 0),
        ]
        actual = [(row[1], row[2].upper(), row[3], row[5]) for row in columns]
        if actual != expected:
            raise TrustStoreError("trust-state schema does not match the expected contract")
        rows = connection.execute(
            f"SELECT singleton, bundle_version, manifest_sha256, manifest_bytes, updated_at "
            f"FROM {_TABLE}"
        ).fetchall()
        if len(rows) != 1:
            raise TrustStoreError("trust-state ledger must contain exactly one row")
        singleton, version, digest, manifest_bytes, updated_at = rows[0]
        if singleton != 1 or type(version) is not int or version < 0:
            raise TrustStoreError("trust-state ledger row is invalid")
        if type(digest) is not str or type(manifest_bytes) is not bytes or type(updated_at) is not str:
            raise TrustStoreError("trust-state ledger fields are invalid")
        if version == 0:
            if digest != "" or manifest_bytes != b"" or updated_at != _INITIAL_TIME:
                raise TrustStoreError("initial trust-state row is inconsistent")
        else:
            if not _HASH_RE.fullmatch(digest):
                raise TrustStoreError("committed manifest digest is invalid")
            if not (1 <= len(manifest_bytes) <= MAX_MANIFEST_BYTES):
                raise TrustStoreError("committed manifest bytes are outside the size limit")
            if hashlib.sha256(manifest_bytes).hexdigest() != digest:
                raise TrustStoreError("committed manifest digest does not match stored bytes")
        try:
            parsed_time = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
            if parsed_time.strftime("%Y-%m-%dT%H:%M:%SZ") != updated_at:
                raise ValueError("non-canonical timestamp")
        except ValueError as exc:
            raise TrustStoreError("trust-state timestamp is invalid") from exc
        return TrustBundleState(version, digest, manifest_bytes, updated_at)

    @staticmethod
    def _rollback(connection: sqlite3.Connection | None) -> None:
        if connection is not None and connection.in_transaction:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.DatabaseError:
                pass
