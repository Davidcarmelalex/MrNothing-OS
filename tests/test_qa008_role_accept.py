from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import subprocess
import sys
from scripts.qa008_role_accept import approve_coordinates, verify_granted, verify_home, verify_settings

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/qa008_role_accept_smoke.sh").read_text()
WORKFLOW = (ROOT / ".github/workflows/qa005-emulator.yml").read_text()

class Qa008Tests(unittest.TestCase):
    def xml(self, *nodes):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        p = Path(temp.name) / "test.xml"
        p.write_text("<hierarchy>" + "".join(nodes) + "</hierarchy>")
        return p

    def prompt(self, button):
        return self.xml(
            '<node package="com.google.android.permissioncontroller" text="Mr. Nothing OS"/>',
            button)

    def test_direct_script_cli_import_and_coordinates(self):
        """Regression: GitHub Actions invokes the file, not python -m."""
        p = self.prompt('<node package="com.google.android.permissioncontroller" text="Set as default" clickable="true" enabled="true" bounds="[10,20][110,80]"/>')
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/qa008_role_accept.py"), "approve", str(p)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        self.assertEqual(result.stdout.strip(), "60 50")

    def test_module_cli_import_and_coordinates(self):
        p = self.prompt('<node package="com.google.android.permissioncontroller" text="Set as default" clickable="true" enabled="true" bounds="[10,20][110,80]"/>')
        result = subprocess.run(
            [sys.executable, "-m", "scripts.qa008_role_accept", "approve", str(p)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        self.assertEqual(result.stdout.strip(), "60 50")

    def test_approve_system_control(self):
        p = self.prompt('<node package="com.google.android.permissioncontroller" text="Set as default" clickable="true" enabled="true" bounds="[10,20][110,80]"/>')
        self.assertEqual(approve_coordinates(p), (60, 50))

    def test_reject_fake_app_button(self):
        p = self.prompt('<node package="tech.mrnothing.os" text="Allow" clickable="true" enabled="true" bounds="[10,20][110,80]"/>')
        with self.assertRaises(ValueError): approve_coordinates(p)

    def test_reject_cancel_button(self):
        p = self.prompt('<node package="com.google.android.permissioncontroller" text="Cancel" clickable="true" enabled="true" bounds="[10,20][110,80]"/>')
        with self.assertRaises(ValueError): approve_coordinates(p)

    def test_reject_ambiguous_buttons(self):
        p = self.prompt('<node package="com.google.android.permissioncontroller" text="Allow" clickable="true" enabled="true" bounds="[10,20][110,80]"/><node package="com.google.android.permissioncontroller" text="OK" clickable="true" enabled="true" bounds="[120,20][220,80]"/>')
        with self.assertRaises(ValueError): approve_coordinates(p)

    def test_exclusive_grant(self):
        verify_granted("com.google.android.apps.nexuslauncher\n", "tech.mrnothing.os\n")

    def test_reject_missing_grant(self):
        with self.assertRaises(ValueError):
            verify_granted("com.google.android.apps.nexuslauncher\n", "com.google.android.apps.nexuslauncher\n")

    def test_home_visible(self):
        verify_home(self.xml('<node package="tech.mrnothing.os" text="MR. NOTHING"/>'))

    def test_wrong_home_rejected(self):
        with self.assertRaises(ValueError):
            verify_home(self.xml('<node package="another.app" text="MR. NOTHING"/>'))

    def test_stock_settings_visible(self):
        verify_settings(self.xml('<node package="com.android.settings" text="Default home app"/>'))

    def test_fake_settings_rejected(self):
        with self.assertRaises(ValueError):
            verify_settings(self.xml('<node package="tech.mrnothing.os" text="Settings"/>'))

    def test_physical_device_refused(self):
        self.assertIn("Refusing non-emulator target", SCRIPT)
        self.assertIn("ro.kernel.qemu", SCRIPT)
        self.assertNotIn("cmd role add-role-holder", SCRIPT)
        self.assertIn("scripts/qa008_role_accept_smoke.sh", WORKFLOW)
