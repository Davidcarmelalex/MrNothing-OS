"""Unit tests for the fail-closed Android 15 QA-005 wake-state parser."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/qa005_power_state.py"
sys.path.insert(0, str(ROOT / "scripts"))

from qa005_power_state import inspect_power_state  # noqa: E402


VALID = """\
Power Manager State:
  mWakefulness=Awake
  mWakefulnessChanging=false
  mHalInteractiveModeEnabled=true
  mLastWakeTime=32654 (22892 ms ago)
"""


class Qa005PowerStateTests(unittest.TestCase):
    def test_accepts_settled_android15_power_manager_snapshot(self):
        settled, age, reason = inspect_power_state(VALID, 1500)
        self.assertTrue(settled, reason)
        self.assertEqual(22892, age)

    def test_rejects_sleeping_display(self):
        settled, age, reason = inspect_power_state(
            VALID.replace("mWakefulness=Awake", "mWakefulness=Asleep")
        )
        self.assertFalse(settled)
        self.assertIsNone(age)
        self.assertIn("mWakefulness", reason)

    def test_rejects_wake_transition_in_progress(self):
        settled, age, reason = inspect_power_state(
            VALID.replace("mWakefulnessChanging=false", "mWakefulnessChanging=true")
        )
        self.assertFalse(settled)
        self.assertIsNone(age)
        self.assertIn("mWakefulnessChanging", reason)

    def test_rejects_noninteractive_hal(self):
        settled, age, reason = inspect_power_state(
            VALID.replace("mHalInteractiveModeEnabled=true", "mHalInteractiveModeEnabled=false")
        )
        self.assertFalse(settled)
        self.assertIsNone(age)
        self.assertIn("mHalInteractiveModeEnabled", reason)

    def test_rejects_wake_age_below_threshold(self):
        settled, age, reason = inspect_power_state(
            VALID.replace("22892 ms ago", "1499 ms ago"), 1500
        )
        self.assertFalse(settled)
        self.assertEqual(1499, age)
        self.assertIn("below", reason)

    def test_accepts_exact_minimum_wake_age(self):
        settled, age, reason = inspect_power_state(
            VALID.replace("22892 ms ago", "1500 ms ago"), 1500
        )
        self.assertTrue(settled, reason)
        self.assertEqual(1500, age)

    def test_rejects_missing_or_malformed_wake_age(self):
        for snapshot in (
            VALID.replace("  mLastWakeTime=32654 (22892 ms ago)\n", ""),
            VALID.replace("22892 ms ago", "unknown"),
        ):
            with self.subTest(snapshot=snapshot):
                settled, age, reason = inspect_power_state(snapshot)
                self.assertFalse(settled)
                self.assertIsNone(age)
                self.assertIn("mLastWakeTime", reason)

    def test_rejects_ambiguous_duplicate_power_fields(self):
        snapshot = VALID.replace(
            "  mWakefulness=Awake\n",
            "  mWakefulness=Awake\n  mWakefulness=Awake\n",
        )
        settled, age, reason = inspect_power_state(snapshot)
        self.assertFalse(settled)
        self.assertIsNone(age)
        self.assertIn("ambiguous", reason)

    def test_rejects_negative_minimum_age_configuration(self):
        settled, age, reason = inspect_power_state(VALID, -1)
        self.assertFalse(settled)
        self.assertIsNone(age)
        self.assertIn("negative", reason)

    def test_cli_reads_snapshot_from_stdin_and_supports_quiet_success(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--min-wake-age-ms", "1500", "--quiet"],
            input=VALID,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_cli_rejects_unsettled_snapshot(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--min-wake-age-ms", "1500", "--quiet"],
            input=VALID.replace("22892 ms ago", "1499 ms ago"),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("below", result.stderr)


if __name__ == "__main__":
    unittest.main()
