"""SEC-014C source-only trust boundary tests, not Android runtime proof."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"
A = "{http://schemas.android.com/apk/res/android}"


class OwnerConsentPreviewTests(unittest.TestCase):
    def test_nonexported(self):
        app = ET.parse(MANIFEST).getroot().find("application")
        matches = [a for a in app.findall("activity")
                   if a.get(A + "name") == ".OwnerConsentPreviewActivity"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get(A + "exported"), "false")
        self.assertFalse(matches[0].findall("intent-filter"))

    def test_credential_and_revoke(self):
        content = (SRC / "OwnerConsentPreviewActivity.kt").read_text()
        for marker in ("isDeviceSecure", "createConfirmDeviceCredentialIntent",
                       "startActivityForResult", "RESULT_OK", "state.finish",
                       "state.revoke", "onDestroy"):
            self.assertIn(marker, content)
        for forbidden in ("CommandRouter(", "ConsentCapability(",
                          "MediaProjectionManager", "AccessibilityService"):
            self.assertNotIn(forbidden, content)

    def test_no_executor_and_only_reviewed_biometric_permission(self):
        root = ET.parse(MANIFEST).getroot()
        permissions = [
            node.get(A + "name") for node in root.findall("uses-permission")
        ]
        self.assertEqual(permissions, ["android.permission.USE_BIOMETRIC"])
        self.assertFalse(root.findall("uses-permission-sdk-23"))
        router = (SRC / "CommandRouter.kt").read_text()
        self.assertNotIn("OwnerConsentPreviewActivity", router)
        self.assertNotIn("ConsentPreviewState", router)


if __name__ == "__main__":
    unittest.main()
