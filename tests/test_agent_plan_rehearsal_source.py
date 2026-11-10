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

    def test_launcher_clears_rehearsal_on_stop(self):
        source = (SOURCE / 'AgentPlanPreviewActivity.kt').read_text()
        self.assertIn('rehearsal.cancel()', source)
        self.assertIn('override fun onStop()', source)
        self.assertIn('No consent granted.', source)


if __name__ == '__main__':
    unittest.main()
