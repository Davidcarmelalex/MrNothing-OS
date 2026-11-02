from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import subprocess
import sys
from scripts.qa008_role_accept import approve_coordinates, select_coordinates, verify_granted, verify_home, verify_settings

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

    def selection_prompt(self, label="Mr. Nothing OS", radio_checked="false"):
        return self.prompt(
            '<node package="com.google.android.permissioncontroller" class="android.widget.LinearLayout">'
            '<node package="com.google.android.permissioncontroller" class="android.widget.TextView" text="' + label + '" bounds="[200,840][540,920]"/>'
            '<node package="com.google.android.permissioncontroller" class="android.widget.RadioButton" checkable="true" checked="' + radio_checked + '" enabled="true" bounds="[860,840][945,920]"/>'
            '</node>'
            '<node package="com.google.android.permissioncontroller" class="android.widget.LinearLayout">'
            '<node package="com.google.android.permissioncontroller" class="android.widget.TextView" text="Pixel Launcher" bounds="[200,1010][540,1090]"/>'
            '<node package="com.google.android.permissioncontroller" class="android.widget.RadioButton" checkable="true" checked="false" enabled="true" bounds="[860,1010][945,1090]"/>'
            '</node>'
            '<node package="com.google.android.permissioncontroller" text="Set as default" clickable="true" enabled="false" bounds="[690,1273][978,1415]"/>'
        )

    def test_select_exact_system_home_option(self):
        self.assertEqual(select_coordinates(self.selection_prompt()), (370, 880))

    def test_select_rejects_already_selected_option(self):
        with self.assertRaises(ValueError):
            select_coordinates(self.selection_prompt(radio_checked="true"))

    def test_select_rejects_wrong_app(self):
        with self.assertRaises(ValueError):
            select_coordinates(self.selection_prompt(label="Other Launcher"))

    def test_approve_rejects_disabled_control(self):
        with self.assertRaises(ValueError):
            approve_coordinates(self.selection_prompt())

    def test_script_selects_before_approving(self):
        self.assertLess(SCRIPT.index("qa008_role_accept.py select"), SCRIPT.index("qa008_role_accept.py approve"))
        self.assertIn("qa008-selected.xml", SCRIPT)

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

    def test_exclusive_grant_from_unassigned_home_role(self):
        # GitHub Actions 41407548448: role-before was exactly b"\n";
        # role-after was b"tech.mrnothing.os\n". Android consent succeeded.
        verify_granted("\n", "tech.mrnothing.os\n")
        verify_granted("", "tech.mrnothing.os\n")

    def test_reject_preexisting_our_home_role(self):
        with self.assertRaises(ValueError):
            verify_granted("tech.mrnothing.os\n", "tech.mrnothing.os\n")

    def test_reject_nonexclusive_after_grant(self):
        with self.assertRaises(ValueError):
            verify_granted("\n", "tech.mrnothing.os\ncom.google.android.apps.nexuslauncher\n")

    def test_cli_grant_accepts_empty_before_role_snapshot(self):
        with TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.txt"
            after = Path(tmp) / "after.txt"
            before.write_text("\n")
            after.write_text("tech.mrnothing.os\n")
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/qa008_role_accept.py"),
                 "granted", str(before), str(after)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )

    def test_reject_missing_grant(self):
        with self.assertRaises(ValueError):
            verify_granted("com.google.android.apps.nexuslauncher\n", "com.google.android.apps.nexuslauncher\n")

    def test_home_visible(self):
        verify_home(self.xml('<node package="tech.mrnothing.os" text="MR. NOTHING"/>'))

    def test_wrong_home_rejected(self):
        with self.assertRaises(ValueError):
            verify_home(self.xml('<node package="another.app" text="MR. NOTHING"/>'))

    def settings_page(self, package="com.google.android.permissioncontroller",
                      heading=True, stock=True):
        # Minimal regression fixture derived from the actual API 35
        # qa008/settings.xml in GitHub Actions run 41413940072.
        nodes = []
        if heading:
            nodes.append(f'<node package="{package}" class="android.widget.FrameLayout" content-desc="Default home app"/>')
        nodes.append(f'<node package="{package}" class="android.widget.TextView" text="Mr. Nothing OS"/>')
        if stock:
            nodes.append(f'<node package="{package}" class="android.widget.TextView" text="Pixel Launcher"/>')
        return self.xml(*nodes)

    def test_real_api35_permissioncontroller_settings_visible(self):
        verify_settings(self.settings_page())

    def test_android_settings_host_supported(self):
        verify_settings(self.settings_page(package="com.android.settings"))

    def test_aosp_permissioncontroller_host_supported(self):
        verify_settings(self.settings_page(package="com.android.permissioncontroller"))

    def test_settings_missing_heading_rejected(self):
        with self.assertRaises(ValueError):
            verify_settings(self.settings_page(heading=False))

    def test_settings_missing_stock_launcher_rejected(self):
        with self.assertRaises(ValueError):
            verify_settings(self.settings_page(stock=False))

    def test_fake_settings_host_rejected_even_with_matching_labels(self):
        with self.assertRaises(ValueError):
            verify_settings(self.settings_page(package="tech.mrnothing.os"))

    def test_fake_settings_rejected(self):
        with self.assertRaises(ValueError):
            verify_settings(self.xml('<node package="tech.mrnothing.os" text="Settings"/>'))

    def test_physical_device_refused(self):
        self.assertIn("Refusing non-emulator target", SCRIPT)
        self.assertIn("ro.kernel.qemu", SCRIPT)
        self.assertNotIn("cmd role add-role-holder", SCRIPT)
        self.assertIn("scripts/qa008_role_accept_smoke.sh", WORKFLOW)
