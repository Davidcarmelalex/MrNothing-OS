"""AGENT-004L owner disclosure and Settings-handoff source boundaries."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"
ANDROID = "{http://schemas.android.com/apk/res/android}"


class AccessibilityDisclosureSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest_text = MANIFEST.read_text(encoding="utf-8")
        cls.activity = (SRC / "AccessibilityDisclosureActivity.kt").read_text(encoding="utf-8")
        cls.state = (SRC / "AccessibilityDisclosureState.kt").read_text(encoding="utf-8")
        cls.probe = (SRC / "AndroidAccessibilityDisclosureProbe.kt").read_text(encoding="utf-8")
        cls.main = (SRC / "MainActivity.kt").read_text(encoding="utf-8")
        cls.preflight = (SRC / "ScreenActionPreflight.kt").read_text(encoding="utf-8")
        cls.router = (SRC / "CommandRouter.kt").read_text(encoding="utf-8")

    def test_disclosure_activity_is_private_and_not_a_service(self):
        root = ET.fromstring(self.manifest_text)
        app = root.find("application")
        matches = [item for item in app.findall("activity")
                   if item.get(ANDROID + "name") == ".AccessibilityDisclosureActivity"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get(ANDROID + "exported"), "false")
        self.assertFalse(matches[0].findall("intent-filter"))
        self.assertFalse(app.findall("service"))

    def test_no_accessibility_or_projection_permission_is_added(self):
        for forbidden in (
            "android.accessibilityservice.AccessibilityService",
            "android.permission.BIND_ACCESSIBILITY_SERVICE",
            "android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION",
            "android.permission.SYSTEM_ALERT_WINDOW",
            "android.permission.CAPTURE_VIDEO_OUTPUT",
        ):
            self.assertNotIn(forbidden, self.manifest_text)

    def test_settings_handoff_is_explicit_and_never_enables_a_service(self):
        self.assertIn("Settings.ACTION_ACCESSIBILITY_SETTINGS", self.activity)
        self.assertIn("setOnClickListener { action() }", self.activity)
        self.assertIn("openAccessibilitySettings()", self.activity)
        self.assertNotIn("Settings.Secure.putString", self.activity)
        self.assertNotIn("setEnabledAccessibilityServices", self.activity)
        self.assertNotIn("requestPermissions(", self.activity)
        self.assertNotIn("startService(", self.activity)

    def test_status_reader_is_exact_component_scoped_and_fail_closed(self):
        self.assertIn('COMPONENT_CLASS_NAME = "tech.mrnothing.os.OwnerScreenControlAccessibilityService"', self.state)
        self.assertIn("AccessibilityServiceContract.COMPONENT_CLASS_NAME", self.probe)
        self.assertIn("if (!probe.isDeclared())", self.state)
        self.assertIn("AccessibilityDisclosureStatus.UNAVAILABLE", self.state)
        self.assertIn("catch (_: SecurityException)", self.state)
        self.assertIn("catch (_: RuntimeException)", self.state)
        self.assertIn("service.packageName == appContext.packageName", self.probe)
        self.assertIn("info.packageName == appContext.packageName", self.probe)
        self.assertIn("info.name == AccessibilityServiceContract.COMPONENT_CLASS_NAME", self.probe)

    def test_disclosure_is_owner_visible_and_accessible(self):
        for required in (
            "No accessibility service is registered in this build.",
            "cannot read your screen or control other apps through Accessibility",
            "Android Settings is the only place to enable or disable",
            "filterTouchesWhenObscured = true",
            "OwnerConsentTouchGate.isUnobscured",
            "minHeight = dp(56)",
            "accessibilityLiveRegion",
            "override fun onResume()",
        ):
            self.assertIn(required, self.activity)

    def test_launcher_exposes_disclosure_and_revocation_handoff(self):
        self.assertIn("AccessibilityDisclosureActivity::class.java", self.main)
        self.assertIn("Accessibility access & revocation", self.main)

    def test_instrumentation_enters_private_disclosure_through_owner_visible_launcher_route(self):
        instrumentation = (ROOT / "android/app/src/androidTest/java/tech/mrnothing/os/AccessibilityDisclosureActivityTest.kt").read_text(encoding="utf-8")
        self.assertIn("MainActivity::class.java", instrumentation)
        self.assertIn("Accessibility access & revocation", instrumentation)
        self.assertIn("ActivityMonitor(\n            AccessibilityDisclosureActivity::class.java.name", instrumentation)
        self.assertIn("waitForActivityWithTimeout", instrumentation)
        self.assertNotIn("Intent(getInstrumentation().targetContext, AccessibilityDisclosureActivity::class.java)", instrumentation)

    def test_existing_preflight_uses_the_same_service_identity(self):
        self.assertIn(
            "private const val OWN_SERVICE = AccessibilityServiceContract.COMPONENT_CLASS_NAME",
            self.preflight,
        )

    def test_command_router_remains_disconnected(self):
        self.assertIn("VERIFIED_TRANSPORT_SESSION_REQUIRED", self.router)
        self.assertNotIn("AccessibilityDisclosureActivity", self.router)
        self.assertNotIn("AccessibilityDisclosureReader", self.router)


if __name__ == "__main__":
    unittest.main()
