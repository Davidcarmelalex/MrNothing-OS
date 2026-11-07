"""Static regression gates for QA-005 emulator job safety and diagnostics.

These tests cannot prove that an emulator booted; runtime evidence is required.
"""
from pathlib import Path
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

    def test_disposable_emulator_is_awake_and_unlocked_before_ui_instrumentation(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        for required in (
            "settings put system screen_off_timeout 600000",
            "input keyevent KEYCODE_SLEEP",
            "dumpsys power",
            "mWakefulness=Asleep",
            "input keyevent KEYCODE_WAKEUP",
            "keyguard-state-after-wake.txt",
            "power-state-after-wake.txt",
            "mWakefulness=Awake",
            "mInteractive=true",
            "screen_is_awake",
            "Disposable emulator display did not reach a fully interactive awake state after wake",
            "KeyguardServiceDelegate",
            "showing=",
            "KeyguardStateMonitor",
            "mIsShowing=",
            "keyguard_is_showing",
            "shell wm size",
            "--capture",
            "keyguard-hierarchy.xml",
            "qa005_unlock_keyguard.py",
            'swipe_start_y="$((display_height - 120))"',
            'swipe_end_y="$((display_height / 2))"',
            '"$swipe_start_y"',
            '"$swipe_end_y"',
            " 450",
            "Disposable emulator keyguard dismissed",
        ):
            self.assertIn(required, boundary)
        self.assertLess(boundary.index("locksettings set-pin"), boundary.index("input keyevent KEYCODE_SLEEP"))
        self.assertLess(boundary.index("input keyevent KEYCODE_SLEEP"), boundary.index("dumpsys power"))
        self.assertLess(boundary.index("dumpsys power"), boundary.index("input keyevent KEYCODE_WAKEUP"))
        self.assertLess(boundary.index("input keyevent KEYCODE_WAKEUP"), boundary.index("keyguard_showing=0"))
        self.assertLess(boundary.index("swipe_start_y="), boundary.index("input swipe"))
        self.assertLess(boundary.index("input swipe"), boundary.index("--capture"))
        self.assertLess(boundary.index("keyguard_showing=0"), boundary.index("if keyguard_is_showing"))
        self.assertLess(boundary.index("if keyguard_is_showing"), boundary.index("--capture"))
        self.assertLess(boundary.index("qa005_unlock_keyguard.py"), boundary.index("--capture"))
        self.assertLess(boundary.index("qa005_unlock_keyguard.py"), boundary.index('if keyguard_is_hidden "$keyguard_policy"'))
        self.assertLess(boundary.index('if keyguard_is_hidden "$keyguard_policy"'), boundary.index(":app:connectedDebugAndroidTest"))
        self.assertNotIn('shell input text "$TEST_PIN"', boundary)
        self.assertNotIn("adb root", boundary)
        self.assertIn("uid=2000(shell)", boundary)

    def test_keyguard_swipe_waits_for_fully_awake_display_and_consistent_policy(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        self.assertIn("mWakefulness=Awake", boundary)
        self.assertIn("mInteractive=true", boundary)
        self.assertIn('if screen_is_awake "$power_state_after_wake"; then', boundary)
        self.assertIn('[[ "$service_state" == "true" && "$monitor_state" == "true" ]]', boundary)
        self.assertLess(boundary.index("KEYCODE_WAKEUP"), boundary.index("power-state-after-wake.txt"))
        self.assertLess(boundary.index("power-state-after-wake.txt"), boundary.index("input swipe"))
        self.assertLess(boundary.index("keyguard_is_showing"), boundary.index("input swipe"))
        self.assertLess(boundary.index("input swipe"), boundary.index("--capture"))

    def test_keyguard_transition_race_requires_observed_bouncer_before_pin_entry(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        self.assertIn('if screen_is_asleep "$power_state"; then', boundary)
        self.assertIn('if keyguard_is_showing "$keyguard_policy"; then', boundary)
        self.assertIn("Synthetic PIN was configured, but Keyguard did not become visibly locked after sleep/wake", boundary)
        self.assertIn("keyguard-state-after-instrumentation-unlock.txt", boundary)
        self.assertLess(boundary.index("keyguard_showing=0"), boundary.index('if keyguard_is_showing "$keyguard_policy"'))
        self.assertLess(boundary.index('if keyguard_is_showing "$keyguard_policy"'), boundary.index("--capture"))
        self.assertLess(boundary.index("qa005_unlock_keyguard.py"), boundary.index("--capture"))
        self.assertLess(boundary.index("qa005_unlock_keyguard.py"), boundary.index('if keyguard_is_hidden "$keyguard_policy"'))

    def test_keyguard_unlock_uses_exact_systemui_resource_ids_without_text_injection(self):
        start = self.workflow.index("SEC-020B4D: Activity destruction before/after trust commit claim")
        end = self.workflow.index("Verify launcher runtime and recovery route", start)
        boundary = self.workflow[start:end]
        script = (WORKFLOW.parents[2] / "scripts/qa005_unlock_keyguard.py").read_text(encoding="utf-8")
        self.assertIn("--capture", boundary)
        self.assertIn("qa005_unlock_keyguard.py", boundary)
        self.assertNotIn('shell input text "$TEST_PIN"', boundary)
        for required in (
            "com.android.systemui:id/keyguard_pin_view",
            "com.android.systemui:id/pin_container",
            "com.android.systemui:id/key_enter",
            'f"{SYSTEM_UI}:id/key{digit}"',
            "uid=2000(shell)",
            "clickable",
            "enabled",
            "bounds",
            '"input", "tap"',
        ):
            self.assertIn(required, script)
        self.assertNotIn("adb root", script)
        self.assertIn("working-directory: android", self.workflow)
        self.assertIn("TEST_PIN=2468", boundary)
        self.assertIn('TEST_PIN="$TEST_PIN" timeout 120s python3 ../scripts/qa005_unlock_keyguard.py', boundary)
        self.assertIn("--capture", boundary)
        self.assertIn("UI hierchary dumped to:", script)
        self.assertIn("ERROR: null root node returned by UiTestAutomationBridge.", script)
        self.assertIn("qa005-keyguard-attempt-", script)
        self.assertIn("max_attempts: int = 5", script)
        self.assertIn('DEVICE_ENTRY_ID = f"{SYSTEM_UI}:id/device_entry_icon_view"', script)
        self.assertIn('DEVICE_ENTRY_FG_ID = f"{SYSTEM_UI}:id/device_entry_icon_fg"', script)
        self.assertIn('DEVICE_LOCKED_DESC = "Device locked"', script)
        self.assertIn("validate_keyguard_locked_surface", script)

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


    def test_locked_surface_validation_and_capture_are_read_only(self):
        script = (WORKFLOW.parents[2] / "scripts/qa005_unlock_keyguard.py").read_text(encoding="utf-8")
        start = script.index("def validate_keyguard_locked_surface")
        end = script.index("\ndef _adb_result", start)
        parser = script[start:end]
        for required in (
            "DEVICE_ENTRY_ID",
            "DEVICE_ENTRY_FG_ID",
            "DEVICE_LOCKED_DESC",
            "content-desc",
            "clickable=True",
            "parse_bounds",
        ):
            self.assertIn(required, parser)
        capture_start = script.index("def capture_fresh_systemui_keypad_hierarchy")
        capture_end = script.index("\ndef unlock_with_visible_systemui_pinpad", capture_start)
        capture = script[capture_start:capture_end]
        self.assertIn("validate_keyguard_locked_surface(hierarchy, width, height)", capture)
        self.assertNotIn('"input", "tap"', capture)
        self.assertNotIn("entry_tapped", capture)
        self.assertIn("max_attempts: int = 5", capture)
        self.assertNotIn('shell", "input", "text"', script)

if __name__ == "__main__":
    unittest.main()
