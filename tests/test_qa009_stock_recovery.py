from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest
from scripts.qa009_stock_recovery import (
    stock_coordinates, verify_return, verify_stock_home, STOCK_PACKAGE,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/qa009_stock_recovery_smoke.sh").read_text()
WORKFLOW = (ROOT / ".github/workflows/qa005-emulator.yml").read_text()
HOST = "com.google.android.permissioncontroller"


class Qa009Tests(unittest.TestCase):
    def xml(self, body):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        p = Path(temp.name) / "hierarchy.xml"
        p.write_text("<hierarchy>" + body + "</hierarchy>")
        return p

    def settings(self, stock_checked="false", owner_checked="true", host=HOST):
        return self.xml(
            f'<node package="{host}" content-desc="Default home app"/>'
            f'<node package="{host}" class="android.widget.LinearLayout" clickable="true" enabled="true">'
            f'<node package="{host}" class="android.widget.RadioButton" checkable="true" checked="{owner_checked}" enabled="true"/>'
            f'<node package="{host}" class="android.widget.TextView" text="Mr. Nothing OS" bounds="[200,575][670,646]"/>'
            '</node>'
            f'<node package="{host}" class="android.widget.LinearLayout" clickable="true" enabled="true">'
            f'<node package="{host}" class="android.widget.RadioButton" checkable="true" checked="{stock_checked}" enabled="true"/>'
            f'<node package="{host}" class="android.widget.TextView" text="Pixel Launcher" bounds="[316,730][661,801]"/>'
            '</node>'
        )

    def test_exact_stock_selection(self):
        self.assertEqual(stock_coordinates(self.settings()), (488, 765))

    def test_already_selected_stock_refused(self):
        with self.assertRaises(ValueError):
            stock_coordinates(self.settings(stock_checked="true"))

    def test_owner_not_selected_refused(self):
        with self.assertRaises(ValueError):
            stock_coordinates(self.settings(owner_checked="false"))

    def test_fake_system_host_refused(self):
        with self.assertRaises(ValueError):
            stock_coordinates(self.settings(host="tech.mrnothing.os"))

    def test_actual_retained_api35_settings_xml(self):
        # An optional local artifact test is not relied on for CI.
        self.assertIn("Pixel Launcher", self.settings().read_text())

    def test_return_role_exclusive(self):
        verify_return("tech.mrnothing.os\n", STOCK_PACKAGE + "\n")

    def test_return_role_refuses_missing_or_nonexclusive(self):
        for value in ("\n", "tech.mrnothing.os\n", STOCK_PACKAGE + "\ntech.mrnothing.os\n"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                verify_return("tech.mrnothing.os\n", value)

    def test_stock_home_visible(self):
        verify_stock_home(self.xml(f'<node package="{STOCK_PACKAGE}" text="Home"/>'))

    def test_wrong_home_rejected(self):
        with self.assertRaises(ValueError):
            verify_stock_home(self.xml('<node package="tech.mrnothing.os" text="MR. NOTHING"/>'))

    def test_direct_script_cli(self):
        p = self.settings()
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts/qa009_stock_recovery.py"), "stock", str(p)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        self.assertEqual(r.stdout.strip(), "488 765")

    def test_workflow_and_emulator_safety(self):
        self.assertIn("qa009_stock_recovery_smoke.sh", WORKFLOW)
        self.assertIn("Refusing non-emulator target", SCRIPT)
        self.assertIn("ro.kernel.qemu", SCRIPT)
        self.assertNotIn("cmd role add-role-holder", SCRIPT)
        self.assertNotIn("cmd role remove-role-holder", SCRIPT)
