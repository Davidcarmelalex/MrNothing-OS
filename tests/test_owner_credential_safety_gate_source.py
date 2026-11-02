"""SEC-014D static boundary checks; Android runtime remains CI-only."""
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "android/app/src/main/java/tech/mrnothing/os"


class CredentialSafetyGateSourceTests(unittest.TestCase):
    def test_android_state_read_from_platform(self):
        gate = (SRC / "OwnerCredentialSafetyGate.kt").read_text()
        for marker in (
            "KeyguardManager::class.java", "PowerManager::class.java",
            "UserManager::class.java", "isDeviceSecure", "isDeviceLocked",
            "isKeyguardLocked", "isUserUnlocked", "isInteractive",
            "catch (_: RuntimeException)", "false",
        ):
            self.assertIn(marker, gate)

    def test_preview_checks_state_before_and_after_credential(self):
        preview = (SRC / "OwnerConsentPreviewActivity.kt").read_text()
        self.assertEqual(preview.count("OwnerCredentialSafetyGate.isSafe(this)"), 2)
        self.assertLess(
            preview.index("if (!OwnerCredentialSafetyGate.isSafe(this))"),
            preview.index("startActivityForResult(prompt, credentialRequest)"),
        )
        self.assertIn("resultCode == RESULT_OK && OwnerCredentialSafetyGate.isSafe(this)", preview)

    def test_no_new_screen_executor_or_issuer(self):
        gate = (SRC / "OwnerCredentialSafetyGate.kt").read_text()
        for forbidden in ("CommandRouter(", "ConsentCapability(", "MediaProjectionManager",
                          "AccessibilityService", "startActivityForResult"):
            self.assertNotIn(forbidden, gate)


if __name__ == "__main__":
    unittest.main()
