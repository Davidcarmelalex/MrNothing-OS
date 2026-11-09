"""QA-011 preflight regression and safety checks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from scripts.qa011_talkback_preflight import PACKAGE, evaluate

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/qa011_talkback_preflight.sh").read_text()
WORKFLOW = (ROOT / ".github/workflows/qa005-emulator.yml").read_text()


class PreflightTests(unittest.TestCase):
    def test_missing_package(self):
        r = evaluate("package:other", "1", PACKAGE + "/.TalkBackService")
        self.assertEqual(r["status"], "blocked_package_missing")
        self.assertFalse(r["acceptance_passed"])

    def test_disabled_accessibility(self):
        self.assertEqual(evaluate("package:" + PACKAGE, "0", PACKAGE + "/.TalkBackService")["status"],
                         "blocked_service_disabled")

    def test_disabled_service(self):
        self.assertEqual(evaluate("package:" + PACKAGE, "1", "other/.Service")["status"],
                         "blocked_service_disabled")

    def test_enabled_is_only_ready(self):
        r = evaluate("package:" + PACKAGE, "1", "other/.S:" + PACKAGE + "/.TalkBackService")
        self.assertEqual(r["status"], "ready_for_manual_validation")
        self.assertFalse(r["acceptance_passed"])
        self.assertFalse(r["spoken_navigation_verified"])

    def test_similar_package_refused(self):
        self.assertEqual(evaluate("package:" + PACKAGE + ".fake", "1", PACKAGE + "/.Service")["status"],
                         "blocked_package_missing")

    def test_similar_service_refused(self):
        self.assertEqual(evaluate("package:" + PACKAGE, "1", PACKAGE + ".fake/.Service")["status"],
                         "blocked_service_disabled")

    def test_null_service(self):
        self.assertEqual(evaluate("package:" + PACKAGE, "1", "null")["status"],
                         "blocked_service_disabled")

    def test_malformed_setting_refused(self):
        for flag in ("null", "", "2", "true"):
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                evaluate("package:" + PACKAGE, flag, PACKAGE + "/.Service")

    def test_cli_explicit_nonacceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            (d / "packages").write_text("package:" + PACKAGE)
            (d / "accessibility").write_text("1")
            (d / "services").write_text(PACKAGE + "/.TalkBackService")
            out = d / "out.json"
            subprocess.run([sys.executable, str(ROOT / "scripts/qa011_talkback_preflight.py"),
                            "--packages", str(d / "packages"), "--accessibility", str(d / "accessibility"),
                            "--services", str(d / "services"), "--output", str(out)],
                           cwd=ROOT, check=True, capture_output=True, text=True)
            self.assertFalse(json.loads(out.read_text())["acceptance_passed"])

    def test_emulator_guard_and_readonly(self):
        self.assertIn("Refusing non-emulator target", SCRIPT)
        self.assertIn("ro.kernel.qemu", SCRIPT)
        self.assertIn("settings get secure", SCRIPT)
        self.assertNotIn("settings put", SCRIPT)
        self.assertNotIn("pm install", SCRIPT)
        self.assertIn("qa011_talkback_preflight.sh", WORKFLOW)
