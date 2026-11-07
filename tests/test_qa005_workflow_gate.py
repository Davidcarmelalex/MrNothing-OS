"""Static regression gates for QA-005 emulator job safety and diagnostics.

These tests cannot prove that an emulator booted; runtime evidence is required.
"""
from pathlib import Path
import re
import unittest

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/qa005-emulator.yml"

class Qa005WorkflowGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_single_pr_trigger_prevents_duplicate_push_emulators(self):
        self.assertIn("pull_request:", self.workflow)
        self.assertNotIn("  push:", self.workflow)

    def test_newer_pr_head_does_not_cancel_active_emulator_cleanup(self):
        self.assertIn(
            "group: qa005-${{ github.event.pull_request.number || github.ref }}",
            self.workflow,
        )
        self.assertIn("cancel-in-progress: false", self.workflow)
        self.assertNotIn("cancel-in-progress: true", self.workflow)

    def test_adb_wait_has_deadline(self):
        self.assertIn('timeout 180s adb -s "$ANDROID_SERIAL" wait-for-device', self.workflow)
        self.assertIn("Emulator boot timed out", self.workflow)

    def test_avd_profile_is_explicit_and_creation_is_verified(self):
        self.assertIn('-d pixel', self.workflow)
        self.assertIn('emulator -list-avds', self.workflow)
        self.assertIn('grep -Fxq mrnothing_qa005', self.workflow)
        self.assertIn('AVD creation failed', self.workflow)

    def test_avd_home_is_shared_by_creation_and_emulator(self):
        self.assertIn('export ANDROID_AVD_HOME="$RUNNER_TEMP/mrnothing-avds"', self.workflow)
        self.assertIn('export ANDROID_USER_HOME="$RUNNER_TEMP/mrnothing-android-user"', self.workflow)
        self.assertIn('mkdir -p "$ANDROID_AVD_HOME" "$ANDROID_USER_HOME"', self.workflow)
        self.assertIn('-p "$ANDROID_AVD_HOME/mrnothing_qa005.avd"', self.workflow)

    def test_avd_diagnostics_capture_both_sdk_tools(self):
        self.assertIn('avd-create.txt', self.workflow)
        self.assertIn('avd-manager-list.txt', self.workflow)
        self.assertIn('avd-directory.txt', self.workflow)

    def test_emulator_never_starts_before_avd_gate(self):
        self.assertLess(self.workflow.index('grep -Fxq mrnothing_qa005'),
                        self.workflow.index('nohup emulator -avd mrnothing_qa005'))

    def test_emulator_diagnostics_always_uploaded(self):
        self.assertIn("Capture emulator diagnostics", self.workflow)
        self.assertIn("if: always()", self.workflow)
        self.assertIn("qa005-emulator-evidence-not-for-release", self.workflow)

    def test_requires_hardware_acceleration(self):
        self.assertIn("/dev/kvm", self.workflow)
        self.assertIn("-accel on", self.workflow)

    def test_emulator_resources_support_instrumentation_startup(self):
        self.assertIn("-memory 3072 -cores 4", self.workflow)

    def test_anr_and_app_memory_diagnostics_are_always_captured(self):
        self.assertIn("dumpsys activity lastanr", self.workflow)
        self.assertIn("dumpsys meminfo tech.mrnothing.os", self.workflow)

    def test_activity_lifecycle_instrumentation_runs_after_emulator_boot(self):
        instrumentation = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        emulator = self.workflow.index("Start disposable x86_64 emulator")
        launcher_smoke = self.workflow.index("Verify launcher runtime and recovery route")
        self.assertLess(emulator, instrumentation)
        self.assertLess(instrumentation, launcher_smoke)
        self.assertIn(":app:connectedDebugAndroidTest", self.workflow)
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary_step = self.workflow[start:end]
        self.assertEqual(1, boundary_step.count(":app:connectedDebugAndroidTest"))
        self.assertIn("locksettings set-pin", boundary_step)
        self.assertIn("locksettings clear --old", boundary_step)
        self.assertIn("trap cleanup EXIT INT TERM", boundary_step)
        self.assertIn("uid=2000(shell)", boundary_step)

    def test_instrumentation_test_apk_is_prebuilt_before_emulator_credential_setup(self):
        build_start = self.workflow.index("Build debug APK with checksum-verified Gradle")
        build_end = self.workflow.index("Negative control — reject modified Gradle dependency", build_start)
        build_step = self.workflow[build_start:build_end]
        self.assertIn(":app:assembleDebugAndroidTest", build_step)
        self.assertLess(
            self.workflow.index(":app:assembleDebugAndroidTest"),
            self.workflow.index("locksettings set-pin"),
        )

    def test_disposable_emulator_is_secure_and_awake_before_ui_instrumentation(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        for required in (
            "locksettings set-pin", "locksettings clear --old", "trap cleanup EXIT INT TERM",
            "uid=2000(shell)", "input keyevent KEYCODE_WAKEUP", "dumpsys power",
            "qa005_power_state.py", "--min-wake-age-ms 1500",
            "power-state-before-instrumentation.txt", "dumpsys window policy",
            "keyguard-state-before-instrumentation.txt",
            "Display is interactive; instrumentation will verify the synthetic credential",
            ":app:connectedDebugAndroidTest",
        ):
            self.assertIn(required, boundary)
        self.assertLess(boundary.index("locksettings set-pin"), boundary.index("KEYCODE_WAKEUP"))
        self.assertLess(boundary.index("screen_is_awake"), boundary.index("keyguard-state-before-instrumentation.txt"))
        self.assertLess(boundary.index("keyguard-state-before-instrumentation.txt"), boundary.index(":app:connectedDebugAndroidTest"))
        self.assertNotIn("keyguard_is_hidden", boundary)
        self.assertNotIn("KeyguardServiceDelegate", boundary)
        self.assertNotIn("KeyguardStateMonitor", boundary)
        self.assertNotIn("input swipe", boundary)
        self.assertNotIn("adb root", boundary)
    def test_keyguard_state_is_diagnostic_not_a_preflight_gate(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        self.assertIn("dumpsys window policy", boundary)
        self.assertIn("keyguard-state-before-instrumentation.txt", boundary)
        self.assertIn("exact visible SystemUI PIN controls", boundary)
        self.assertNotIn("keyguard_is_hidden", boundary)
        self.assertNotIn("KeyguardServiceDelegate", boundary)
        self.assertNotIn("KeyguardStateMonitor", boundary)
        self.assertNotIn("refusing to synthesize a Keyguard dismissal", boundary)
    def test_android15_power_manager_dump_uses_hal_interactive_mode_field(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        parser = (WORKFLOW.parents[2] / "scripts/qa005_power_state.py").read_text(encoding="utf-8")
        self.assertIn('("mWakefulness", "Awake")', parser)
        self.assertIn('("mWakefulnessChanging", "false")', parser)
        self.assertIn('("mHalInteractiveModeEnabled", "true")', parser)
        self.assertIn("mLastWakeTime=", parser)
        self.assertNotIn("mInteractive=true", parser)
        self.assertNotIn("mInteractive=false", parser)

    def test_wake_gate_precedes_keyguard_diagnostic_and_instrumentation(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        parser = (WORKFLOW.parents[2] / "scripts/qa005_power_state.py").read_text(encoding="utf-8")
        self.assertIn('("mWakefulnessChanging", "false")', parser)
        self.assertIn("screen_is_awake", boundary)
        self.assertIn("keyguard-state-before-instrumentation.txt", boundary)
        self.assertLess(boundary.index("screen_is_awake"), boundary.index("keyguard-state-before-instrumentation.txt"))
        self.assertLess(boundary.index("keyguard-state-before-instrumentation.txt"), boundary.index(":app:connectedDebugAndroidTest"))
    def test_wake_gate_requires_minimum_post_wake_settle_interval(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        parser = (WORKFLOW.parents[2] / "scripts/qa005_power_state.py").read_text(encoding="utf-8")
        self.assertIn("minimum_wake_age_ms: int = 1500", parser)
        self.assertIn("age_ms < minimum_wake_age_ms", parser)
        self.assertIn("--min-wake-age-ms 1500", boundary)
        self.assertIn("power-state-before-instrumentation.txt", boundary)
        self.assertLess(boundary.index("screen_is_awake"), boundary.index("keyguard-state-before-instrumentation.txt"))
    def test_instrumentation_owns_locked_emulator_authentication(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        self.assertIn("locksettings set-pin", boundary)
        self.assertIn("locksettings clear --old", boundary)
        self.assertIn("keyguard-state-before-instrumentation.txt", boundary)
        self.assertNotIn("Fresh disposable emulator is not already unlocked", boundary)
        self.assertNotIn("keyguard_is_hidden", boundary)
        source = (WORKFLOW.parents[2] / "android/app/src/androidTest/java/tech/mrnothing/os/OwnerAuthorityTrustActivityCommitLifecycleTest.kt").read_text(encoding="utf-8")
        self.assertIn("prepareInteractiveUnlockedEmulator()", source)
        self.assertIn("keyguard.isDeviceSecure", source)
        self.assertIn("keyguard.isDeviceLocked || keyguard.isKeyguardLocked", source)
        self.assertIn("longPressSystemDeviceEntryIconToRevealCredentialEntry()", source)
        self.assertIn("awaitKeyguardPinPad", source)
        self.assertIn("enterSyntheticKeyguardPin(identity)", source)
        self.assertIn('identity.contains("uid=2000(shell)")', source)
    def test_active_preflight_never_synthesizes_keyguard_dismissal(self):
        self.assertNotIn("qa005_unlock_keyguard.py", self.workflow)
        self.assertNotIn("input swipe", self.workflow)
        self.assertNotIn("KEYCODE_SLEEP", self.workflow)
        self.assertNotIn('shell input text "$TEST_PIN"', self.workflow)
        self.assertNotIn("adb root", self.workflow)

    def test_instrumentation_uses_compile_only_platform_test_apis(self):
        gradle = (WORKFLOW.parents[2] / "android/app/build.gradle.kts").read_text(encoding="utf-8")
        self.assertIn("androidTestCompileOnly(files(androidTestPlatformApiJars))", gradle)
        self.assertIn("android.test.base.jar", gradle)
        self.assertIn("android.test.runner.jar", gradle)

    def test_android_instrumentation_reports_and_full_logcat_are_always_uploaded(self):
        self.assertIn("android-test-report", self.workflow)
        self.assertIn("outputs/androidTest-results/connected/debug", self.workflow)
        self.assertIn("reports/androidTests/connected/debug", self.workflow)
        self.assertIn("logcat -b all -d -t 2000", self.workflow)

    def test_credential_preflight_failure_captures_structural_ui_and_screenshot(self):
        instrumentation_path = (WORKFLOW.parents[2] /
            "android/app/src/androidTest/java/tech/mrnothing/os/OwnerAuthorityTrustActivityCommitLifecycleTest.kt")
        instrumentation = instrumentation_path.read_text(encoding="utf-8")
        self.assertIn("viewIdResourceName", instrumentation)
        self.assertIn("getBoundsInScreen", instrumentation)
        self.assertIn("credentialNodeSummary", instrumentation)
        self.assertNotIn("takeScreenshot()", instrumentation)
        self.assertIn("credential-ui-pre-cleanup.png", self.workflow)
        for helper_name in (
            "private fun awaitKeyguardPinPad",
            "private fun awaitBiometricPromptCredentialField",
        ):
            start = instrumentation.index(helper_name)
            end = instrumentation.index("\n    private fun ", start + len(helper_name))
            self.assertIn("credentialUiSnapshot()", instrumentation[start:end])
        self.assertIn("hasVisibleBiometricPromptCredentialField", instrumentation)
        self.assertIn("hasVisibleKeyguardPinPad", instrumentation)
        self.assertIn("exec-out screencap -p", self.workflow)

    def test_failure_screenshot_is_extracted_without_root(self):
        self.assertIn("timeout 180s", self.workflow)
        self.assertIn("exec-out screencap -p", self.workflow)
        self.assertIn("credential-ui-pre-cleanup.png", self.workflow)
        self.assertLess(self.workflow.index("exec-out screencap -p"), self.workflow.index("locksettings clear --old"))
        self.assertNotIn("adb root", self.workflow)

    def test_no_physical_device_target(self):
        self.assertIn("ANDROID_SERIAL: emulator-5554", self.workflow)
        script = (WORKFLOW.parents[2] / "scripts/qa005_emulator_smoke.sh").read_text(encoding="utf-8")
        self.assertIn("Refusing non-emulator target", script)
        self.assertIn("ro.kernel.qemu", script)


    def test_instrumentation_preflight_matches_owner_credential_safety_gate(self):
        root = WORKFLOW.parents[2]
        instrumentation = (root /
            "android/app/src/androidTest/java/tech/mrnothing/os/OwnerAuthorityTrustActivityCommitLifecycleTest.kt").read_text(encoding="utf-8")
        safety_gate = (root /
            "android/app/src/main/java/tech/mrnothing/os/OwnerCredentialSafetyGate.kt").read_text(encoding="utf-8")
        self.assertIn("keyguard.isDeviceSecure", instrumentation)
        self.assertIn("keyguard.isDeviceLocked", instrumentation)
        self.assertIn("keyguard.isKeyguardLocked", instrumentation)
        self.assertIn("OwnerCredentialSafetyGate.isSafe(context)", instrumentation)
        self.assertIn("secureLockConfigured = keyguard.isDeviceSecure", safety_gate)
        self.assertIn("deviceLocked = keyguard.isDeviceLocked", safety_gate)
        self.assertIn("keyguardLocked = keyguard.isKeyguardLocked", safety_gate)
        self.assertIn("screenInteractive = power.isInteractive", safety_gate)
        self.assertIn("!signals.deviceLocked", safety_gate)
        self.assertIn("!signals.keyguardLocked", safety_gate)

    def test_wake_gate_uses_the_unit_tested_fail_closed_parser(self):
        self.assertIn(
            'python3 ../scripts/qa005_power_state.py --min-wake-age-ms 1500 --quiet 2>/dev/null <<< "$1"',
            self.workflow,
        )
        self.assertIn(
            'python3 ../scripts/qa005_power_state.py --min-wake-age-ms 1500 <<< "$power_state" || true',
            self.workflow,
        )
        self.assertNotIn("sed -nE", self.workflow)

    def test_active_workflow_has_no_lockscreen_gesture_or_credential_helper(self):
        self.assertNotIn("shell input swipe", self.workflow)
        self.assertNotIn("qa005_unlock_keyguard.py", self.workflow)
        self.assertNotIn("settings get secure navigation_mode", self.workflow)
        self.assertNotIn("navigation-mode.txt", self.workflow)

    def test_power_snapshot_writer_uses_a_real_newline(self):
        line = next(
            line for line in self.workflow.splitlines()
            if "power-state-before-instrumentation.txt" in line and "printf" in line
        )
        self.assertEqual(1, line.count("\\"))
        self.assertIn("printf '%s\\n'", line)

    def test_systemui_device_entry_uses_exact_long_click_action(self):
        source = (WORKFLOW.parents[2] / "android/app/src/androidTest/java/tech/mrnothing/os/OwnerAuthorityTrustActivityCommitLifecycleTest.kt").read_text(encoding="utf-8")
        start = source.index("private fun longPressSystemDeviceEntryIconToRevealCredentialEntry")
        end = source.index("private fun awaitCredentialPrompt", start)
        helper = source[start:end]
        for required in (
            'val viewId = "com.android.systemui:id/device_entry_icon_view"',
            'root.packageName?.toString() != "com.android.systemui"',
            'it.className?.toString() == "android.widget.FrameLayout"',
            "it.isVisibleToUser && it.isEnabled",
            "it.isClickable && it.isLongClickable",
            "getBoundsInScreen",
            "bounds.right <= width && bounds.bottom <= height",
            "target.performAction(AccessibilityNodeInfo.ACTION_LONG_CLICK)",
            'identity.contains("uid=2000(shell)")',
        ):
            self.assertIn(required, helper)
        self.assertNotIn("input tap", helper)
        self.assertNotIn("input swipe", helper)

    def test_instrumentation_command_is_invoked_exactly_once(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        self.assertEqual(1, boundary.count(":app:connectedDebugAndroidTest"))


    def test_action_filtered_settings_monitor_is_scoped_after_private_disclosure_launch(self):
        root = WORKFLOW.parents[2]
        source = (root /
            "android/app/src/androidTest/java/tech/mrnothing/os/AccessibilityDisclosureActivityTest.kt").read_text(encoding="utf-8")
        start = source.index("private fun launchMainActivity")
        end = source.index("private fun openDisclosureFromLauncher", start)
        launch = source[start:end]
        self.assertIn("Intent(Intent.ACTION_MAIN)", launch)
        self.assertIn("Intent.CATEGORY_LAUNCHER", launch)
        self.assertIn("intent.hasCategory(Intent.CATEGORY_LAUNCHER)", launch)
        monitor_start = source.index("val settingsMonitor")
        monitor_end = source.index("        var monitorRegistered", monitor_start)
        settings_monitor = source[monitor_start:monitor_end]
        self.assertIn("IntentFilter(Settings.ACTION_ACCESSIBILITY_SETTINGS)", settings_monitor)
        self.assertIn("Instrumentation.ActivityResult(Activity.RESULT_OK, null)", settings_monitor)
        self.assertIn("true", settings_monitor)

        test_start = source.index("fun testAccessibilitySettingsIntentIsIssuedOnlyAfterExplicitTap")
        test_body = source[test_start:]
        disclosure_open = test_body.index("activity = openDisclosureFromLauncher(launcher!!)")
        monitor_add = test_body.index("getInstrumentation().addMonitor(settingsMonitor)")
        explicit_tap = test_body.index("button!!.performClick()")
        self.assertLess(disclosure_open, monitor_add)
        self.assertLess(monitor_add, explicit_tap)
        self.assertIn("monitorRegistered = true", test_body)
        self.assertIn(
            "if (monitorRegistered) getInstrumentation().removeMonitor(settingsMonitor)",
            test_body
        )
        self.assertNotIn("Intent(instrumentation.targetContext, MainActivity::class.java)", launch)

    def test_process_startup_anr_diagnostics_capture_exit_history_and_events(self):
        marker = self.workflow.index("      - name: Capture emulator diagnostics")
        upload = self.workflow.index("      - uses: actions/upload-artifact", marker)
        diagnostics = self.workflow[marker:upload]
        for required in (
            'timeout 15s adb -s "$ANDROID_SERIAL" logcat -b events -d -t 10000',
            'timeout 15s adb -s "$ANDROID_SERIAL" shell dumpsys activity exit-info tech.mrnothing.os',
            'timeout 15s adb -s "$ANDROID_SERIAL" shell dumpsys activity exit-info tech.mrnothing.os.test',
            'timeout 15s adb -s "$ANDROID_SERIAL" shell dumpsys dropbox --print data_app_anr',
        ):
            self.assertIn(required, diagnostics)
        for artifact_name in ("events-tail.txt", "app-exit-info.txt", "test-exit-info.txt", "dropbox-data-app-anr.txt"):
            self.assertIn(artifact_name, diagnostics)
        self.assertNotIn("adb root", diagnostics)


    def test_legacy_instrumentation_runner_uses_explicit_class_allowlist(self):
        root = WORKFLOW.parents[2]
        gradle = (root / "android/app/build.gradle.kts").read_text(encoding="utf-8")
        self.assertIn(
            'testInstrumentationRunner = "android.test.InstrumentationTestRunner"',
            gradle,
        )
        assignment = 'testInstrumentationRunnerArguments["class"] = listOf('
        self.assertIn(assignment, gradle)
        start = gradle.index(assignment)
        end = gradle.index(').joinToString(",")', start)
        configured_block = gradle[start:end]
        configured = re.findall(
            r'"(tech\.mrnothing\.os\.[A-Za-z0-9_]+)"',
            configured_block,
        )

        test_dir = root / "android/app/src/androidTest/java/tech/mrnothing/os"
        discovered = []
        for source_path in sorted(test_dir.glob("*.kt")):
            source = source_path.read_text(encoding="utf-8")
            discovered.extend(
                f"tech.mrnothing.os.{name}"
                for name in re.findall(
                    r"^class\s+(\w+)\s*:\s*InstrumentationTestCase\b",
                    source,
                    re.MULTILINE,
                )
            )

        self.assertTrue(discovered, "no InstrumentationTestCase classes were discovered")
        self.assertEqual(sorted(discovered), sorted(configured))
        self.assertEqual(len(configured), len(set(configured)))
        self.assertEqual(5, len(configured))
        self.assertIn('.joinToString(",")', gradle)



if __name__ == "__main__":
    unittest.main()
