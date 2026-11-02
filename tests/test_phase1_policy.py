import unittest
from core.phase1_policy import Decision, Request, authorize


class PolicyTests(unittest.TestCase):
    def test_unauthenticated_denied(self):
        self.assertEqual(authorize(Request("open_app", False)), Decision.DENY)

    def test_low_risk_authenticated(self):
        self.assertEqual(authorize(Request("get_battery", True)), Decision.ALLOW)

    def test_unknown_action_denied(self):
        self.assertEqual(authorize(Request("root_shell", True)), Decision.DENY)

    def test_unapproved_contact_requires_approval(self):
        self.assertEqual(authorize(Request("place_call", True)), Decision.APPROVAL)

    def test_approved_contact(self):
        self.assertEqual(authorize(Request("place_call", True, True)), Decision.ALLOW)

    def test_screen_actions_always_require_explicit_owner_approval(self):
        for action in ("read_screen", "navigate", "scroll"):
            with self.subTest(action=action):
                self.assertEqual(authorize(Request(action, True)), Decision.APPROVAL)

    def test_screen_actions_deny_unauthenticated(self):
        for action in ("read_screen", "navigate", "scroll"):
            with self.subTest(action=action):
                self.assertEqual(authorize(Request(action, False)), Decision.DENY)

    def test_contact_approval_cannot_be_reused_as_screen_consent(self):
        for action in ("read_screen", "navigate", "scroll"):
            with self.subTest(action=action):
                self.assertEqual(authorize(Request(action, True, contact_approved=True)), Decision.APPROVAL)

    def test_screen_approval_cannot_be_forged_in_request(self):
        with self.assertRaises(TypeError):
            Request("read_screen", True, screen_approved=True)

    def test_payment_requires_approval(self):
        self.assertEqual(authorize(Request("transfer_money", True)), Decision.APPROVAL)


if __name__ == "__main__":
    unittest.main()
