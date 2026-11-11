"""Structural no-execution guards; Kotlin/JVM CI is a separate acceptance gate."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "android/app/src/main/java/tech/mrnothing/os"


class NoOpSupervisorSourceGate(unittest.TestCase):
    def test_supervisor_has_only_blocked_verdicts_and_no_device_bridge(self):
        source = (SOURCE / "AgentNoOpSupervisor.kt").read_text()
        self.assertNotIn("import android.", source)
        self.assertNotIn("ALLOWED", source)
        self.assertNotIn("GRANTED", source)
        for token in (
            "CommandRouter(", "startActivity(", "Intent(", "requestPermissions(",
            "Runtime.getRuntime(", "ProcessBuilder(", "execute(", "sendMessage("
        ):
            self.assertNotIn(token, source)
        self.assertIn("val authorized: Boolean get() = false", source)
        self.assertIn("val deviceActionsExecuted: Boolean get() = false", source)

    def test_completed_plan_is_terminal_even_if_snapshot_contains_step(self):
        source = (SOURCE / "AgentNoOpSupervisor.kt").read_text()
        self.assertIn("RehearsalPhase.COMPLETE, RehearsalPhase.CANCELLED", source)
        self.assertIn("NoOpSupervisorVerdict.BLOCKED_TERMINAL_REHEARSAL", source)

    def test_owner_visible_activity_uses_deny_only_gate(self):
        activity = (SOURCE / "AgentPlanPreviewActivity.kt").read_text()
        self.assertIn("AgentNoOpSupervisor.inspect(snapshot)", activity)
        self.assertIn("Supervisor gate:", activity)
        self.assertIn("No consent granted.", activity)


if __name__ == "__main__":
    unittest.main()
