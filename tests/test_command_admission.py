import os
import sqlite3
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
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
