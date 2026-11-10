"""UX-AGENT-001: offline launcher sample preview source-only safety gates."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
A = "{http://schemas.android.com/apk/res/android}"


class AgentPlanPreviewSourceTests(unittest.TestCase):
    def test_activity_is_not_exported_and_has_no_intent_filter(self):
        app = ET.parse(ROOT / "android/app/src/main/AndroidManifest.xml").getroot().find("application")
        entries = [a for a in app.findall("activity")
                   if a.get(A + "name") == ".AgentPlanPreviewActivity"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].get(A + "exported"), "false")
        self.assertFalse(entries[0].findall("intent-filter"))

    def test_launcher_offers_explicit_owner_open_only(self):
        source = (SRC / "MainActivity.kt").read_text()
        self.assertIn('"Offline agent plan preview"', source)
        self.assertIn("startActivity(Intent(this, AgentPlanPreviewActivity::class.java))", source)

    def test_preview_has_no_device_effect_or_authentication_api(self):
        activity = (SRC / "AgentPlanPreviewActivity.kt").read_text()
        policy = (SRC / "AgentPlanPreview.kt").read_text()
        for forbidden in (
            "CommandRouter", "AppCatalog.launch", "DeviceDiagnostics.snapshot",
            "OwnerConsentSigner", "OwnerConsentTlsAdapter", "ProcessBuilder",
            "Runtime.getRuntime", "startActivity(", "AccessibilityService",
            "MediaProjectionManager", "HttpURLConnection", "Socket(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, activity + policy)
        self.assertIn("AgentPolicy.classify", policy)
        self.assertIn("val deviceActionsExecuted: Boolean get() = false", policy)
        self.assertIn("val authorized: Boolean get() = false", policy)
        self.assertIn("onStop()", activity)
        self.assertIn("Preview only.", activity)


if __name__ == "__main__":
    unittest.main()
