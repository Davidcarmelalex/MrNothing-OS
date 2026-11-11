"""QA-007 parser and non-consent safety regression tests."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from scripts.qa007_role_consent import (
    tap_coordinates, verify_consent_prompt, verify_no_implicit_grant, classify_consent_screen,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/qa007_role_consent_smoke.sh").read_text()
WORKFLOW = (ROOT / ".github/workflows/qa005-emulator.yml").read_text()


def hierarchy(*nodes: str) -> str:
    return "<hierarchy>" + "".join(nodes) + "</hierarchy>"


class Qa007ConsentTests(unittest.TestCase):
    def xml(self, content: str):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        p = Path(temp.name) / "hierarchy.xml"
        p.write_text(content)
        return p

    def test_tap_center_from_accessible_button(self):
        p = self.xml(hierarchy('<node text="Choose Mr. Nothing as Home" clickable="true" enabled="true" bounds="[10,20][110,80]"/>'))
        self.assertEqual(tap_coordinates(p), (60, 50))

    def test_missing_or_disabled_button_fails_closed(self):
        p = self.xml(hierarchy('<node text="Choose Mr. Nothing as Home" clickable="false" enabled="true" bounds="[10,20][110,80]"/>'))
        with self.assertRaisesRegex(ValueError, "not enabled"):
            tap_coordinates(p)

    def test_empty_bounds_fails_closed(self):
        p = self.xml(hierarchy('<node text="Choose Mr. Nothing as Home" clickable="true" enabled="true" bounds="[10,20][10,80]"/>'))
        with self.assertRaisesRegex(ValueError, "empty bounds"):
            tap_coordinates(p)

    def test_permission_controller_prompt(self):
        p = self.xml(hierarchy('<node package="com.google.android.permissioncontroller" text="Set Mr. Nothing OS as default home?" />'))
        verify_consent_prompt(p)

    def test_non_system_prompt_rejected(self):
        p = self.xml(hierarchy('<node package="tech.mrnothing.os" text="Mr. Nothing OS" />'))
        with self.assertRaisesRegex(ValueError, "permission controller"):
            verify_consent_prompt(p)

    def test_state_recognizes_launcher_only_when_chooser_is_clickable(self):
        p = self.xml(hierarchy('<node package="tech.mrnothing.os" text="Choose Mr. Nothing as Home" clickable="true" enabled="true" bounds="[10,20][110,80]"/>'))
        self.assertEqual(classify_consent_screen(p), "launcher")

    def test_state_recognizes_actual_permission_controller_prompt(self):
        p = self.xml(hierarchy('<node package="com.google.android.permissioncontroller" text="Set Mr. Nothing OS as default home?" />'))
        self.assertEqual(classify_consent_screen(p), "prompt")

    def test_state_rejects_unexpected_overlay(self):
        p = self.xml(hierarchy('<node package="com.android.systemui" text="Choose Mr. Nothing as Home" clickable="true" enabled="true" bounds="[10,20][110,80]"/>'))
        with self.assertRaisesRegex(ValueError, "Unexpected foreground"):
            classify_consent_screen(p)

    def test_state_rejects_mixed_launcher_and_unknown_window(self):
        p = self.xml(hierarchy('<node package="tech.mrnothing.os" text="Choose Mr. Nothing as Home" clickable="true" enabled="true" bounds="[10,20][110,80]"/><node package="com.android.systemui"/>'))
        with self.assertRaisesRegex(ValueError, "Unexpected foreground"):
            classify_consent_screen(p)

    def test_state_rejects_permission_controller_without_target(self):
        p = self.xml(hierarchy('<node package="com.google.android.permissioncontroller" text="Unrelated role" />'))
        with self.assertRaisesRegex(ValueError, "not identified"):
            classify_consent_screen(p)

    def test_dismissal_keeps_role(self):
        verify_no_implicit_grant("com.google.android.apps.nexuslauncher\n", "com.google.android.apps.nexuslauncher\n")

    def test_role_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "changed"):
            verify_no_implicit_grant("com.google.android.apps.nexuslauncher\n", "tech.mrnothing.os\n")

    def test_script_emulator_only_and_never_forces_role(self):
        self.assertIn("Refusing non-emulator target", SCRIPT)
        self.assertIn("ro.kernel.qemu", SCRIPT)
        self.assertIn("KEYCODE_BACK", SCRIPT)
        self.assertEqual(SCRIPT.count("cmd role get-role-holders android.app.role.HOME"), 3)
        self.assertNotIn("cmd role add-role-holder", "\n".join(line for line in SCRIPT.splitlines() if not line.lstrip().startswith("#")))
        self.assertIn("scripts/qa007_role_consent_smoke.sh", WORKFLOW)
        self.assertIn("for attempt in 1 2", SCRIPT)
        self.assertIn("qa007_role_consent.py state", SCRIPT)
        self.assertIn("role-before-retry.txt", SCRIPT)

if __name__ == "__main__":
    unittest.main()
