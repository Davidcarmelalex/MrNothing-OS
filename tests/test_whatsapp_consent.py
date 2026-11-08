import inspect
import unittest
from unittest.mock import Mock, patch

from modules.whatsapp import whatsapp as wa


class WhatsAppConsentTests(unittest.TestCase):
    def setUp(self):
        self.run_patch = patch.object(wa.subprocess, "run")
        self.run = self.run_patch.start()
        self.run.return_value = Mock(returncode=0)
        self.log_patch = patch.object(wa, "log")
        self.log = self.log_patch.start()

    def tearDown(self):
        self.log_patch.stop()
        self.run_patch.stop()

    def test_phone_parser_accepts_bounded_international_style_numbers(self):
        self.assertEqual(wa._normalize_phone("+919876543210"), "+919876543210")
        self.assertEqual(wa._normalize_phone("919876543210"), "919876543210")
        for value in ("", "-n", "https://example.com", "123", "123456789012345678", "+0123456789", None, 7):
            with self.subTest(value=value):
                self.assertIsNone(wa._normalize_phone(value))

    def test_sms_confirmation_challenge_binds_recipient_and_exact_message(self):
        first = wa._sms_confirmation_challenge("+919876543210", "Hello")
        self.assertTrue(first.startswith("SEND SMS "))
        self.assertNotEqual(first, wa._sms_confirmation_challenge("+919876543211", "Hello"))
        self.assertNotEqual(first, wa._sms_confirmation_challenge("+919876543210", "Hello!"))

    def test_sms_requires_internal_exact_confirmation_before_subprocess(self):
        phone = "+919876543210"
        message = "Please call me."
        challenge = wa._sms_confirmation_challenge(phone, message)
        with patch.object(wa, "_has_termux", return_value=True), patch("builtins.input", return_value=challenge):
            self.assertTrue(wa.send_sms(phone, message))
        self.run.assert_called_once_with(
            ["termux-sms-send", "-n", phone, message],
            timeout=10,
            check=True,
            shell=False,
        )

    def test_sms_decline_causes_no_subprocess(self):
        with patch.object(wa, "_has_termux", return_value=True), patch("builtins.input", return_value="NO"):
            self.assertFalse(wa.send_sms("+919876543210", "Hello"))
        self.run.assert_not_called()

    def test_sms_eof_or_interrupt_fails_closed(self):
        for error in (EOFError(), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                with patch.object(wa, "_has_termux", return_value=True), patch("builtins.input", side_effect=error):
                    self.assertFalse(wa.send_sms("+919876543210", "Hello"))
        self.run.assert_not_called()

    def test_sms_without_termux_api_does_not_prompt_or_spawn(self):
        with patch.object(wa, "_has_termux", return_value=False), patch("builtins.input") as prompt:
            self.assertFalse(wa.send_sms("+919876543210", "Hello"))
        prompt.assert_not_called()
        self.run.assert_not_called()

    def test_sms_rejects_invalid_recipient_empty_oversized_and_nul_messages(self):
        with patch.object(wa, "_has_termux", return_value=True), patch("builtins.input") as prompt:
            self.assertFalse(wa.send_sms("-n", "Hello"))
            self.assertFalse(wa.send_sms("+919876543210", ""))
            self.assertFalse(wa.send_sms("+919876543210", "x" * (wa.MAX_SMS_CHARS + 1)))
            self.assertFalse(wa.send_sms("+919876543210", "bad\x00message"))
        prompt.assert_not_called()
        self.run.assert_not_called()

    def test_sms_api_has_no_injectable_confirmation_callback(self):
        self.assertEqual(list(inspect.signature(wa.send_sms).parameters), ["phone", "message"])
        self.assertEqual(list(inspect.signature(wa._confirm_sms_send).parameters), ["phone", "message"])

    def test_whatsapp_opens_encoded_compose_link_without_claiming_delivery(self):
        phone = "+919876543210"
        message = "hello & goodbye?"
        with patch.object(wa, "log") as log:
            self.assertTrue(wa.send_message(phone, message))
        args, kwargs = self.run.call_args
        self.assertEqual(args[0], ["termux-open-url", "https://wa.me/919876543210?text=hello%20%26%20goodbye%3F"])
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["timeout"], 10)
        self.assertIs(kwargs["check"], True)
        self.assertIn("owner must review and tap Send", log.call_args.args[0])

    def test_whatsapp_invalid_input_causes_no_external_open(self):
        self.assertFalse(wa.send_message("https://example.com", "Hello"))
        self.assertFalse(wa.send_message("+919876543210", "bad\x00message"))
        self.run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
