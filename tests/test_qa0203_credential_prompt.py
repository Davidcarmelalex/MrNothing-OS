"""QA-020B3 static gates and strict hierarchy parser tests."""
from pathlib import Path
import unittest

from scripts import qa0203_credential_prompt as helper

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
DEBUG_MANIFEST = ROOT / "android/app/src/debug/AndroidManifest.xml"
MAIN_MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"
WORKFLOW = ROOT / ".github/workflows/qa005-emulator.yml"
SMOKE = ROOT / "scripts/qa0203_credential_prompt_smoke.sh"


class CredentialPromptProbeTests(unittest.TestCase):
    def test_probe_is_debug_only_and_shell_restricted(self):
        import xml.etree.ElementTree as ET
        root = ET.parse(DEBUG_MANIFEST).getroot()
        app = root.find("application")
        android = "{http://schemas.android.com/apk/res/android}"
        matches = [node for node in app.findall("activity")
                   if node.get(android + "name") == ".OwnerCredentialPromptProbeActivity"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get(android + "exported"), "true")
        self.assertEqual(matches[0].get(android + "permission"), "android.permission.DUMP")
        self.assertEqual(matches[0].get(android + "excludeFromRecents"), "true")

    def test_probe_is_absent_from_release_manifest(self):
        import xml.etree.ElementTree as ET
        root = ET.parse(MAIN_MANIFEST).getroot()
        app = root.find("application")
        android = "{http://schemas.android.com/apk/res/android}"
        self.assertFalse(any(
            node.get(android + "name") == ".OwnerCredentialPromptProbeActivity"
            for node in app.findall("activity")
        ))

    def test_shared_prompt_factory_allows_only_device_credential(self):
        factory = (SRC / "OwnerCredentialPromptFactory.kt").read_text()
        self.assertIn("BiometricPrompt.Builder(activity)", factory)
        self.assertIn("setAllowedAuthenticators(", factory)
        self.assertIn("BiometricManager.Authenticators.DEVICE_CREDENTIAL", factory)
        self.assertNotIn("BIOMETRIC_STRONG", factory)
        self.assertNotIn("BIOMETRIC_WEAK", factory)
        self.assertNotIn("setNegativeButton", factory)

    def test_production_activity_uses_the_shared_prompt_factory(self):
        activity = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("OwnerCredentialPromptFactory.create(", activity)
        self.assertNotIn("BiometricPrompt.Builder(", activity)

    def test_probe_has_no_trust_store_permission_or_execution_path(self):
        probe = (ROOT / "android/app/src/debug/java/tech/mrnothing/os/OwnerCredentialPromptProbeActivity.kt").read_text()
        for forbidden in (
            "AndroidOwnerAuthorityTrustStore", "OwnerAuthorityTrustStore(",
            "store.commit(", "requestPermissions(", "CommandRouter(",
            "ProcessBuilder(", "Runtime.getRuntime(", "Socket("
        ):
            self.assertNotIn(forbidden, probe)

    def test_smoke_is_emulator_only_and_cleans_test_pin(self):
        code = SMOKE.read_text()
        self.assertIn('emulator-*)', code)
        self.assertIn('getprop ro.kernel.qemu', code)
        self.assertIn('locksettings set-pin', code)
        self.assertIn('locksettings clear --old', code)
        self.assertIn('trap cleanup EXIT INT TERM', code)
        self.assertIn('uid=2000(shell)', code)

    def test_smoke_never_escalates_or_targets_a_physical_device(self):
        code = SMOKE.read_text()
        self.assertNotRegex(code, r"(?m)^\s*adb\s+root\b")
        self.assertNotRegex(code, r"(?m)^\s*su(?:\s|$)")
        for forbidden in ("fastboot", "setenforce", "flashall"):
            self.assertNotIn(forbidden, code)

    def test_workflow_runs_probe_after_insecure_emulator_trust_test(self):
        code = WORKFLOW.read_text()
        b2 = code.index('QA-020B2: owner authority trust UI runtime')
        b3 = code.index('QA-020B3: credential-only platform prompt')
        self.assertLess(b2, b3)
        self.assertIn("scripts/qa0203_credential_prompt_smoke.sh", code)
        self.assertIn("tests/test_qa0203_*", code)

    def test_helper_finds_exact_probe_button_and_status(self):
        xml = """<hierarchy>
        <node package="tech.mrnothing.os" class="android.widget.TextView"
              text="Device credential prompt probe" bounds="[0,0][300,40]"/>
        <node package="tech.mrnothing.os" class="android.widget.TextView"
              text="STATUS: READY" bounds="[0,40][300,80]"/>
        <node package="tech.mrnothing.os" class="android.widget.Button"
              text="Authenticate with device credential"
              content-desc="Authenticate with device credential"
              visible-to-user="true" bounds="[0,80][300,140]"/>
        <node package="tech.mrnothing.os" class="android.widget.Button"
              text="Cancel prompt" content-desc="Cancel prompt"
              visible-to-user="true" bounds="[0,140][300,200]"/>
        </hierarchy>"""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hierarchy.xml"
            path.write_text(xml)
            self.assertEqual(
                helper.find_button(path, "Authenticate with device credential"),
                (150, 110)
            )
            helper.assert_probe(path)
            self.assertEqual(helper.status(path), "STATUS: READY")

    def test_helper_rejects_ambiguous_button(self):
        xml = """<hierarchy>
        <node package="tech.mrnothing.os" class="android.widget.Button"
              text="Cancel prompt" bounds="[0,0][100,50]"/>
        <node package="tech.mrnothing.os" class="android.widget.Button"
              text="Cancel prompt" bounds="[0,50][100,100]"/>
        </hierarchy>"""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hierarchy.xml"
            path.write_text(xml)
            with self.assertRaises(ValueError):
                helper.find_button(path, "Cancel prompt")

    def test_helper_requires_system_pin_prompt_and_exact_status(self):
        xml = """<hierarchy>
        <node package="com.android.systemui" class="android.widget.TextView"
              text="Enter PIN" bounds="[0,0][100,50]"/>
        </hierarchy>"""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hierarchy.xml"
            path.write_text(xml)
            helper.assert_prompt_visible(path)
            with self.assertRaises(ValueError):
                helper.assert_status(path, "STATUS: DEVICE_CREDENTIAL_ACCEPTED")


if __name__ == "__main__":
    unittest.main()
