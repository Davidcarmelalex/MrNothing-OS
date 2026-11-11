"""Structural non-execution checks; not a substitute for Android/JVM CI."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'android/app/src/main/java/tech/mrnothing/os'


class RehearsalSourceGate(unittest.TestCase):
    def test_rehearsal_has_no_executor_or_android_imports(self):
        source = (SOURCE / 'AgentPlanRehearsal.kt').read_text()
        self.assertNotIn('import android.', source)
        for token in ('CommandRouter(', 'Intent(', 'startActivity(', 'execute(',
                      'sendMessage(', 'requestPermissions(', 'Runtime.getRuntime('):
            self.assertNotIn(token, source)
        self.assertIn('val authorized: Boolean get() = false', source)
        self.assertIn('val deviceActionsExecuted: Boolean get() = false', source)

    def test_begin_expires_stale_active_plan_before_replacement(self):
        source = (SOURCE / 'AgentPlanRehearsal.kt').read_text()
        begin = source.split('fun begin(sampleActions: List<String>): RehearsalSnapshot {', 1)[1]
        begin = begin.split('fun acknowledgeSampleReview()', 1)[0]
        self.assertLess(begin.index('if (expireIfNeeded()) return snapshotWithoutClock()'),
                        begin.index('if (phase in setOf('))

    def test_launcher_clears_rehearsal_on_stop(self):
        source = (SOURCE / 'AgentPlanPreviewActivity.kt').read_text()
        self.assertIn('rehearsal.cancel()', source)
        self.assertIn('override fun onStop()', source)
        self.assertIn('No consent granted.', source)


if __name__ == '__main__':
    unittest.main()
