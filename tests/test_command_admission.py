import os
import sqlite3
from contextlib import closing
import stat
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch
from dataclasses import replace

from core.command_admission import DurableReplayLedger, admit_signed_command
from core.command_security import SignedCommand, sign

KEY = b"test-device-secret-32-byte-minimum-abc"


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, "replay.sqlite")
        self.ledger = DurableReplayLedger(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def command(self, action="get_battery", args=None, issued_at=1000, command_id="id-1"):
        cmd = SignedCommand(command_id, issued_at, action, {} if args is None else args, "")
        return replace(cmd, signature=sign(cmd, KEY))

    def check(self, cmd=None, **kwargs):
        return admit_signed_command(
            self.command() if cmd is None else cmd,
            device_id=kwargs.pop("device_id", "pixel-caiman"),
            device_key=kwargs.pop("device_key", KEY),
            transport_authenticated=kwargs.pop("transport_authenticated", True),
            ledger=kwargs.pop("ledger", self.ledger),
            now=kwargs.pop("now", 1001),
        )

    def test_valid_battery_command(self):
        self.assertEqual(self.check().reason, "ADMITTED_NO_EXECUTION")

    def test_replay_blocked(self):
        self.assertTrue(self.check().admitted)
        self.assertFalse(self.check().admitted)

    def test_replay_ledger_closes_every_connection(self):
        class TrackedConnection(sqlite3.Connection):
            opened = 0
            closed = 0

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                type(self).opened += 1

            def close(self):
                type(self).closed += 1
                super().close()

        def tracked_connect(ledger):
            return sqlite3.connect(
                ledger.path, timeout=5, isolation_level=None,
                factory=TrackedConnection,
            )

        with patch.object(DurableReplayLedger, "_connect", tracked_connect):
            ledger = DurableReplayLedger(os.path.join(self.temp.name, "tracked.sqlite"))
            self.assertTrue(ledger.reserve("pixel-1", "nonce-1", 100))
            self.assertFalse(ledger.reserve("pixel-1", "nonce-1", 100))
        self.assertEqual(TrackedConnection.opened, 3)
        self.assertEqual(TrackedConnection.closed, TrackedConnection.opened)


    @unittest.skipUnless(os.name == "posix", "POSIX file mode")
    def test_replay_file_is_private_under_permissive_umask(self):
        old = os.umask(0o022)
        try:
            ledger = DurableReplayLedger(os.path.join(self.temp.name, "private.sqlite"))
        finally:
            os.umask(old)
        self.assertEqual(stat.S_IMODE(os.stat(ledger.path).st_mode), 0o600)
        self.assertTrue(ledger.reserve("pixel", "nonce", 100))

    @unittest.skipUnless(os.name == "posix", "POSIX file mode")
    def test_existing_world_readable_replay_file_rejected(self):
        path = os.path.join(self.temp.name, "exposed.sqlite")
        with open(path, "wb") as file:
            file.write(b"")
        os.chmod(path, 0o644)
        with self.assertRaisesRegex(ValueError, "owner-only"):
            DurableReplayLedger(path)

    @unittest.skipUnless(os.name == "posix", "POSIX file ownership")
    def test_hardlinked_replay_file_rejected_at_initialization(self):
        path = os.path.join(self.temp.name, "linked.sqlite")
        with open(path, "wb"):
            pass
        os.chmod(path, 0o600)
        os.link(path, os.path.join(self.temp.name, "alias.sqlite"))
        with self.assertRaisesRegex(ValueError, "unlinked elsewhere"):
            DurableReplayLedger(path)

    @unittest.skipUnless(os.name == "posix", "POSIX file ownership")
    def test_new_hardlink_causes_fail_closed_admission(self):
        ledger = DurableReplayLedger(os.path.join(self.temp.name, "hardlink.sqlite"))
        self.assertTrue(self.check(ledger=ledger).admitted)
        alias = os.path.join(self.temp.name, "alias.sqlite")
        os.link(ledger.path, alias)
        self.assertEqual(
            self.check(self.command(command_id="id-2"), ledger=ledger).reason,
            "LEDGER_UNAVAILABLE",
        )

    @unittest.skipUnless(os.name == "posix", "POSIX directory permissions")
    def test_world_writable_nonsticky_parent_rejected(self):
        parent = os.path.join(self.temp.name, "unsafe")
        os.mkdir(parent, 0o700)
        os.chmod(parent, 0o777)
        try:
            with self.assertRaisesRegex(ValueError, "parent directory is unsafe"):
                DurableReplayLedger(os.path.join(parent, "ledger.sqlite"))
        finally:
            os.chmod(parent, 0o700)

    @unittest.skipUnless(os.name == "posix", "POSIX directory permissions")
    def test_world_readable_immediate_parent_rejected_for_sqlite_sidecars(self):
        parent = os.path.join(self.temp.name, "readable")
        os.mkdir(parent, 0o700)
        for mode in (0o755, 0o750, 0o711, 0o770):
            with self.subTest(mode=oct(mode)):
                os.chmod(parent, mode)
                with self.assertRaisesRegex(ValueError, "parent directory is unsafe"):
                    DurableReplayLedger(os.path.join(parent, "ledger.sqlite"))

    @unittest.skipUnless(os.name == "posix", "POSIX directory permissions")
    def test_private_child_under_sticky_ancestor_supported(self):
        ancestor = os.path.join(self.temp.name, "sticky-ancestor")
        private = os.path.join(ancestor, "private")
        os.mkdir(ancestor, 0o700)
        os.chmod(ancestor, 0o1777)
        os.mkdir(private, 0o700)
        ledger = DurableReplayLedger(os.path.join(private, "ledger.sqlite"))
        self.assertTrue(ledger.reserve("pixel", "nonce", 100))

    @unittest.skipUnless(os.name == "posix", "POSIX directory permissions")
    def test_readable_parent_after_open_denies_admission(self):
        parent = os.path.join(self.temp.name, "readable-later")
        os.mkdir(parent, 0o700)
        ledger = DurableReplayLedger(os.path.join(parent, "ledger.sqlite"))
        os.chmod(parent, 0o755)
        self.assertEqual(self.check(ledger=ledger).reason, "LEDGER_UNAVAILABLE")

    @unittest.skipUnless(os.name == "posix", "POSIX directory permissions")
    def test_parent_permission_downgrade_fails_closed(self):
        parent = os.path.join(self.temp.name, "downgraded")
        os.mkdir(parent, 0o700)
        ledger = DurableReplayLedger(os.path.join(parent, "ledger.sqlite"))
        os.chmod(parent, 0o777)
        try:
            self.assertEqual(self.check(ledger=ledger).reason, "LEDGER_UNAVAILABLE")
        finally:
            os.chmod(parent, 0o700)

    @unittest.skipUnless(os.name == "posix", "POSIX directory permissions")
    def test_untrusted_sticky_directory_owner_is_rejected(self):
        from types import SimpleNamespace
        ledger = DurableReplayLedger(os.path.join(self.temp.name, "trusted.sqlite"))
        fake_stat = SimpleNamespace(
            st_mode=stat.S_IFDIR | 0o1777, st_uid=os.geteuid() + 1000,
        )
        with patch("core.command_admission.os.lstat", return_value=fake_stat):
            self.assertFalse(ledger._parent_is_safe())

    @unittest.skipUnless(os.name == "posix", "POSIX directory security")
    def test_untrusted_private_parent_owner_rejected(self):
        from types import SimpleNamespace
        ledger = DurableReplayLedger(os.path.join(self.temp.name, "trusted.sqlite"))
        fake_stat = SimpleNamespace(
            st_mode=stat.S_IFDIR | 0o700, st_uid=os.geteuid() + 1000,
        )
        with patch("core.command_admission.os.lstat", return_value=fake_stat):
            self.assertFalse(ledger._parent_is_safe())

    @unittest.skipUnless(os.name == "posix", "POSIX directory security")
    def test_untrusted_private_ancestor_owner_rejected(self):
        from types import SimpleNamespace
        ancestor = os.path.join(self.temp.name, "ancestor")
        private = os.path.join(ancestor, "private")
        os.makedirs(private, mode=0o700)
        real_lstat = os.lstat

        def altered_lstat(path):
            info = real_lstat(path)
            if path == ancestor:
                return SimpleNamespace(
                    st_mode=info.st_mode, st_uid=os.geteuid() + 1000,
                )
            return info

        with patch("core.command_admission.os.lstat", side_effect=altered_lstat):
            with self.assertRaisesRegex(ValueError, "parent directory is unsafe"):
                DurableReplayLedger(os.path.join(private, "ledger.sqlite"))

    @unittest.skipUnless(os.name == "posix", "POSIX directory security")
    def test_symlinked_parent_rejected_even_when_target_private(self):
        real = os.path.join(self.temp.name, "real")
        os.mkdir(real, 0o700)
        alias = os.path.join(self.temp.name, "alias")
        os.symlink(real, alias)
        with self.assertRaisesRegex(ValueError, "parent directory is unsafe"):
            DurableReplayLedger(os.path.join(alias, "ledger.sqlite"))

    @unittest.skipUnless(os.name == "posix", "POSIX directory security")
    def test_symlinked_grandparent_rejected(self):
        real = os.path.join(self.temp.name, "real")
        os.makedirs(os.path.join(real, "private"), mode=0o700)
        alias = os.path.join(self.temp.name, "alias")
        os.symlink(real, alias)
        with self.assertRaisesRegex(ValueError, "parent directory is unsafe"):
            DurableReplayLedger(os.path.join(alias, "private", "ledger.sqlite"))

    @unittest.skipUnless(os.name == "posix", "POSIX directory security")
    def test_world_writable_nonsticky_grandparent_rejected(self):
        ancestor = os.path.join(self.temp.name, "unsafe")
        private = os.path.join(ancestor, "private")
        os.makedirs(private, mode=0o700)
        os.chmod(ancestor, 0o777)
        try:
            with self.assertRaisesRegex(ValueError, "parent directory is unsafe"):
                DurableReplayLedger(os.path.join(private, "ledger.sqlite"))
        finally:
            os.chmod(ancestor, 0o700)

    @unittest.skipUnless(os.name == "posix", "POSIX directory security")
    def test_ancestor_permission_relaxation_fails_closed(self):
        ancestor = os.path.join(self.temp.name, "safe")
        private = os.path.join(ancestor, "private")
        os.makedirs(private, mode=0o700)
        ledger = DurableReplayLedger(os.path.join(private, "ledger.sqlite"))
        self.assertTrue(self.check(ledger=ledger).admitted)
        os.chmod(ancestor, 0o777)
        try:
            self.assertEqual(
                self.check(self.command(command_id="id-2"), ledger=ledger).reason,
                "LEDGER_UNAVAILABLE",
            )
        finally:
            os.chmod(ancestor, 0o700)

    @unittest.skipUnless(os.name == "posix", "POSIX directory security")
    def test_retargeted_parent_symlink_fails_closed_without_inode_change(self):
        parent = os.path.join(self.temp.name, "private")
        os.mkdir(parent, 0o700)
        ledger = DurableReplayLedger(os.path.join(parent, "ledger.sqlite"))
        self.assertTrue(self.check(ledger=ledger).admitted)
        moved = os.path.join(self.temp.name, "private-old")
        os.rename(parent, moved)
        os.symlink(moved, parent)
        self.assertEqual(
            self.check(self.command(command_id="id-2"), ledger=ledger).reason,
            "LEDGER_UNAVAILABLE",
        )

    @unittest.skipUnless(os.name == "posix", "POSIX directory permissions")
    def test_sticky_world_writable_immediate_parent_rejected(self):
        # Sticky protects the database inode, not SQLite -journal/-wal/-shm
        # sidecar names that another directory writer could pre-create.
        parent = os.path.join(self.temp.name, "sticky")
        os.mkdir(parent, 0o700)
        os.chmod(parent, 0o1777)
        try:
            with self.assertRaisesRegex(ValueError, "parent directory is unsafe"):
                DurableReplayLedger(os.path.join(parent, "ledger.sqlite"))
        finally:
            os.chmod(parent, 0o700)

    def test_symlink_replay_file_rejected(self):
        path = os.path.join(self.temp.name, "target.sqlite")
        with open(path, "wb"):
            pass
        link = os.path.join(self.temp.name, "link.sqlite")
        try:
            os.symlink(path, link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "non-symlink"):
            DurableReplayLedger(link)

    def test_replaced_replay_file_fails_closed(self):
        path = os.path.join(self.temp.name, "replace.sqlite")
        ledger = DurableReplayLedger(path)
        self.assertTrue(self.check(ledger=ledger).admitted)
        os.unlink(path)
        # sqlite3.Connection.__exit__ commits/rolls back but does not close.
        with closing(sqlite3.connect(path)):
            pass
        self.assertEqual(self.check(self.command(command_id="id-2"), ledger=ledger).reason,
                         "LEDGER_UNAVAILABLE")

    @unittest.skipUnless(os.name == "posix", "POSIX file mode")
    def test_replay_file_permission_downgrade_fails_closed(self):
        ledger = DurableReplayLedger(os.path.join(self.temp.name, "downgrade.sqlite"))
        os.chmod(ledger.path, 0o644)
        self.assertEqual(self.check(ledger=ledger).reason, "LEDGER_UNAVAILABLE")

    @unittest.skipUnless(os.name == "posix", "POSIX inode identity")
    def test_ledger_swap_after_commit_refuses_admission(self):
        # A same-UID writer can restore an old database snapshot after the
        # reservation commits. The caller must not report success if the
        # canonical pathname no longer points to the verified inode.
        import shutil
        saved = os.path.join(self.temp.name, "snapshot-after.sqlite")
        shutil.copyfile(self.path, saved)
        os.chmod(saved, 0o600)
        real_connect = sqlite3.connect

        class SwapAfterCommit(sqlite3.Connection):
            def execute(self, statement, parameters=()):
                result = super().execute(statement, parameters)
                if statement == "COMMIT":
                    os.replace(saved, self_path)
                return result

        self_path = self.path
        def connect(*args, **kwargs):
            return real_connect(*args, factory=SwapAfterCommit, **kwargs)

        with patch("core.command_admission.sqlite3.connect", side_effect=connect):
            self.assertEqual(self.check().reason, "LEDGER_UNAVAILABLE")
        # The original instance also rejects the replacement on reuse.
        self.assertEqual(self.check().reason, "LEDGER_UNAVAILABLE")

    @unittest.skipUnless(os.name == "posix", "POSIX inode identity")
    def test_ledger_swap_during_transaction_refuses_admission(self):
        import shutil
        saved = os.path.join(self.temp.name, "snapshot-before.sqlite")
        shutil.copyfile(self.path, saved)
        os.chmod(saved, 0o600)
        real_connect = sqlite3.connect
        self_path = self.path

        class SwapDuringInsert(sqlite3.Connection):
            def execute(self, statement, parameters=()):
                result = super().execute(statement, parameters)
                if statement.startswith("INSERT INTO seen("):
                    os.replace(saved, self_path)
                return result

        def connect(*args, **kwargs):
            return real_connect(*args, factory=SwapDuringInsert, **kwargs)

        with patch("core.command_admission.sqlite3.connect", side_effect=connect):
            self.assertEqual(self.check().reason, "LEDGER_UNAVAILABLE")

    def test_memory_only_replay_ledger_rejected(self):
        with self.assertRaisesRegex(ValueError, "durable"):
            DurableReplayLedger(":memory:")

    def test_non_integer_ledger_limits_rejected(self):
        for ttl, capacity in [(True, 10), (60, False), (1.5, 10)]:
            with self.subTest(ttl=ttl, capacity=capacity):
                with self.assertRaises(ValueError):
                    DurableReplayLedger(os.path.join(self.temp.name, "bad.sqlite"),
                                        ttl_seconds=ttl, max_entries=capacity)

    def test_replay_survives_restart(self):
        self.assertTrue(self.check().admitted)
        self.assertFalse(self.check(ledger=DurableReplayLedger(self.path)).admitted)

    def test_rollback_rejected_before_pruning_or_nonce_reservation(self):
        self.assertTrue(self.ledger.reserve("pixel", "nonce-1000", 1000))
        with self.assertRaisesRegex(sqlite3.DataError, "clock rollback"):
            self.ledger.reserve("pixel", "nonce-rollback", 999)
        # A rejected rollback must not consume a nonce or remove a row.
        self.assertTrue(self.ledger.reserve("pixel", "nonce-rollback", 1000))
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM seen").fetchone()[0], 2)

    def test_clock_watermark_survives_ttl_pruning_and_restart(self):
        self.assertTrue(self.ledger.reserve("pixel", "old", 100))
        self.assertTrue(self.ledger.reserve("pixel", "new", 1000))
        reopened = DurableReplayLedger(self.path)
        with self.assertRaisesRegex(sqlite3.DataError, "clock rollback"):
            reopened.reserve("pixel", "rollback", 900)
        self.assertTrue(reopened.reserve("pixel", "after-restart", 1001))

    def test_signed_command_denied_after_clock_rollback(self):
        self.assertTrue(self.check().admitted)
        rolled_back = self.command(issued_at=999, command_id="new-rollback")
        self.assertEqual(self.check(rolled_back, now=999).reason, "LEDGER_UNAVAILABLE")
        self.assertEqual(
            self.check(rolled_back, now=1001).reason,
            "ADMITTED_NO_EXECUTION",
        )

    def test_legacy_ledger_migrates_existing_seen_timestamp(self):
        path = os.path.join(self.temp.name, "legacy.sqlite")
        with closing(sqlite3.connect(path)) as db:
            db.execute("CREATE TABLE seen (device_id TEXT NOT NULL, "
                       "command_id TEXT NOT NULL, seen_at INTEGER NOT NULL, "
                       "PRIMARY KEY (device_id, command_id))")
            db.execute("INSERT INTO seen VALUES ('pixel', 'legacy', 1000)")
            db.commit()
        os.chmod(path, 0o600)
        ledger = DurableReplayLedger(path)
        with self.assertRaisesRegex(sqlite3.DataError, "clock rollback"):
            ledger.reserve("pixel", "new", 999)
        self.assertFalse(ledger.reserve("pixel", "legacy", 1000))
        self.assertTrue(ledger.reserve("pixel", "new", 1001))

    def test_missing_clock_watermark_fails_closed(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DELETE FROM ledger_clock")
            db.commit()
        with self.assertRaises(sqlite3.DatabaseError):
            self.ledger.reserve("pixel", "new", 1001)

    def test_deleted_watermark_stays_unavailable_after_restart(self):
        self.assertTrue(self.ledger.reserve("pixel", "original", 1000))
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DELETE FROM ledger_clock")
            db.commit()
        with self.assertRaisesRegex(sqlite3.DatabaseError, "watermark inconsistent"):
            DurableReplayLedger(self.path)
        # Reopening must not have silently restored a missing security record.
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ledger_clock").fetchone()[0], 0)

    def test_watermark_below_retained_nonce_fails_on_restart(self):
        self.assertTrue(self.ledger.reserve("pixel", "original", 1000))
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE ledger_clock SET max_now=1 WHERE id=1")
            db.commit()
        with self.assertRaisesRegex(sqlite3.DatabaseError, "watermark inconsistent"):
            DurableReplayLedger(self.path)

    def test_negative_or_text_watermark_fails_on_restart(self):
        for invalid in (-1, "corrupt"):
            with self.subTest(invalid=invalid):
                path = os.path.join(self.temp.name, f"corrupt-{invalid}.sqlite")
                DurableReplayLedger(path)
                with closing(sqlite3.connect(path)) as db:
                    db.execute("UPDATE ledger_clock SET max_now=? WHERE id=1", (invalid,))
                    db.commit()
                with self.assertRaisesRegex(sqlite3.DatabaseError, "watermark inconsistent"):
                    DurableReplayLedger(path)

    def test_live_ledger_refuses_lowered_clock_below_retained_nonce(self):
        self.assertTrue(self.ledger.reserve("pixel", "original", 1000))
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE ledger_clock SET max_now=1 WHERE id=1")
            db.commit()
        # The already-open ledger must fail closed without requiring restart.
        with self.assertRaisesRegex(sqlite3.DatabaseError, "watermark inconsistent"):
            self.ledger.reserve("pixel", "new", 900)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM seen").fetchone()[0], 1)

    def test_live_ledger_refuses_invalid_clock_types_and_negative_values(self):
        for invalid in (-1, "corrupt"):
            with self.subTest(invalid=invalid):
                path = os.path.join(self.temp.name, f"live-invalid-{invalid}.sqlite")
                ledger = DurableReplayLedger(path)
                with closing(sqlite3.connect(path)) as db:
                    db.execute("UPDATE ledger_clock SET max_now=? WHERE id=1", (invalid,))
                    db.commit()
                with self.assertRaisesRegex(sqlite3.DatabaseError, "watermark inconsistent"):
                    ledger.reserve("pixel", "new", 100)

    def test_live_signed_admission_denies_clock_corruption(self):
        self.assertTrue(self.check().admitted)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE ledger_clock SET max_now=1 WHERE id=1")
            db.commit()
        self.assertEqual(
            self.check(self.command(command_id="after-tamper"), now=1001).reason,
            "LEDGER_UNAVAILABLE",
        )

    def test_replay_trigger_erasing_nonce_fails_closed(self):
        # A writable SQLite schema must not make an admitted nonce disappear.
        with closing(sqlite3.connect(self.path)) as db:
            db.execute(
                "CREATE TRIGGER erase_nonce AFTER INSERT ON seen BEGIN "
                "DELETE FROM seen WHERE device_id=NEW.device_id "
                "AND command_id=NEW.command_id; END"
            )
            db.commit()
        self.assertEqual(self.check().reason, "LEDGER_UNAVAILABLE")
        self.assertEqual(self.check().reason, "LEDGER_UNAVAILABLE")
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM seen").fetchone()[0], 0)

    def test_reopened_ledger_rejects_unexpected_trigger(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute(
                "CREATE TRIGGER erase_nonce AFTER INSERT ON seen BEGIN "
                "DELETE FROM seen WHERE command_id=NEW.command_id; END"
            )
            db.commit()
        with self.assertRaisesRegex(sqlite3.DatabaseError, "unexpected trigger"):
            DurableReplayLedger(self.path)

    def test_clock_update_trigger_cannot_silently_reset_watermark(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute(
                "CREATE TRIGGER reset_clock AFTER UPDATE ON ledger_clock BEGIN "
                "UPDATE ledger_clock SET max_now=0 WHERE id=1; END"
            )
            db.commit()
        self.assertEqual(self.check().reason, "LEDGER_UNAVAILABLE")
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT max_now FROM ledger_clock").fetchone()[0], 0)

    def test_replaced_seen_schema_cannot_erase_replay_history(self):
        # A tampered schema must not silently reset previously accepted nonces.
        self.assertEqual(self.check().reason, "ADMITTED_NO_EXECUTION")
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DROP TABLE seen")
            db.execute(
                "CREATE TABLE seen (device_id TEXT NOT NULL, "
                "command_id TEXT NOT NULL, seen_at INTEGER NOT NULL)"
            )
            db.commit()
        self.assertEqual(self.check().reason, "LEDGER_UNAVAILABLE")
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM seen").fetchone()[0], 0)

    def test_reopened_ledger_rejects_seen_without_primary_key(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DROP TABLE seen")
            db.execute(
                "CREATE TABLE seen (device_id TEXT NOT NULL, "
                "command_id TEXT NOT NULL, seen_at INTEGER NOT NULL)"
            )
            db.commit()
        with self.assertRaisesRegex(sqlite3.DatabaseError, "schema"):
            DurableReplayLedger(self.path)

    def test_live_ledger_rejects_seen_column_integrity_downgrade(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DROP TABLE seen")
            db.execute(
                "CREATE TABLE seen (device_id TEXT, "
                "command_id TEXT, seen_at TEXT)"
            )
            db.commit()
        self.assertEqual(self.check().reason, "LEDGER_UNAVAILABLE")

    def test_live_clock_table_without_primary_key_fails_closed(self):
        self.assertTrue(self.ledger.reserve("pixel", "first", 1000))
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DROP TABLE ledger_clock")
            db.execute("CREATE TABLE ledger_clock (id INTEGER, max_now INTEGER NOT NULL)")
            db.execute("INSERT INTO ledger_clock VALUES (1, 1000)")
            db.commit()
        self.assertEqual(
            self.check(self.command(command_id="after-clock-schema"), now=1001).reason,
            "LEDGER_UNAVAILABLE",
        )
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM seen").fetchone()[0], 1)

    def test_reopened_ledger_rejects_clock_without_primary_key(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DROP TABLE ledger_clock")
            db.execute("CREATE TABLE ledger_clock (id INTEGER, max_now INTEGER NOT NULL)")
            db.execute("INSERT INTO ledger_clock VALUES (1, 0)")
            db.commit()
        with self.assertRaisesRegex(sqlite3.DatabaseError, "clock schema"):
            DurableReplayLedger(self.path)

    def test_live_clock_table_with_unexpected_row_fails_closed(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DROP TABLE ledger_clock")
            db.execute(
                "CREATE TABLE ledger_clock (id INTEGER PRIMARY KEY, max_now INTEGER NOT NULL)"
            )
            db.executemany(
                "INSERT INTO ledger_clock VALUES (?, ?)", [(1, 0), (2, 0)]
            )
            db.commit()
        self.assertEqual(self.check().reason, "LEDGER_UNAVAILABLE")

    def test_untrusted_transport(self):
        self.assertEqual(self.check(transport_authenticated=False).reason, "UNAUTHENTICATED")

    def test_device_key_mismatch(self):
        self.assertEqual(self.check(device_key=b"z" * 32).reason, "BAD_SIGNATURE")

    def test_tampering(self):
        self.assertEqual(self.check(replace(self.command(), action="root_shell")).reason, "BAD_SIGNATURE")

    def test_unknown_action(self):
        self.assertFalse(self.check(self.command(action="root_shell")).admitted)

    def test_out_of_range_sqlite_timestamps_fail_closed_without_exception(self):
        # A signed, fresh command at 2**63 previously reached sqlite3.bind
        # and raised an uncaught OverflowError instead of denying admission.
        for timestamp in (-1, 1 << 63, 1 << 100):
            with self.subTest(timestamp=timestamp):
                cmd = self.command(issued_at=timestamp, command_id=f"id-{timestamp}")
                self.assertEqual(
                    self.check(cmd, now=timestamp).reason, "INVALID_TIMESTAMP"
                )
        # A rejected timestamp must not reserve a nonce.
        self.assertTrue(self.check().admitted)

    def test_direct_replay_reservation_rejects_invalid_sqlite_time(self):
        for timestamp in (-1, True, 1 << 63, 1 << 100):
            with self.subTest(timestamp=timestamp):
                with self.assertRaises(sqlite3.DataError):
                    self.ledger.reserve("pixel", "nonce", timestamp)
        self.assertTrue(self.ledger.reserve("pixel", "nonce", 100))
        self.assertFalse(self.ledger.reserve("pixel", "nonce", 100))

    def test_ledger_ttl_cannot_overflow_sqlite_bound_parameter(self):
        with self.assertRaises(ValueError):
            DurableReplayLedger(
                os.path.join(self.temp.name, "oversized-ttl.sqlite"),
                ttl_seconds=1 << 63,
            )

    def test_expired(self):
        self.assertEqual(self.check(now=2000).reason, "EXPIRED_OR_FUTURE")

    def test_future(self):
        self.assertEqual(self.check(self.command(issued_at=2000)).reason, "EXPIRED_OR_FUTURE")

    def test_invalid_device(self):
        self.assertEqual(self.check(device_id="../other").reason, "INVALID_DEVICE")

    def test_nan_payload_rejected(self):
        self.assertEqual(self.check(self.command(args={"bad": float("nan")})).reason, "INVALID_PAYLOAD")

    def test_non_string_json_object_key_rejected(self):
        cmd = self.command(args={"nested": {1: "not-a-json-object-key"}})
        self.assertEqual(self.check(cmd).reason, "INVALID_PAYLOAD")

    def test_python_tuple_rejected_as_non_json_container(self):
        cmd = self.command(args={"items": ("one", "two")})
        self.assertEqual(self.check(cmd).reason, "INVALID_PAYLOAD")

    def test_excessive_json_depth_rejected(self):
        nested = "leaf"
        for _ in range(33):
            nested = {"child": nested}
        cmd = self.command(args={"nested": nested})
        self.assertEqual(self.check(cmd).reason, "INVALID_PAYLOAD")

    def test_excessive_json_node_count_rejected(self):
        cmd = self.command(args={"items": ["x"] * 4096})
        self.assertEqual(self.check(cmd).reason, "INVALID_PAYLOAD")

    def test_excessive_json_text_budget_rejected(self):
        cmd = self.command(args={"padding": "x" * 16385})
        self.assertEqual(self.check(cmd).reason, "INVALID_PAYLOAD")

    def test_oversized_action_name_rejected(self):
        cmd = self.command(action="x" * 129)
        self.assertEqual(self.check(cmd).reason, "INVALID_PAYLOAD")

    def test_valid_nested_json_values_are_accepted(self):
        cmd = self.command(args={"items": ["one", {"enabled": True, "count": 2, "ratio": 1.5, "empty": None}]})
        self.assertTrue(self.check(cmd).admitted)

    def test_large_payload_rejected(self):
        self.assertEqual(self.check(self.command(args={"padding": "x" * 9000})).reason, "PAYLOAD_TOO_LARGE")

    def test_missing_package_rejected(self):
        self.assertFalse(self.check(self.command(action="open_app", args={})).admitted)

    def test_valid_app_package(self):
        self.assertTrue(self.check(self.command(action="open_app", args={"packageName": "com.android.settings"})).admitted)

    def test_capacity_fail_closed(self):
        small = DurableReplayLedger(os.path.join(self.temp.name, "small.sqlite"), max_entries=1)
        self.assertTrue(self.check(ledger=small).admitted)
        self.assertEqual(self.check(self.command(command_id="id-2"), ledger=small).reason, "REPLAY_OR_CAPACITY")

    def test_concurrent_replay_only_one_wins(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.check(), range(8)))
        self.assertEqual(sum(result.admitted for result in results), 1)

    def test_separate_devices_have_separate_replay_namespaces(self):
        self.assertTrue(self.check().admitted)
        other_key = b"another-independent-device-key-32-bytes"
        other = self.command()
        other = replace(other, signature=sign(other, other_key))
        self.assertTrue(self.check(other, device_id="pixel-two", device_key=other_key).admitted)

    def test_database_unavailable_fails_closed(self):
        self.ledger.path = os.path.join(self.temp.name, "missing", "db.sqlite")
        self.assertEqual(self.check().reason, "LEDGER_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
