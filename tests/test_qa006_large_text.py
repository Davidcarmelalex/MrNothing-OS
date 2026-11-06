"""QA-006 parser and emulator-only workflow contract tests."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from scripts.qa006_assert_hierarchy import heading_height, verify

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/qa006_large_text_smoke.sh").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/qa005-emulator.yml").read_text(encoding="utf-8")


def hierarchy(height: int, text: str = "MR. NOTHING") -> str:
    return (
        '<hierarchy><node text="' + text + '" bounds="[0,10][100,'
        + str(10 + height) + ']"/></hierarchy>'
    )


class Qa006LargeTextTests(unittest.TestCase):
    def test_height_grows(self):
        with TemporaryDirectory() as directory:
            normal = Path(directory) / "normal.xml"
            large = Path(directory) / "large.xml"
            normal.write_text(hierarchy(30), encoding="utf-8")
            large.write_text(hierarchy(65), encoding="utf-8")
            self.assertEqual(verify(normal, large), (30, 65))

    def test_height_not_growing_is_rejected(self):
        with TemporaryDirectory() as directory:
            normal = Path(directory) / "normal.xml"
            large = Path(directory) / "large.xml"
            normal.write_text(hierarchy(30), encoding="utf-8")
            large.write_text(hierarchy(30), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "did not increase"):
                verify(normal, large)

    def test_missing_heading_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "missing.xml"
            path.write_text(hierarchy(30, "OTHER"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "heading missing"):
                heading_height(path)

    def test_invalid_bounds_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.xml"
            path.write_text('<hierarchy><node text="MR. NOTHING" bounds="bad"/></hierarchy>', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "valid bounds"):
                heading_height(path)

    def test_emulator_only_and_restore_on_exit(self):
        self.assertIn("Refusing non-emulator target", SCRIPT)
        self.assertIn("ro.kernel.qemu", SCRIPT)
        self.assertIn("trap restore_font_scale EXIT", SCRIPT)
        self.assertIn("settings delete system font_scale", SCRIPT)

    def test_runtime_job_includes_large_font_step_and_artifacts(self):
        self.assertIn('name: "QA-006: 200% font and recovery smoke"', WORKFLOW)
        self.assertIn("scripts/qa006_large_text_smoke.sh", WORKFLOW)
        self.assertIn("qa005-emulator-evidence-not-for-release", WORKFLOW)
        self.assertIn("QA006_OUTPUT:", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
