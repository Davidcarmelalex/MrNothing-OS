from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest
from scripts.qa010_accessibility import RECOVERY, SETTINGS, baseline, focused, sequence

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/qa010_keyboard_navigation_smoke.sh").read_text()
WORKFLOW = (ROOT / ".github/workflows/qa005-emulator.yml").read_text()


class Qa010Tests(unittest.TestCase):
    def xml(self, focus="", label=True, recovery=True):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = Path(tmp.name) / "hierarchy.xml"
        buttons = []
        for name in (RECOVERY if recovery else "Other", SETTINGS):
            desc = name if label else ""
            buttons.append(f'<node package="tech.mrnothing.os" class="android.widget.Button" '
                           f'clickable="true" enabled="true" focusable="true" '
                           f'focused="{str(name == focus).lower()}" content-desc="{desc}"/>')
        p.write_text("<hierarchy>" + "".join(buttons) + "</hierarchy>")
        return p

    def test_baseline(self):
        baseline(self.xml())

    def test_missing_label_refused(self):
        with self.assertRaises(ValueError):
            baseline(self.xml(label=False))

    def test_missing_recovery_refused(self):
        with self.assertRaises(ValueError):
            baseline(self.xml(recovery=False))

    def test_duplicate_refused(self):
        p = self.xml()
        p.write_text(p.read_text().replace(SETTINGS, RECOVERY))
        with self.assertRaises(ValueError):
            baseline(p)

    def test_focused(self):
        self.assertEqual(focused(self.xml(focus=RECOVERY)), RECOVERY)
        self.assertEqual(focused(self.xml()), "")

    def test_sequence(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        (d / "focus-1.xml").write_text(self.xml(focus=SETTINGS).read_text())
        (d / "focus-2.xml").write_text(self.xml(focus=RECOVERY).read_text())
        sequence(self.xml(), d)

    def test_sequence_missing_recovery_refused(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        (d / "focus-1.xml").write_text(self.xml(focus=SETTINGS).read_text())
        (d / "focus-2.xml").write_text(self.xml().read_text())
        with self.assertRaises(ValueError):
            sequence(self.xml(), d)

    def test_cli(self):
        p = self.xml(focus=RECOVERY)
        out = subprocess.check_output([sys.executable, str(ROOT / "scripts/qa010_accessibility.py"),
                                       "focus", str(p)], cwd=ROOT, text=True)
        self.assertEqual(out.strip(), RECOVERY)

    def test_emulator_safety(self):
        self.assertIn("Refusing non-emulator target", SCRIPT)
        self.assertIn("ro.kernel.qemu", SCRIPT)
        self.assertIn("KEYCODE_TAB", SCRIPT)
        self.assertNotIn("settings put secure", SCRIPT)
        self.assertNotIn("cmd role add-role-holder", SCRIPT)
        self.assertIn("qa010_keyboard_navigation_smoke.sh", WORKFLOW)
