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

    def test_scroll_snapshots_reveal_offscreen_section_and_dedupe_overlap(self):
        text = lambda value: node("android.widget.TextView", text=value)
        button = lambda desc: node("android.widget.Button", desc=desc)
        top = "<hierarchy>" + text("MR. NOTHING") + text("Device status") + button(RECOVERY) + button(SETTINGS) + "</hierarchy>"
        bottom = "<hierarchy>" + button(SETTINGS) + text("Installed apps") + "</hierarchy>"
        result = audit([top, bottom], 2)
        self.assertTrue(result["structural_checks_passed"])
        self.assertEqual(2, result["hierarchy_snapshots"])
        self.assertEqual(2, result["action_count"])

    def test_duplicate_action_within_one_viewport_is_not_hidden(self):
        text = lambda value: node("android.widget.TextView", text=value)
        button = lambda desc: node("android.widget.Button", desc=desc)
        xml = ("<hierarchy>" + text("MR. NOTHING") + text("Device status") +
               button(RECOVERY) + button(RECOVERY) + button(SETTINGS) +
               text("Installed apps") + "</hierarchy>")
        with self.assertRaisesRegex(ValueError, "duplicate system action"):
            audit(xml, 2)

    def test_duplicate_action_in_later_viewport_is_not_hidden_by_overlap(self):
        text = lambda value: node("android.widget.TextView", text=value)
        button = lambda desc: node("android.widget.Button", desc=desc)
        top = ("<hierarchy>" + text("MR. NOTHING") + text("Device status") +
               button(RECOVERY) + button(SETTINGS) + "</hierarchy>")
        bottom = ("<hierarchy>" + button(RECOVERY) + button(RECOVERY) +
                  button(SETTINGS) + text("Installed apps") + "</hierarchy>")
        with self.assertRaisesRegex(ValueError, "duplicate system action"):
            audit([top, bottom], 2)

    def test_missing_section_across_all_snapshots(self):
        text = lambda value: node("android.widget.TextView", text=value)
        button = lambda desc: node("android.widget.Button", desc=desc)
        top = "<hierarchy>" + text("MR. NOTHING") + text("Device status") + button(RECOVERY) + button(SETTINGS) + "</hierarchy>"
        bottom = "<hierarchy>" + text("No apps") + "</hierarchy>"
        with self.assertRaisesRegex(ValueError, "Installed apps"):
            audit([top, bottom], 2)

    def test_cli_accepts_multiple_viewports(self):
        with tempfile.TemporaryDirectory() as d:
            top = Path(d) / "top.xml"
            bottom = Path(d) / "bottom.xml"
            output = Path(d) / "result.json"
            text = lambda value: node("android.widget.TextView", text=value)
            button = lambda desc: node("android.widget.Button", desc=desc)
            top.write_text("<hierarchy>" + text("MR. NOTHING") + text("Device status") + button(RECOVERY) + button(SETTINGS) + "</hierarchy>")
            bottom.write_text("<hierarchy>" + text("Installed apps") + "</hierarchy>")
            subprocess.run([sys.executable, str(ROOT / "scripts/qa012_semantics.py"),
                            "--hierarchy", str(top), "--hierarchy", str(bottom),
                            "--density", "2", "--output", str(output)],
                           check=True, cwd=ROOT, capture_output=True)
            result = json.loads(output.read_text())
            self.assertEqual(2, result["hierarchy_snapshots"])
            self.assertFalse(result["acceptance_passed"])

    def test_shell_captures_top_and_bounded_bottom_viewports(self):
        self.assertIn('--hierarchy "$QA012_OUTPUT/top-hierarchy.xml"', SHELL)
        self.assertIn('set -- "$@" --hierarchy "$QA012_OUTPUT/bottom-hierarchy.xml"', SHELL)
        self.assertIn('input swipe "$scroll_x" "$scroll_start_y" "$scroll_x" "$scroll_end_y" 400', SHELL)
        self.assertIn("for attempt in 1 2 3 4 5", SHELL)

    def test_emulator_safety(self):
        self.assertIn("Refusing non-emulator target", SHELL)
        self.assertIn("ro.kernel.qemu", SHELL)
        self.assertNotIn("settings put", SHELL)
        self.assertNotIn("cmd role add-role-holder", SHELL)
        self.assertNotIn("pm install", SHELL)
        self.assertIn("am start -W -S -n tech.mrnothing.os/.MainActivity", SHELL)
        self.assertIn("qa012_semantics_smoke.sh", WORKFLOW)
