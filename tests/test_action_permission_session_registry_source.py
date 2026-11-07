from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "android/app/src/main/java/tech/mrnothing/os/ActionPermissionSessionRegistry.kt"
MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"
ROUTER = ROOT / "android/app/src/main/java/tech/mrnothing/os/CommandRouter.kt"


class ActionPermissionSessionRegistrySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = REGISTRY.read_text(encoding="utf-8")
        cls.manifest = MANIFEST.read_text(encoding="utf-8")
        cls.router = ROUTER.read_text(encoding="utf-8")

    def test_registry_is_pure_kotlin_without_android_framework_imports(self):
        self.assertNotIn("import android.", self.source)
        self.assertNotIn("android.content", self.source)

    def test_registry_has_no_device_side_effect_or_dispatch_api(self):
        for forbidden in (
            "startActivity(", "requestPermissions(", "performGlobalAction(",
            "dispatchGesture(", "getMediaProjection(", "createScreenCaptureIntent(",
            "ProcessBuilder(", "Runtime.getRuntime(", "subprocess",
        ):
            self.assertNotIn(forbidden, self.source)

    def test_session_leases_are_not_persisted_or_restored(self):
        for forbidden in (
            "SharedPreferences", "DataStore", "SQLiteDatabase", "RoomDatabase",
            "serializeLease", "restoreLease",
        ):
            self.assertNotIn(forbidden, self.source)

    def test_no_accessibility_or_projection_service_is_declared(self):
        self.assertNotIn("OwnerScreenControlAccessibilityService", self.manifest)
        self.assertNotIn("MediaProjection", self.manifest)
        self.assertNotIn("FOREGROUND_SERVICE_MEDIA_PROJECTION", self.manifest)

    def test_command_router_remains_fail_closed_and_unconnected(self):
        self.assertIn("VERIFIED_TRANSPORT_SESSION_REQUIRED", self.router)
        self.assertNotIn("ActionPermissionSessionRegistry", self.router)
        self.assertNotIn("ActionPermissionGate(", self.router)


if __name__ == "__main__":
    unittest.main()
