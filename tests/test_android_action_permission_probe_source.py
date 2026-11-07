import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANDROID = (ROOT / "android/app/src/main/java/tech/mrnothing/os/AndroidActionPermissionProbe.kt").read_text(encoding="utf-8")
GATE = (ROOT / "android/app/src/main/java/tech/mrnothing/os/ActionPermissionGate.kt").read_text(encoding="utf-8")
MANIFEST = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
ROUTER = (ROOT / "android/app/src/main/java/tech/mrnothing/os/CommandRouter.kt").read_text(encoding="utf-8")


class AndroidActionPermissionProbeSourceTests(unittest.TestCase):
    def test_navigation_is_exact_package_scoped_and_read_only(self):
        self.assertIn("getLaunchIntentForPackage(packageName)", ANDROID)
        self.assertIn("component.packageName != packageName", ANDROID)
        self.assertIn("getActivityInfo(component, 0)", ANDROID)
        self.assertIn("activity.exported && activity.enabled && activity.applicationInfo.enabled", ANDROID)
        self.assertIn("checkPermission(requiredPermission, appContext.packageName)", ANDROID)
        self.assertNotIn("QUERY_ALL_PACKAGES", MANIFEST)

    def test_scroll_requires_enabled_and_connected_service(self):
        self.assertIn("ScreenActionPreflight.isOwnAccessibilityServiceEnabled(appContext)", ANDROID)
        self.assertIn("accessibilityConnectionProbe.isConnected(appContext.packageName)", ANDROID)
        self.assertIn("AccessibilityServiceConnectionProbe { false }", ANDROID)

    def test_screen_read_requires_app_owned_projection_session_default_deny(self):
        self.assertIn("projectionSessionProbe.isActive(appContext.packageName)", ANDROID)
        self.assertIn("UserApprovedProjectionSessionProbe { false }", ANDROID)

    def test_probe_has_no_permission_prompt_or_device_side_effect(self):
        for forbidden in (
            "startActivity(",
            "requestPermissions(",
            "createScreenCaptureIntent(",
            "getMediaProjection(",
            "performGlobalAction(",
            "dispatchGesture("
        ):
            self.assertNotIn(forbidden, ANDROID)

    def test_gate_result_is_not_named_or_used_as_authorization(self):
        self.assertIn("PlatformPrerequisitesPresent", GATE)
        self.assertIn("not authentication, owner consent, authorization", GATE)
        self.assertIn('CommandResult.Rejected("VERIFIED_TRANSPORT_SESSION_REQUIRED")', ROUTER)
        self.assertNotIn("ActionPermissionGate(", ROUTER)

    def test_no_new_sensitive_manifest_permissions_or_services(self):
        for forbidden in (
            "QUERY_ALL_PACKAGES",
            "BIND_ACCESSIBILITY_SERVICE",
            "FOREGROUND_SERVICE_MEDIA_PROJECTION",
            "CAPTURE_VIDEO_OUTPUT"
        ):
            self.assertNotIn(forbidden, MANIFEST)


if __name__ == "__main__":
    unittest.main()
