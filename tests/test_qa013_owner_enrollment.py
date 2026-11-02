"""QA-013 unit tests; Android runtime evidence requires emulator CI."""
from pathlib import Path
import unittest
from scripts.qa013_owner_enrollment import find_button, assert_status

ROOT = Path(__file__).resolve().parents[1]
DESC = "Owner button"
BUTTON = '<node package="tech.mrnothing.os" class="android.widget.Button" content-desc="Owner button" enabled="true" clickable="true" bounds="[20,40][200,120]"/>'
STATUS = '<node package="tech.mrnothing.os" class="android.widget.TextView" text="Denied"/>'


class Qa013Tests(unittest.TestCase):
    def test_button(self):
        self.assertEqual(find_button("<hierarchy>"+BUTTON+"</hierarchy>", DESC), (110, 80))

    def test_missing_and_duplicate(self):
        for s in ("", BUTTON+BUTTON):
            with self.assertRaises(ValueError):
                find_button("<hierarchy>"+s+"</hierarchy>", DESC)

    def test_malformed_bounds(self):
        for bad in ("oops", "[20,20][10,10]"):
            with self.assertRaises(ValueError):
                find_button("<hierarchy>"+BUTTON.replace("[20,40][200,120]", bad)+"</hierarchy>", DESC)

    def test_wrong_package_and_disabled(self):
        for bad in (BUTTON.replace("tech.mrnothing.os", "other"), BUTTON.replace('enabled="true"', 'enabled="false"')):
            with self.assertRaises(ValueError):
                find_button("<hierarchy>"+bad+"</hierarchy>", DESC)

    def test_status(self):
        assert_status("<hierarchy>"+STATUS+"</hierarchy>", "Denied")
        with self.assertRaises(ValueError):
            assert_status("<hierarchy>"+STATUS+"</hierarchy>", "Enrolled")

    def test_emulator_safety(self):
        shell = (ROOT/"scripts/qa013_owner_enrollment_smoke.sh").read_text()
        workflow = (ROOT/".github/workflows/qa005-emulator.yml").read_text()
        for token in ("Refusing non-emulator target", "ro.kernel.qemu", "secure lock required. Refused."):
            self.assertIn(token, shell)
        for forbidden in ("settings put", "locksettings set-", "adb root", "pm grant", "generateKeyPair"):
            self.assertNotIn(forbidden, shell)
        self.assertIn("qa013_owner_enrollment_smoke.sh", workflow)
