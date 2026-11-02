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

    def test_no_physical_device_target(self):
        self.assertIn("ANDROID_SERIAL: emulator-5554", self.workflow)
        script = (WORKFLOW.parents[2] / "scripts/qa005_emulator_smoke.sh").read_text(encoding="utf-8")
        self.assertIn("Refusing non-emulator target", script)
        self.assertIn("ro.kernel.qemu", script)

if __name__ == "__main__":
    unittest.main()
