"""QA-STACK-037: exact source of emulator UX evidence after split Gradle runs."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/qa005-emulator.yml"
BRANCH = "feat/qa-stack037-ux-evidence-20261114"
REPO = "Davidcarmelalex/MrNothing-OS"
MANUAL = (
    f"(github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/{BRANCH}' "
    f"&& github.repository == '{REPO}')"
)


class Stack037EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_ux_gate_consumes_preserved_uncredentialed_suite_not_overwritten_live_xml(self):
        source = self.workflow
        preserve = source.index('cp -a app/build/outputs/androidTest-results/connected/debug/.')
        credential = source.index('SEC-020B4D: Activity destruction before/after trust commit claim')
        ux = source.index('QA-STACK-008: require executed UX rehearsal instrumentation')
        split = source.index('QA-STACK-011: require complete split instrumentation evidence')
        self.assertLess(preserve, credential)
        self.assertLess(credential, ux)
        self.assertLess(ux, split)
        step = source[ux:split]
        self.assertIn('"$QA005_OUTPUT/uncredentialed-instrumentation"', step)
        self.assertNotIn('            app/build/outputs/androidTest-results/connected/debug', step)
        self.assertIn('--require-ux-rehearsal', step)
        self.assertIn('--summary "$QA005_OUTPUT/ux-rehearsal-instrumentation-summary.json"', step)

    def test_split_gate_retains_both_suites_and_fail_closed_verifier(self):
        source = self.workflow
        split = source.index('QA-STACK-011: require complete split instrumentation evidence')
        smoke = source.index('Verify launcher runtime and recovery route', split)
        step = source[split:smoke]
        self.assertIn('scripts/qa_stack011_instrumentation_evidence.py', step)
        self.assertIn('"$QA005_OUTPUT/uncredentialed-instrumentation"', step)
        self.assertIn('android/app/build/outputs/androidTest-results/connected/debug', step)
        self.assertNotIn('|| true', step)

    def test_scoped_manual_emulator_run_has_no_widened_automatic_triggers(self):
        source = self.workflow
        job = next(line for line in source.splitlines() if line.startswith('    if: '))
        ux_start = source.index('QA-STACK-008: require executed UX rehearsal instrumentation')
        ux_end = source.index('QA-STACK-011: require complete split instrumentation evidence')
        ux_gate = next(line for line in source[ux_start:ux_end].splitlines() if line.startswith('        if: '))
        self.assertEqual(job.count(MANUAL), 1)
        self.assertEqual(ux_gate.count(MANUAL), 1)
        self.assertIn('permissions:\n  contents: read', source)
        self.assertNotIn('pull_request_target', source)
        self.assertIn('cancel-in-progress: false', source)


if __name__ == "__main__":
    unittest.main()
