"""Ensure emulator CI checks real installed MemoryVault test execution."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Qa023b1aWorkflowGateTests(unittest.TestCase):
    def test_xml_evidence_gate_follows_connected_instrumentation(self):
        workflow = (ROOT / ".github/workflows/qa005-emulator.yml").read_text(encoding="utf-8")
        connected = workflow.index(":app:connectedDebugAndroidTest")
        gate = workflow.index("python3 ../scripts/qa023b1a_instrumentation_evidence.py")
        next_smoke = workflow.index("Verify launcher runtime and recovery route")
        self.assertLess(connected, gate)
        self.assertLess(gate, next_smoke)
        self.assertIn("app/build/outputs/androidTest-results/connected/debug", workflow)
        self.assertIn("--summary \"$QA005_OUTPUT/memory-vault-instrumentation-summary.json\"", workflow)


if __name__ == "__main__":
    unittest.main()
