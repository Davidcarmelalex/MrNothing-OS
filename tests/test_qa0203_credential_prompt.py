"""QA-020B3 static gates and strict hierarchy parser tests."""
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from scripts import qa0203_credential_prompt as helper

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
DEBUG_SRC = ROOT / "android/app/src/debug/java/tech/mrnothing/os"
DEBUG_MANIFEST = ROOT / "android/app/src/debug/AndroidManifest.xml"
MAIN_MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"
WORKFLOW = ROOT / ".github/workflows/qa005-emulator.yml"
SMOKE = ROOT / "scripts/qa0203_credential_prompt_smoke.sh"
ANDROID = "{http://schemas.android.com/apk/res/android}"


class CredentialPromptProbeTests(unittest.TestCase):
    def test_probe_is_debug_only_and_shell_restricted(self):
        app = ET.parse(DEBUG_MANIFEST).getroot().find("application")
        matches = [n for n in app.findall("activity")
                   if n.get(ANDROID + "name") == ".OwnerCredentialPromptProbeActivity"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get(ANDROID + "exported"), "true")
        self.assertEqual(matches[0].get(ANDROID + "permission"), "android.permission.DUMP")
        self.assertEqual(matches[0].get(ANDROID + "excludeFromRecents"), "true")

    def test_cancel_receiver_is_debug_only_and_shell_restricted(self):
        app = ET.parse(DEBUG_MANIFEST).getroot().find("application")
        matches = [n for n in app.findall("receiver")
                   if n.get(ANDROID + "name") == ".OwnerCredentialPromptProbeCancelReceiver"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get(ANDROID + "exported"), "true")
        self.assertEqual(matches[0].get(ANDROID + "permission"), "android.permission.DUMP")
        actions = [n.get(ANDROID + "name") for n in matches[0].findall("intent-filter/action")]
        self.assertEqual(actions, ["tech.mrnothing.os.debug.CANCEL_CREDENTIAL_PROMPT"])

    def test_probe_and_receiver_are_absent_from_release_manifest(self):
        app = ET.parse(MAIN_MANIFEST).getroot().find("application")
        self.assertNotIn(".OwnerCredentialPromptProbeActivity",
                         [n.get(ANDROID + "name") for n in app.findall("activity")])
        self.assertNotIn(".OwnerCredentialPromptProbeCancelReceiver",
                         [n.get(ANDROID + "name") for n in app.findall("receiver")])

    def test_shared_prompt_factory_allows_only_device_credential(self):
        factory = (SRC / "OwnerCredentialPromptFactory.kt").read_text()
        self.assertIn("BiometricPrompt.Builder(activity)", factory)
        self.assertIn("setAllowedAuthenticators(", factory)
        self.assertIn("BiometricManager.Authenticators.DEVICE_CREDENTIAL", factory)
        self.assertNotIn("BIOMETRIC_STRONG", factory)
        self.assertNotIn("BIOMETRIC_WEAK", factory)
        self.assertNotIn("setNegativeButton", factory)

    def test_production_activity_uses_shared_prompt_factory(self):
        activity = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("OwnerCredentialPromptFactory.create(", activity)
        self.assertNotIn("BiometricPrompt.Builder(", activity)

    def test_debug_probe_and_controls_have_no_trust_or_device_action_path(self):
        for path in ("OwnerCredentialPromptProbeActivity.kt",
                     "OwnerCredentialPromptProbeControl.kt",
                     "OwnerCredentialPromptProbeCancelReceiver.kt"):
            source = (DEBUG_SRC / path).read_text()
            for forbidden in ("AndroidOwnerAuthorityTrustStore", "OwnerAuthorityTrustStore(",
                              "store.commit(", "requestPermissions(", "CommandRouter(",
                              "ProcessBuilder(", "Runtime.getRuntime(", "Socket("):
                self.assertNotIn(forbidden, source)

    def test_cancel_control_is_single_signal_and_only_cancels(self):
        source = (DEBUG_SRC / "OwnerCredentialPromptProbeControl.kt").read_text()
        self.assertIn("private var activeSignal: CancellationSignal? = null", source)
        self.assertIn("synchronized(lock)", source)
        self.assertIn("signal.cancel()", source)
        self.assertIn("if (activeSignal === signal) activeSignal = null", source)

    def test_cancel_receiver_calls_probe_control(self):
        source = (DEBUG_SRC / "OwnerCredentialPromptProbeCancelReceiver.kt").read_text()
        self.assertIn("OwnerCredentialPromptProbeControl.cancelActive()", source)
        self.assertIn("ACTION_CANCEL", source)
        self.assertNotIn("OwnerAuthorityTrust", source)
        self.assertNotIn("CommandRouter", source)

    def test_smoke_is_emulator_only_and_cleans_test_pin(self):
        code = SMOKE.read_text()
        for expected in ("emulator-*)", "getprop ro.kernel.qemu", "locksettings set-pin",
                         "locksettings clear --old", "trap cleanup EXIT INT TERM",
                         "uid=2000(shell)", "OwnerCredentialPromptProbeCancelReceiver",
                         "CANCEL_CREDENTIAL_PROMPT", "assert-prompt-absent"):
            self.assertIn(expected, code)
        for removed in ("cancel-gutter-target", "tap_prompt_cancel_surface",
                        "adb root", "fastboot"):
            self.assertNotIn(removed, code)

    def test_smoke_never_escalates_or_targets_physical_device(self):
        code = SMOKE.read_text()
        self.assertNotRegex(code, r"(?m)^\s*adb\s+root\b")
        self.assertNotRegex(code, r"(?m)^\s*su(?:\s|$)")
        for forbidden in ("fastboot", "setenforce", "flashall"):
            self.assertNotIn(forbidden, code)

    def test_workflow_runs_probe_after_insecure_emulator_trust_test(self):
        code = WORKFLOW.read_text()
        self.assertLess(code.index("QA-020B2: owner authority trust UI runtime"),
                        code.index("QA-020B3: credential-only platform prompt"))
        self.assertIn("scripts/qa0203_credential_prompt_smoke.sh", code)
        self.assertIn("tests/test_qa0203_*", code)

    def test_helper_finds_probe_button_and_status(self):
        xml = """<hierarchy>
        <node package="tech.mrnothing.os" class="android.widget.TextView"
              text="Device credential prompt probe" bounds="[0,0][300,40]"/>
        <node package="tech.mrnothing.os" class="android.widget.TextView"
              text="STATUS: READY" bounds="[0,40][300,80]"/>
        <node package="tech.mrnothing.os" class="android.widget.Button"
              text="Authenticate with device credential" content-desc="Authenticate with device credential"
              visible-to-user="true" bounds="[0,80][300,140]"/>
        <node package="tech.mrnothing.os" class="android.widget.Button"
              text="Cancel prompt" content-desc="Cancel prompt"
              visible-to-user="true" bounds="[0,140][300,200]"/>
        </hierarchy>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hierarchy.xml"
            path.write_text(xml)
            self.assertEqual(helper.find_button(path, "Authenticate with device credential"), (150,110))
            helper.assert_probe(path)
            self.assertEqual(helper.status(path), "STATUS: READY")

    def test_helper_rejects_ambiguous_button(self):
        xml = """<hierarchy><node package="tech.mrnothing.os" class="android.widget.Button"
        text="Cancel prompt" bounds="[0,0][100,50]"/><node package="tech.mrnothing.os"
        class="android.widget.Button" text="Cancel prompt" bounds="[0,50][100,100]"/></hierarchy>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hierarchy.xml"
            path.write_text(xml)
            with self.assertRaises(ValueError):
                helper.find_button(path, "Cancel prompt")

    def test_helper_requires_system_pin_prompt(self):
        xml = """<hierarchy><node package="com.android.systemui" class="android.widget.TextView"
        text="Enter PIN" bounds="[0,0][100,50]"/></hierarchy>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hierarchy.xml"
            path.write_text(xml)
            helper.assert_prompt_visible(path)

    def test_helper_rejects_prompt_still_visible_after_cancellation(self):
        xml = """<hierarchy><node package="com.android.systemui" class="android.widget.EditText"
        resource-id="com.android.systemui:id/lockPassword" text=""
        bounds="[267,935][813,1131]"/></hierarchy>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hierarchy.xml"
            path.write_text(xml)
            with self.assertRaisesRegex(ValueError, "remains visible"):
                helper.assert_prompt_absent(path)

    def test_helper_accepts_dismissed_prompt_and_rejects_typed_credential(self):
        gone = """<hierarchy><node package="tech.mrnothing.os" class="android.widget.TextView"
        text="STATUS: PROMPT_ERROR:5" bounds="[0,0][300,40]"/></hierarchy>"""
        typed = """<hierarchy><node package="com.android.systemui" class="android.widget.EditText"
        resource-id="com.android.systemui:id/lockPassword" text="•"
        bounds="[267,935][813,1131]"/></hierarchy>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hierarchy.xml"
            path.write_text(gone)
            helper.assert_prompt_absent(path)
            helper.assert_no_credential_input(path)
            path.write_text(typed)
            with self.assertRaisesRegex(ValueError, "changed the credential input"):
                helper.assert_no_credential_input(path)


if __name__ == "__main__":
    unittest.main()
