import unittest
from pathlib import Path
from scripts.launcher_accessibility_gate import check, contrast_ratio

SOURCE = Path("android/app/src/main/java/tech/mrnothing/os/MainActivity.kt")

class LauncherAccessibilityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_source_passes(self):
        self.assertEqual([], check(self.source))

    def test_missing_home_recovery_fails(self):
        source = self.source.replace("Settings.ACTION_HOME_SETTINGS", "Settings.ACTION_SETTINGS")
        self.assertTrue(any("recovery" in x for x in check(source)))

    def test_low_contrast_fails(self):
        source = self.source.replace(
            "private val secondaryTextColor = Color.rgb(206, 210, 226)",
            "private val secondaryTextColor = Color.rgb(15, 15, 15)"
        )
        self.assertTrue(any("secondaryTextColor" in x for x in check(source)))

    def test_touch_target_regression_fails(self):
        self.assertTrue(any("touch targets" in x for x in check(
            self.source.replace("minHeight = dp(56)", "minHeight = dp(32)")
        )))

    def test_contrast_math(self):
        self.assertAlmostEqual(21.0, contrast_ratio((0, 0, 0), (255, 255, 255)), places=2)
        self.assertAlmostEqual(1.0, contrast_ratio((0, 0, 0), (0, 0, 0)), places=2)

if __name__ == "__main__":
    unittest.main()
