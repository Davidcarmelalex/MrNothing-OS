"""SEC-014E static safety boundaries; Android overlay runtime is not tested here."""
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "android/app/src/main/java/tech/mrnothing/os"


class OwnerConsentTouchGateSourceTests(unittest.TestCase):
    def test_preview_blocks_screenshots(self):
        source = (SRC / "OwnerConsentPreviewActivity.kt").read_text()
        self.assertIn("window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)", source)

    def test_buttons_reject_obscured_touches_and_revoke_preview(self):
        source = (SRC / "OwnerConsentPreviewActivity.kt").read_text()
        self.assertIn("filterTouchesWhenObscured = true", source)
        self.assertIn("OwnerConsentTouchGate.isUnobscured(event.flags)", source)
        touch_handler = source.split("setOnTouchListener", 1)[1].split("setOnClickListener", 1)[0]
        self.assertIn("state.revoke()", touch_handler)
        self.assertIn("action = null", touch_handler)
        self.assertIn("true", touch_handler)

    def test_both_obscuration_flags_are_rejected(self):
        gate = (SRC / "OwnerConsentTouchGate.kt").read_text()
        self.assertIn("MotionEvent.FLAG_WINDOW_IS_OBSCURED", gate)
        self.assertIn("MotionEvent.FLAG_WINDOW_IS_PARTIALLY_OBSCURED", gate)

    def test_no_permission_or_execution_added(self):
        gate = (SRC / "OwnerConsentTouchGate.kt").read_text()
        for forbidden in ("CommandRouter", "ConsentCapability", "startActivity", "AccessibilityService", "MediaProjectionManager"):
            self.assertNotIn(forbidden, gate)


if __name__ == "__main__":
    unittest.main()
