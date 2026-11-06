"""SEC-020B4D source gates for debug-only trust commit lifecycle instrumentation."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "android/app/src/main"
DEBUG = ROOT / "android/app/src/debug"
TEST = ROOT / "android/app/src/androidTest/java/tech/mrnothing/os/OwnerAuthorityTrustActivityCommitLifecycleTest.kt"
ANDROID = "{http://schemas.android.com/apk/res/android}"


class Sec020B4DLifecycleInstrumentationTests(unittest.TestCase):
    def test_fake_host_is_non_exported_debug_only(self):
        main_app = ET.parse(MAIN / "AndroidManifest.xml").getroot().find("application")
        debug_app = ET.parse(DEBUG / "AndroidManifest.xml").getroot().find("application")
        self.assertNotIn(
            ".OwnerAuthorityTrustActivityTestHost",
            [n.get(ANDROID + "name") for n in main_app.findall("activity")],
        )
        hosts = [n for n in debug_app.findall("activity")
                 if n.get(ANDROID + "name") == ".OwnerAuthorityTrustActivityTestHost"]
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0].get(ANDROID + "exported"), "false")
        self.assertIsNone(hosts[0].get(ANDROID + "permission"))

    def test_test_covers_both_sides_of_commit_claim(self):
        source = TEST.read_text(encoding="utf-8")
        activity = (MAIN / "java/tech/mrnothing/os/OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("testDestroyBeforeCommitClaimPreventsFakeStoreMutation", source)
        self.assertIn("testDestroyAfterCommitClaimAllowsAtomicFakeCommitButSuppressesUiDelivery", source)
        self.assertIn("operationGate.claimCommit(token)", activity)
        self.assertIn("gate.isDeliverable", source)
        self.assertIn("onActivityDestroyed", source)

    def test_fake_backend_is_memory_only_and_uses_synthetic_credential(self):
        source = TEST.read_text(encoding="utf-8")
        self.assertIn("BlockingFakeTrustStore", source)
        self.assertIn("RFC 8032 test vector 1 public key", source)
        self.assertIn("Base64.getDecoder().decode(", source)
        self.assertNotIn("KeyPairGenerator", source)
        self.assertNotIn("generateKeyPair()", source)
        self.assertNotIn("locksettings set-pin", source)
        self.assertNotIn("locksettings clear --old", source)
        self.assertIn("rootInActiveWindow", source)
        self.assertIn("automation.windows", source)
        self.assertIn("com.android.systemui:id/auth_credential_input", source)
        self.assertIn("com.android.systemui:id/lockPassword", source)
        self.assertIn('setOf("com.android.systemui", "com.android.settings")', source)
        self.assertIn("isVisibleToUser", source)
        self.assertIn("awaitCredentialRevalidation(target)", source)
        self.assertIn("findAccessibilityNodeInfosByViewId", source)
        self.assertNotIn("uiautomator dump", source)
        for forbidden in ("AndroidOwnerAuthorityTrustStore(", "AndroidAuthorityTrustCrypto(",
                          "AndroidAtomicAuthorityRecordPersistence(", "fastboot", "adb root",
                          "ProcessBuilder(", "Runtime.getRuntime(", "CommandRouter(",
                          "requestPermissions(", "store.commit(real"):
            self.assertNotIn(forbidden, source)


    def test_android_15_systemui_keyguard_fields_use_exact_view_classes(self):
        source = TEST.read_text(encoding="utf-8")
        self.assertIn(
            '"com.android.systemui:id/pinEntry" to "com.android.keyguard.PasswordTextView"',
            source,
        )
        self.assertIn(
            '"com.android.systemui:id/passwordEntry" to "android.widget.EditText"',
            source,
        )
        self.assertIn("it.className?.toString() == expectedClassName", source)
        self.assertIn("root.packageName?.toString() !in allowedPackages", source)
        self.assertNotIn(
            'it.className?.toString() == "android.widget.EditText"',
            source,
        )

    def test_locked_keyguard_reveals_system_pin_with_unprivileged_shell_swipe(self):
        source = TEST.read_text(encoding="utf-8")
        prepare_start = source.index("private fun prepareInteractiveUnlockedEmulator()")
        swipe_start = source.index("private fun swipeUpToRevealSystemCredentialEntry()", prepare_start)
        prompt_start = source.index("private fun awaitCredentialPrompt", swipe_start)
        prepare = source[prepare_start:swipe_start]
        swipe = source[swipe_start:prompt_start]

        self.assertIn('shell("input keyevent KEYCODE_WAKEUP")', prepare)
        self.assertIn("keyguard.isDeviceLocked || keyguard.isKeyguardLocked", prepare)
        self.assertIn("if (!hasVisibleSystemCredentialInput())", prepare)
        self.assertIn("swipeUpToRevealSystemCredentialEntry()", prepare)
        self.assertLess(prepare.index("swipeUpToRevealSystemCredentialEntry()"),
                        prepare.index("awaitSystemCredentialUi"))
        self.assertLess(prepare.index("awaitSystemCredentialUi"),
                        prepare.index('shell("input text $TEST_PIN")'))

        self.assertIn("resources.displayMetrics", swipe)
        self.assertIn("widthPixels", swipe)
        self.assertIn("heightPixels", swipe)
        self.assertIn('shell("id")', swipe)
        self.assertIn('"uid=2000(shell)"', swipe)
        self.assertIn('val command = "input swipe $centerX $startY $centerX $endY 300"', swipe)
        self.assertIn("val result = shell(command)", swipe)
        self.assertNotIn("MotionEvent", source)
        self.assertNotIn("requestDismissKeyguard", source)
        self.assertNotIn("wm dismiss-keyguard", source)
        self.assertNotIn("KEYCODE_MENU", source)
        self.assertNotIn("adb root", source)

    def test_missing_credential_ui_failure_captures_bounded_window_evidence(self):
        source = TEST.read_text(encoding="utf-8")
        self.assertIn("private fun credentialUiSnapshot()", source)
        self.assertIn("automation.windows", source)
        self.assertIn("rootInActiveWindow", source)
        self.assertIn("java.util.ArrayDeque<Pair<AccessibilityNodeInfo, Int>>", source)
        self.assertIn("visited < 96", source)
        self.assertIn("take(14_000)", source)
        self.assertIn("node.recycle()", source)
        self.assertIn("viewIdResourceName", source)
        self.assertIn("getBoundsInScreen", source)
        self.assertIn("takeScreenshot()", source)
        self.assertIn("qa005-credential-ui.png", source)
        self.assertIn("captureCredentialUiScreenshot()", source)
        self.assertIn('shell("dumpsys window windows")', source)
        self.assertIn("lastCredentialPreflightDiagnostics", source)
        self.assertIn("ui=${credentialUiSnapshot()}", source)

    def test_activity_default_factory_remains_android_backend(self):
        source = (MAIN / "java/tech/mrnothing/os/OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("internal open fun createTrustStore(context: Context)", source)
        self.assertIn("AndroidOwnerAuthorityTrustStore(context)", source)
        self.assertEqual(source.count("createTrustStore(appContext)"), 3)

    def test_emulator_preflight_wakes_and_uses_only_visible_systemui_credential(self):
        source = TEST.read_text(encoding="utf-8")
        self.assertIn("prepareInteractiveUnlockedEmulator()", source)
        self.assertIn('shell("input keyevent KEYCODE_WAKEUP")', source)
        self.assertIn("keyguard.isDeviceLocked || keyguard.isKeyguardLocked", source)
        self.assertIn("awaitSystemCredentialUi", source)
        self.assertIn('shell("input text $TEST_PIN")', source)
        self.assertIn("OwnerCredentialSafetyGate.isSafe(context)", source)
        self.assertIn("deviceCredentialCanAuthenticate", source)
        self.assertNotIn("wm dismiss-keyguard", source)
        self.assertNotIn("adb root", source)


if __name__ == "__main__":
    unittest.main()
