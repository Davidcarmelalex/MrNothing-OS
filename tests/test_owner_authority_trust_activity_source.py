"""SEC-020B2 source gates; these are not Android runtime or StrongBox tests."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"
A = "{http://schemas.android.com/apk/res/android}"


class OwnerAuthorityTrustActivitySourceTests(unittest.TestCase):
    def test_activity_is_private_and_has_no_intent_filter(self):
        app = ET.parse(MANIFEST).getroot().find("application")
        matches = [item for item in app.findall("activity")
                   if item.get(A + "name") == ".OwnerAuthorityTrustActivity"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get(A + "exported"), "false")
        self.assertFalse(matches[0].findall("intent-filter"))

    def test_explicit_launcher_entry_exists(self):
        main = (SRC / "MainActivity.kt").read_text()
        self.assertIn('addAction(root, "Offline authority trust"', main)

    def test_fresh_system_credential_and_safety_recheck(self):
        code = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("createConfirmDeviceCredentialIntent", code)
        self.assertGreaterEqual(code.count("OwnerCredentialSafetyGate.isSafe(this)"), 2)
        self.assertIn("confirmation.finish(expectedBinding, credentialApproved)", code)

    def test_store_commit_follows_credential_and_state_revalidation(self):
        code = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        finish = code.index("confirmation.finish(expectedBinding, credentialApproved)")
        inspect = code.index("store.inspect()", finish)
        commit = code.index("store.commit(decision)", inspect)
        self.assertLess(finish, inspect)
        self.assertLess(inspect, commit)

    def test_out_of_band_fingerprint_attestation_is_required(self):
        code = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("independentFingerprintConfirmed.isChecked", code)
        self.assertIn("separate trusted channel", code)
        self.assertIn("FINGERPRINT_MISMATCH", (SRC / "AuthorityTrustImport.kt").read_text())

    def test_sensitive_ui_is_obscured_touch_and_screenshot_hardened(self):
        code = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("FLAG_SECURE", code)
        self.assertIn("filterTouchesWhenObscured = true", code)
        self.assertIn("OwnerConsentTouchGate.isUnobscured", code)

    def test_no_permissions_network_or_agent_execution(self):
        for name in ("OwnerAuthorityTrustActivity.kt", "AuthorityTrustImport.kt"):
            code = (SRC / name).read_text()
            for forbidden in (
                "requestPermissions(", "CommandRouter(", "startForegroundService(",
                "MediaProjectionManager", "AccessibilityService", "ProcessBuilder(",
                "Runtime.getRuntime(", "HttpURLConnection", "Socket("
            ):
                self.assertNotIn(forbidden, code)

    def test_manifest_has_no_new_permissions(self):
        root = ET.parse(MANIFEST).getroot()
        permissions = [node.get(A + "name") for node in root.findall("uses-permission")]
        self.assertEqual(permissions, ["android.permission.USE_BIOMETRIC"])


if __name__ == "__main__":
    unittest.main()
