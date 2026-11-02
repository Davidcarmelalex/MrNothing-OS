import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.sax.saxutils import quoteattr
from scripts.qa012_semantics import audit, RECOVERY, SETTINGS, CONSENT

ROOT = Path(__file__).resolve().parents[1]
SHELL = (ROOT / "scripts/qa012_semantics_smoke.sh").read_text()
WORKFLOW = (ROOT / ".github/workflows/qa005-emulator.yml").read_text()


def node(kind, text="", desc="", bounds="[0,0][200,120]", clickable=None):
    if clickable is None:
        clickable = kind == "android.widget.Button"
    attrs = {"package": "tech.mrnothing.os", "class": kind, "text": text,
             "content-desc": desc, "bounds": bounds,
             "clickable": str(clickable).lower(),
             "focusable": str(kind == "android.widget.Button").lower(),
             "enabled": "true"}
    return "<node " + " ".join(k + "=" + quoteattr(v) for k, v in attrs.items()) + "/>"


def fixture(consent=True, recovery_bounds="[0,0][200,120]"):
    text = lambda value: node("android.widget.TextView", text=value)
    button = lambda desc, bounds="[0,0][200,120]": node("android.widget.Button", desc=desc, bounds=bounds)
    return ("<hierarchy>" + text("MR. NOTHING") + text("Device status") +
            (button(CONSENT) if consent else "") + button(RECOVERY, recovery_bounds) +
            button(SETTINGS) + text("Installed apps") + "</hierarchy>")


class Qa012Tests(unittest.TestCase):
    def test_valid(self):
        r = audit(fixture(), 2)
        self.assertTrue(r["structural_checks_passed"])
        self.assertFalse(r["spoken_navigation_verified"])
        self.assertFalse(r["acceptance_passed"])

    def test_consent_absent_allowed(self):
        self.assertFalse(audit(fixture(consent=False), 2)["consent_action_present"])

    def test_missing_recovery(self):
        with self.assertRaises(ValueError):
            audit(fixture().replace(RECOVERY, "Other"), 2)

    def test_duplicate_recovery(self):
        with self.assertRaises(ValueError):
            audit(fixture().replace(SETTINGS, RECOVERY), 2)

    def test_missing_section(self):
        with self.assertRaises(ValueError):
            audit(fixture().replace("Installed apps", "Something else"), 2)

    def test_bad_order(self):
        with self.assertRaises(ValueError):
            audit(fixture().replace("Device status", "Wrong section"), 2)

    def test_empty_label(self):
        with self.assertRaises(ValueError):
            audit(fixture().replace(SETTINGS, ""), 2)

    def test_small_target(self):
        with self.assertRaises(ValueError):
            audit(fixture(recovery_bounds="[0,0][60,60]"), 2)

    def test_malformed_bounds(self):
        with self.assertRaises(ValueError):
            audit(fixture(recovery_bounds="oops"), 2)

    def test_bad_density(self):
        with self.assertRaises(ValueError):
            audit(fixture(), 0)

    def test_wrong_package(self):
        with self.assertRaises(ValueError):
            audit(fixture().replace("tech.mrnothing.os", "other.package"), 2)

    def test_disabled_action(self):
        with self.assertRaises(ValueError):
            original = node("android.widget.Button", desc=RECOVERY)
            disabled = original.replace('enabled="true"', 'enabled="false"')
            audit(fixture().replace(original, disabled), 2)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "hierarchy.xml"
            o = Path(d) / "result.json"
            p.write_text(fixture())
            subprocess.run([sys.executable, str(ROOT / "scripts/qa012_semantics.py"),
                            "--hierarchy", str(p), "--density", "2", "--output", str(o)],
                           check=True, cwd=ROOT, capture_output=True)
            self.assertFalse(json.loads(o.read_text())["acceptance_passed"])

    def test_emulator_safety(self):
        self.assertIn("Refusing non-emulator target", SHELL)
        self.assertIn("ro.kernel.qemu", SHELL)
        self.assertNotIn("settings put", SHELL)
        self.assertNotIn("cmd role add-role-holder", SHELL)
        self.assertNotIn("pm install", SHELL)
        self.assertIn("qa012_semantics_smoke.sh", WORKFLOW)
