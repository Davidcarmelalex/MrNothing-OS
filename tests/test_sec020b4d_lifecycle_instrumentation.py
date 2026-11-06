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
        self.assertIn("android.widget.ImeAwareEditText", source)
        self.assertIn("android.widget.EditText", source)
        self.assertIn("hasVisibleBiometricPromptCredentialField", source)
        self.assertIn("hasVisibleKeyguardPinPad", source)
        self.assertIn('shell("input text $TEST_PIN")', source)
        self.assertIn('shell("input keyevent KEYCODE_ENTER")', source)
        self.assertIn('identity.contains("uid=2000(shell)")', source)
        self.assertIn("isVisibleToUser", source)
        self.assertIn("awaitCredentialRevalidation(target)", source)
        self.assertIn("findAccessibilityNodeInfosByViewId", source)
        self.assertNotIn("uiautomator dump", source)
        self.assertNotIn('com.android.systemui:id/pinEntry" to', source)
        self.assertNotIn('com.android.systemui:id/passwordEntry" to', source)
        for forbidden in ("AndroidOwnerAuthorityTrustStore(", "AndroidAuthorityTrustCrypto(",
                          "AndroidAtomicAuthorityRecordPersistence(", "fastboot", "adb root",
                          "ProcessBuilder(", "Runtime.getRuntime(", "CommandRouter(",
                          "requestPermissions(", "store.commit(real"):
            self.assertNotIn(forbidden, source)

    def test_android_15_biometric_prompt_uses_exact_systemui_ime_field(self):
        source = TEST.read_text(encoding="utf-8")
        prompt_start = source.index("private fun hasVisibleBiometricPromptCredentialField")
        keyguard_start = source.index("private fun hasVisibleSystemPinPad", prompt_start)
        prompt_gate = source[prompt_start:keyguard_start]

        self.assertIn('root.packageName?.toString() != "com.android.systemui"', prompt_gate)
        self.assertIn('val containerId = "com.android.systemui:id/auth_credential_input"', prompt_gate)
        self.assertIn('val fieldId = "com.android.systemui:id/lockPassword"', prompt_gate)
        self.assertIn('"android.widget.FrameLayout"', prompt_gate)
        self.assertIn('"android.widget.ImeAwareEditText"', prompt_gate)
        self.assertIn("container.findAccessibilityNodeInfosByViewId(fieldId)", prompt_gate)
        self.assertIn("field.isVisibleToUser", prompt_gate)
        self.assertIn("field.isEnabled", prompt_gate)
        self.assertIn("field.isFocusable", prompt_gate)
        self.assertIn("field.isFocused", prompt_gate)
        self.assertIn("field.isPassword", prompt_gate)
        self.assertIn("fields.forEach { it.recycle() }", prompt_gate)
        self.assertIn("containers.forEach { it.recycle() }", prompt_gate)
        self.assertNotIn("com.android.settings", prompt_gate)
        self.assertNotIn("pinEntry", prompt_gate)
        self.assertNotIn("key0", prompt_gate)

    def test_biometric_prompt_field_uses_narrow_runtime_class_allowlist(self):
        source = TEST.read_text(encoding="utf-8")
        prompt_start = source.index("private fun hasVisibleBiometricPromptCredentialField")
        keyguard_start = source.index("private fun hasVisibleSystemPinPad", prompt_start)
        prompt_gate = source[prompt_start:keyguard_start]

        self.assertIn('root.packageName?.toString() != "com.android.systemui"', prompt_gate)
        self.assertIn('val containerId = "com.android.systemui:id/auth_credential_input"', prompt_gate)
        self.assertIn('val fieldId = "com.android.systemui:id/lockPassword"', prompt_gate)
        self.assertIn('container.className?.toString() != "android.widget.FrameLayout"', prompt_gate)
        self.assertIn('fieldClass != "android.widget.ImeAwareEditText"', prompt_gate)
        self.assertIn('fieldClass != "android.widget.EditText"', prompt_gate)
        self.assertIn("field.viewIdResourceName != fieldId", prompt_gate)
        self.assertIn("field.isFocused", prompt_gate)
        self.assertIn("field.isPassword", prompt_gate)
        self.assertNotIn("fieldClass?.contains", prompt_gate)
        self.assertNotIn("com.android.settings", prompt_gate)

    def test_android_15_keyguard_pad_uses_exact_systemui_resource_hierarchy(self):
        source = TEST.read_text(encoding="utf-8")
        pin_start = source.index("private fun hasVisibleSystemPinPad")
        node_start = source.index("private fun hasVisibleSystemUiNode", pin_start)
        pin_pad = source[pin_start:node_start]

        self.assertIn('root.packageName?.toString() != "com.android.systemui"', pin_pad)
        self.assertIn('val pinViewId = "com.android.systemui:id/keyguard_pin_view"', pin_pad)
        self.assertIn('val containerId = "com.android.systemui:id/pin_container"', pin_pad)
        self.assertIn("pinView.findAccessibilityNodeInfosByViewId(containerId)", pin_pad)
        self.assertIn('val controlIds = (0..9).map {', pin_pad)
        self.assertIn('"com.android.systemui:id/key$it"', pin_pad)
        self.assertIn('"com.android.systemui:id/key_enter"', pin_pad)
        self.assertIn("hasVisibleSystemUiNode(", pin_pad)
        self.assertIn("requireClickable = true", pin_pad)
        self.assertNotIn("className", pin_pad)
        self.assertNotIn("KeyguardPINView", pin_pad)
        self.assertNotIn("ConstraintLayout", pin_pad)
        self.assertNotIn("NumPadKey", pin_pad)

        node_gate = source[node_start:source.index(
            "private fun awaitCredentialRevalidation", node_start
        )]
        self.assertIn("parent.findAccessibilityNodeInfosByViewId(viewId)", node_gate)
        self.assertIn('node.packageName?.toString() != "com.android.systemui"', node_gate)
        self.assertIn("node.viewIdResourceName != viewId", node_gate)
        self.assertIn("node.isVisibleToUser", node_gate)
        self.assertIn("node.isEnabled", node_gate)
        self.assertIn("node.isClickable", node_gate)
        self.assertIn("bounds.width() > 0 && bounds.height() > 0", node_gate)
        self.assertIn("matches.forEach { it.recycle() }", node_gate)
        self.assertNotIn("expectedClassName", node_gate)

    def test_locked_keyguard_taps_exact_systemui_device_entry_with_unprivileged_shell(self):
        source = TEST.read_text(encoding="utf-8")
        prepare_start = source.index("private fun prepareInteractiveUnlockedEmulator()")
        pin_helper_start = source.index("private fun enterSyntheticKeyguardPin", prepare_start)
        tap_start = source.index(
            "private fun tapSystemDeviceEntryIconToRevealCredentialEntry()", pin_helper_start
        )
        prompt_start = source.index("private fun awaitCredentialPrompt", tap_start)
        prepare = source[prepare_start:pin_helper_start]
        tap = source[tap_start:prompt_start]

        self.assertIn('shell("input keyevent KEYCODE_WAKEUP")', prepare)
        self.assertIn("keyguard.isDeviceLocked || keyguard.isKeyguardLocked", prepare)
        self.assertIn("if (!hasVisibleKeyguardPinPad())", prepare)
        self.assertIn("tapSystemDeviceEntryIconToRevealCredentialEntry()", prepare)
        self.assertLess(
            prepare.index("tapSystemDeviceEntryIconToRevealCredentialEntry()"),
            prepare.index("awaitKeyguardPinPad"),
        )
        self.assertLess(
            prepare.index("awaitKeyguardPinPad"),
            prepare.index("enterSyntheticKeyguardPin(identity)"),
        )

        self.assertIn("resources.displayMetrics", tap)
        self.assertIn("widthPixels", tap)
        self.assertIn("heightPixels", tap)
        self.assertIn('val viewId = "com.android.systemui:id/device_entry_icon_view"', tap)
        self.assertIn('root.packageName?.toString() != "com.android.systemui"', tap)
        self.assertIn("it.viewIdResourceName == viewId", tap)
        self.assertIn('it.className?.toString() == "android.widget.FrameLayout"', tap)
        self.assertIn("it.isVisibleToUser && it.isEnabled && it.isClickable", tap)
        self.assertIn("getBoundsInScreen", tap)
        self.assertIn("bounds.left >= 0 && bounds.top >= 0", tap)
        self.assertIn("bounds.right <= width && bounds.bottom <= height", tap)
        self.assertIn('shell("id")', tap)
        self.assertIn('"uid=2000(shell)"', tap)
        self.assertIn(
            'val command = "input tap ${targetBounds.centerX()} ${targetBounds.centerY()}"',
            tap,
        )
        self.assertIn("val result = shell(command)", tap)
        self.assertNotIn("input swipe", source)
        self.assertNotIn("MotionEvent", source)
        self.assertNotIn("requestDismissKeyguard", source)
        self.assertNotIn("wm dismiss-keyguard", source)
        self.assertNotIn("KEYCODE_MENU", source)
        self.assertNotIn("adb root", source)

    def test_synthetic_keyguard_pin_entry_uses_exact_systemui_hierarchy_controls(self):
        source = TEST.read_text(encoding="utf-8")
        pin_start = source.index("private fun enterSyntheticKeyguardPin")
        biometric_start = source.index("private fun enterSyntheticBiometricPromptPin", pin_start)
        tap_start = source.index("private fun tapVisibleSystemUiNode", biometric_start)
        device_entry_start = source.index(
            "private fun tapSystemDeviceEntryIconToRevealCredentialEntry", tap_start
        )
        keyguard_helper = source[pin_start:biometric_start]
        node_tap = source[tap_start:device_entry_start]

        self.assertIn('identity.contains("uid=2000(shell)")', keyguard_helper)
        self.assertIn("hasVisibleKeyguardPinPad()", keyguard_helper)
        self.assertIn("for (digit in TEST_PIN)", keyguard_helper)
        self.assertIn('com.android.systemui:id/key$digit', keyguard_helper)
        self.assertIn("tapVisibleSystemUiNode(viewId)", keyguard_helper)
        self.assertIn('tapVisibleSystemUiNode("com.android.systemui:id/key_enter")', keyguard_helper)
        self.assertNotIn("NumPadKey", keyguard_helper)
        self.assertNotIn("NumPadButton", keyguard_helper)

        self.assertIn("val allowedViewIds = (0..9).map", node_tap)
        self.assertIn('"com.android.systemui:id/key_enter"', node_tap)
        self.assertIn('root.packageName?.toString() != "com.android.systemui"', node_tap)
        self.assertIn('val pinViewId = "com.android.systemui:id/keyguard_pin_view"', node_tap)
        self.assertIn('val containerId = "com.android.systemui:id/pin_container"', node_tap)
        self.assertIn("pinView.findAccessibilityNodeInfosByViewId(containerId)", node_tap)
        self.assertIn("container.findAccessibilityNodeInfosByViewId(viewId)", node_tap)
        self.assertIn("node.viewIdResourceName != viewId", node_tap)
        self.assertIn("!node.isVisibleToUser", node_tap)
        self.assertIn("!node.isEnabled", node_tap)
        self.assertIn("!node.isClickable", node_tap)
        self.assertIn("node.getBoundsInScreen(bounds)", node_tap)
        self.assertIn("bounds.right > metrics.widthPixels", node_tap)
        self.assertIn("bounds.bottom > metrics.heightPixels", node_tap)
        self.assertIn('shell("input tap', node_tap)
        self.assertIn("matches.forEach { it.recycle() }", node_tap)
        self.assertIn("containers.forEach { it.recycle() }", node_tap)
        self.assertIn("pinViews.forEach { it.recycle() }", node_tap)
        self.assertIn("roots.forEach { it.recycle() }", node_tap)
        self.assertNotIn("expectedClassName", node_tap)
        self.assertNotIn("NumPadKey", node_tap)
        self.assertNotIn("NumPadButton", node_tap)

    def test_biometric_prompt_pin_entry_targets_only_focused_systemui_ime_field(self):
        source = TEST.read_text(encoding="utf-8")
        start = source.index("private fun enterSyntheticBiometricPromptPin")
        end = source.index("private fun tapVisibleSystemUiNode", start)
        helper = source[start:end]

        self.assertIn('identity.contains("uid=2000(shell)")', helper)
        self.assertIn("hasVisibleBiometricPromptCredentialField()", helper)
        self.assertIn('shell("input text $TEST_PIN")', helper)
        self.assertIn('shell("input keyevent KEYCODE_ENTER")', helper)
        self.assertNotIn("input tap", helper)
        self.assertNotIn("key$digit", helper)
        self.assertNotIn("TEST_PIN.to", helper)

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
        self.assertIn("credentialNodeSummary", source)
        self.assertNotIn("takeScreenshot()", source)
        self.assertIn("viewIdResourceName", source)
        self.assertIn("getBoundsInScreen", source)
        self.assertIn("credentialUiSnapshot()", source)
        self.assertIn('shell("dumpsys window windows")', source)
        self.assertIn("lastCredentialPreflightDiagnostics", source)
        self.assertIn("ui=${credentialUiSnapshot()}", source)

    def test_activity_default_factory_remains_android_backend(self):
        source = (MAIN / "java/tech/mrnothing/os/OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("internal open fun createTrustStore(context: Context)", source)
        self.assertIn("AndroidOwnerAuthorityTrustStore(context)", source)
        self.assertEqual(source.count("createTrustStore(appContext)"), 3)

    def test_emulator_preflight_and_biometric_prompt_use_distinct_systemui_surfaces(self):
        source = TEST.read_text(encoding="utf-8")
        self.assertIn("prepareInteractiveUnlockedEmulator()", source)
        self.assertIn('shell("input keyevent KEYCODE_WAKEUP")', source)
        self.assertIn("keyguard.isDeviceLocked || keyguard.isKeyguardLocked", source)
        self.assertIn("tapSystemDeviceEntryIconToRevealCredentialEntry()", source)
        self.assertIn("com.android.systemui:id/device_entry_icon_view", source)
        self.assertIn("awaitKeyguardPinPad", source)
        self.assertIn("private fun enterSyntheticKeyguardPin", source)
        self.assertIn("awaitBiometricPromptCredentialField", source)
        self.assertIn("private fun enterSyntheticBiometricPromptPin", source)
        self.assertIn("hasVisibleBiometricPromptCredentialField", source)
        self.assertIn('val fieldId = "com.android.systemui:id/lockPassword"', source)
        self.assertIn("OwnerCredentialSafetyGate.isSafe(context)", source)
        self.assertIn("deviceCredentialCanAuthenticate", source)
        self.assertNotIn("wm dismiss-keyguard", source)
        self.assertNotIn("adb root", source)

if __name__ == "__main__":
    unittest.main()
