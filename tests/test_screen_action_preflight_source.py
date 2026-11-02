"""SEC-014F source boundaries; runtime Android permission tests remain open."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"


class ScreenPreflightSourceTests(unittest.TestCase):
    def test_reads_only_own_enabled_accessibility_service(self):
        code = (SRC / "ScreenActionPreflight.kt").read_text()
        for token in (
            "AccessibilityManager::class.java",
            "getEnabledAccessibilityServiceList",
            "AccessibilityServiceInfo.FEEDBACK_ALL_MASK",
            "info.packageName == context.packageName",
            "info.name == OWN_SERVICE",
            "catch (_: RuntimeException)",
            "catch (_: SecurityException)",
        ):
            self.assertIn(token, code)

    def test_no_accessibility_service_or_projection_grant_declared(self):
        manifest = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text()
        self.assertNotIn("android.accessibilityservice.AccessibilityService", manifest)
        self.assertNotIn("android.permission.BIND_ACCESSIBILITY_SERVICE", manifest)
        self.assertNotIn("android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION", manifest)
        self.assertNotIn("android.permission.SYSTEM_ALERT_WINDOW", manifest)

    def test_agent_policy_and_router_remain_nonexecuting(self):
        policy = (SRC / "AgentPolicy.kt").read_text()
        router = (SRC / "CommandRouter.kt").read_text()
        self.assertIn("action.name in screenActions -> Verdict.APPROVAL_REQUIRED", policy)
        for name in ("read_screen", "navigate", "scroll"):
            self.assertNotIn('"' + name + '"', router)

    def test_preflight_does_not_issue_capabilities_or_request_permissions(self):
        code = (SRC / "ScreenActionPreflight.kt").read_text()
        for forbidden in (
            "startActivityForResult", "requestPermissions(",
            "MediaProjectionManager", "createScreenCaptureIntent",
            "ConsentCapability(", "CommandRouter(", "KeyStore.getInstance",
            "Settings.Secure.put", "setEnabledAccessibilityServices",
        ):
            self.assertNotIn(forbidden, code)


if __name__ == "__main__":
    unittest.main()
