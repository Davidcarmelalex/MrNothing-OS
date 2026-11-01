import unittest
from dataclasses import replace
from core.command_security import SignedCommand, ReplayGuard, sign

KEY = b"x" * 32

class CommandSecurityTests(unittest.TestCase):
    def make(self, issued=1000):
        cmd = SignedCommand("request-1", issued, "get_battery", {}, "")
        return replace(cmd, signature=sign(cmd, KEY))

    def test_valid_signature(self):
        self.assertTrue(ReplayGuard().verify(self.make(), KEY, now=1001))
    def test_replay_rejected(self):
        guard = ReplayGuard()
        self.assertTrue(guard.verify(self.make(), KEY, now=1001))
        self.assertFalse(guard.verify(self.make(), KEY, now=1002))
    def test_wrong_key(self):
        self.assertFalse(ReplayGuard().verify(self.make(), b"y" * 32, now=1001))
    def test_expired(self):
        self.assertFalse(ReplayGuard().verify(self.make(), KEY, now=2000))
    def test_future(self):
        self.assertFalse(ReplayGuard().verify(self.make(2000), KEY, now=1000))
    def test_modified_payload(self):
        cmd = replace(self.make(), action="root_shell")
        self.assertFalse(ReplayGuard().verify(cmd, KEY, now=1001))
    def test_short_key(self):
        self.assertFalse(ReplayGuard().verify(self.make(), b"x", now=1001))

if __name__ == "__main__":
    unittest.main()
