import hashlib
import os
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.attestation_trust_store import SQLiteTrustVersionStore, TrustStoreError
from attestation_test_support import build_manifest


NOW = datetime(2026, 11, 5, 3, 0, tzinfo=timezone.utc)


class AttestationTrustStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "trust-state.sqlite3"
        self.store = SQLiteTrustVersionStore(self.path)
        self.signer = Ed25519PrivateKey.generate()
        self.public = self.signer.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        self.keys = {"release-key-1": self.public}
        self.store.initialize()

    def tearDown(self):
        self.temp.cleanup()

    def verify(self, version, *, raw=None, store=None):
        return (store or self.store).verify_and_commit(
            build_manifest(self.signer, bundle_version=version) if raw is None else raw,
            pinned_update_keys=self.keys,
            now=NOW,
        )

    def test_initialization_is_owner_only_and_idempotent(self):
        first = self.store.read_state()
        second = SQLiteTrustVersionStore(self.path).initialize()
        self.assertEqual(first, second)
        if os.name == "posix":
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_success_advances_version_and_records_manifest_digest(self):
        raw = build_manifest(self.signer, bundle_version=8)
        result = self.verify(8, raw=raw)
        state = self.store.read_state()
        self.assertEqual(state.bundle_version, 8)
        self.assertEqual(state.manifest_sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(state.manifest_bytes, raw)
        self.assertEqual(result.state, state)

    def test_restart_preserves_committed_version(self):
        self.verify(8)
        restarted = SQLiteTrustVersionStore(self.path)
        loaded = restarted.load_committed(pinned_update_keys=self.keys, now=NOW)
        self.assertEqual(loaded.state.bundle_version, 8)
        self.assertEqual(loaded.authenticated_manifest.manifest.bundle_version, 8)

    def test_equal_version_replay_is_rejected_without_state_change(self):
        self.verify(8)
        before = self.store.read_state()
        with self.assertRaises(TrustStoreError):
            self.verify(8)
        self.assertEqual(self.store.read_state(), before)

    def test_older_version_rollback_is_rejected_without_state_change(self):
        self.verify(9)
        before = self.store.read_state()
        with self.assertRaises(TrustStoreError):
            self.verify(8)
        self.assertEqual(self.store.read_state(), before)

    def test_bad_signature_does_not_advance_state(self):
        raw = build_manifest(self.signer, bundle_version=8)
        tampered = raw.replace(b'"bundle_version":8', b'"bundle_version":9')
        with self.assertRaises(TrustStoreError):
            self.verify(8, raw=tampered)
        self.assertEqual(self.store.read_state().bundle_version, 0)

    def test_stored_manifest_digest_mismatch_fails_closed(self):
        self.verify(8)
        db = sqlite3.connect(self.path)
        db.execute(
            "UPDATE trust_bundle_state SET manifest_bytes = ? WHERE singleton = 1",
            (sqlite3.Binary(b"tampered"),),
        )
        db.commit()
        db.close()
        with self.assertRaises(TrustStoreError):
            self.store.read_state()

    def test_expired_stored_manifest_is_not_reauthenticated(self):
        self.verify(8)
        later = datetime(2028, 1, 1, tzinfo=timezone.utc)
        with self.assertRaises(TrustStoreError):
            self.store.load_committed(pinned_update_keys=self.keys, now=later)

    def test_missing_database_fails_closed_without_reinitializing(self):
        self.path.unlink()
        with self.assertRaises(TrustStoreError):
            self.verify(8)
        self.assertFalse(self.path.exists())

    def test_corrupt_database_fails_closed_and_is_not_repaired(self):
        self.path.write_bytes(b"not a sqlite database")
        before = self.path.read_bytes()
        with self.assertRaises(TrustStoreError):
            self.store.read_state()
        self.assertEqual(self.path.read_bytes(), before)

    def test_initialize_never_overwrites_an_existing_corrupt_database(self):
        self.path.write_bytes(b"corrupt-existing-state")
        before = self.path.read_bytes()
        with self.assertRaises(TrustStoreError):
            SQLiteTrustVersionStore(self.path).initialize()
        self.assertEqual(self.path.read_bytes(), before)

    def test_writer_lock_timeout_fails_closed(self):
        blocker = sqlite3.connect(self.path, timeout=1, isolation_level=None)
        blocker.execute("BEGIN IMMEDIATE")
        try:
            short_wait = SQLiteTrustVersionStore(self.path, timeout_seconds=0.05)
            with self.assertRaises(TrustStoreError):
                short_wait.verify_and_commit(
                    build_manifest(self.signer, bundle_version=8),
                    pinned_update_keys=self.keys,
                    now=NOW,
                )
            self.assertEqual(self.store.read_state().bundle_version, 0)
        finally:
            blocker.execute("ROLLBACK")
            blocker.close()

    def test_wrong_schema_fails_closed(self):
        self.path.unlink()
        db = sqlite3.connect(self.path)
        db.execute("CREATE TABLE trust_bundle_state (bad TEXT)")
        db.execute("PRAGMA user_version = 1")
        db.commit()
        db.close()
        os.chmod(self.path, 0o600)
        with self.assertRaises(TrustStoreError):
            self.store.read_state()

    def test_permissive_database_permissions_are_rejected(self):
        if os.name != "posix":
            self.skipTest("POSIX file permissions are not available")
        os.chmod(self.path, 0o644)
        with self.assertRaises(TrustStoreError):
            self.store.read_state()

    def test_symlink_database_is_rejected(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are not available")
        target = Path(self.temp.name) / "target.sqlite3"
        target.write_bytes(self.path.read_bytes())
        os.chmod(target, 0o600)
        link = Path(self.temp.name) / "linked.sqlite3"
        link.symlink_to(target)
        with self.assertRaises(TrustStoreError):
            SQLiteTrustVersionStore(link).read_state()

    def test_concurrent_same_version_allows_exactly_one_commit(self):
        barrier = threading.Barrier(2)
        raw = build_manifest(self.signer, bundle_version=8)

        def worker():
            store = SQLiteTrustVersionStore(self.path)
            barrier.wait()
            try:
                store.verify_and_commit(raw, pinned_update_keys=self.keys, now=NOW)
                return "accepted"
            except TrustStoreError:
                return "rejected"

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(outcomes.count("accepted"), 1)
        self.assertEqual(outcomes.count("rejected"), 1)
        self.assertEqual(self.store.read_state().bundle_version, 8)

    def test_concurrent_increasing_versions_never_roll_back(self):
        barrier = threading.Barrier(4)
        versions = [8, 9, 10, 11]

        def worker(version):
            store = SQLiteTrustVersionStore(self.path)
            raw = build_manifest(self.signer, bundle_version=version)
            barrier.wait()
            try:
                store.verify_and_commit(raw, pinned_update_keys=self.keys, now=NOW)
                return True
            except TrustStoreError:
                return False

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(worker, versions))
        self.assertEqual(self.store.read_state().bundle_version, max(versions))


if __name__ == "__main__":
    unittest.main()
