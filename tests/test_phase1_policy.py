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

    def test_payment_requires_approval(self):
        self.assertEqual(authorize(Request("transfer_money", True)), Decision.APPROVAL)


if __name__ == "__main__":
    unittest.main()
