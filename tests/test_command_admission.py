import os
import sqlite3
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
        with patch("core.command_admission.os.stat", return_value=fake_stat):
            self.assertFalse(ledger._parent_is_safe())

    @unittest.skipUnless(os.name == "posix", "POSIX directory permissions")
    def test_sticky_world_writable_parent_is_supported(self):
        parent = os.path.join(self.temp.name, "sticky")
        os.mkdir(parent, 0o700)
        os.chmod(parent, 0o1777)
        try:
            ledger = DurableReplayLedger(os.path.join(parent, "ledger.sqlite"))
            self.assertTrue(ledger.reserve("pixel", "nonce", 100))
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
        with sqlite3.connect(path):
            pass
        self.assertEqual(self.check(self.command(command_id="id-2"), ledger=ledger).reason,
                         "LEDGER_UNAVAILABLE")

    @unittest.skipUnless(os.name == "posix", "POSIX file mode")
    def test_replay_file_permission_downgrade_fails_closed(self):
        ledger = DurableReplayLedger(os.path.join(self.temp.name, "downgrade.sqlite"))
        os.chmod(ledger.path, 0o644)
        self.assertEqual(self.check(ledger=ledger).reason, "LEDGER_UNAVAILABLE")

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

    def test_untrusted_transport(self):
        self.assertEqual(self.check(transport_authenticated=False).reason, "UNAUTHENTICATED")

    def test_device_key_mismatch(self):
        self.assertEqual(self.check(device_key=b"z" * 32).reason, "BAD_SIGNATURE")

    def test_tampering(self):
        self.assertEqual(self.check(replace(self.command(), action="root_shell")).reason, "BAD_SIGNATURE")

    def test_unknown_action(self):
        self.assertFalse(self.check(self.command(action="root_shell")).admitted)

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
