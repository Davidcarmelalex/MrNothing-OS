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
        start = instrumentation.index("private fun awaitSystemCredentialUi")
        end = instrumentation.index("private fun hasVisibleSystemCredentialInput", start)
        self.assertIn("captureCredentialUiScreenshot()", instrumentation[start:end])

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

if __name__ == "__main__":
    unittest.main()
