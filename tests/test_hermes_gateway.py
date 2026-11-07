import unittest
from core.hermes_gateway import CommandEnvelope, validate

class HermesGatewayTests(unittest.TestCase):
    def test_reject_unauthenticated(self):
        self.assertFalse(validate(CommandEnvelope("1", "get_battery", {}), authenticated=False).accepted)
    def test_accept_battery(self):
        self.assertTrue(validate(CommandEnvelope("2", "get_battery", {}), authenticated=True).accepted)
    def test_reject_shell(self):
        self.assertFalse(validate(CommandEnvelope("3", "root_shell", {}), authenticated=True).accepted)
    def test_reject_invalid_package(self):
        self.assertFalse(validate(CommandEnvelope("4", "open_app", {"packageName": "com.example;rm"}), authenticated=True).accepted)
    def test_accept_package(self):
        self.assertTrue(validate(CommandEnvelope("5", "open_app", {"packageName": "com.android.settings"}), authenticated=True).accepted)
    def test_reject_empty_id(self):
        self.assertFalse(validate(CommandEnvelope("", "get_battery", {}), authenticated=True).accepted)

if __name__ == "__main__":
    unittest.main()
