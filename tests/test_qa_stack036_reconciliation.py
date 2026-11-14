"""QA-STACK-036: fail-closed review gates for combining security and CI diagnostics.

Static checks do not constitute independent security review, an emulator run,
or a reproducible Android build.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/qa-stack036-reconcile-ci-ux-20261114"
REPO = "Davidcarmelalex/MrNothing-OS"
MANUAL = (
    "(github.event_name == 'workflow_dispatch' && "
    f"github.ref == 'refs/heads/{BRANCH}' && github.repository == '{REPO}')"
)


class Stack036ReconciliationTests(unittest.TestCase):
    def test_ci003_jobs_preserve_strict_repro_and_exact_scoped_manual_gate(self):
        source = (ROOT / ".github/workflows/ci003-reproducibility.yml").read_text()
        self.assertIn("branches: [main, feat/phase1-agentic-phone, feat/qa-stack008-ux-memoryvault-integration-20261113]", source)
        self.assertNotIn("pull_request_target", source)
        self.assertIn("permissions:\n  contents: read", source)
        self.assertNotIn("contents: write", source)
        self.assertIn("build_environment_sbom.py verify", source)
        self.assertIn("ci003_artifacts.py verify", source)
        self.assertIn("cancel-in-progress: false", source)
        for part in (source.split("  build:", 1)[1].split("  verify-independent-runners:", 1)[0],
                     source.split("  verify-independent-runners:", 1)[1]):
            gate = next(x for x in part.splitlines() if x.startswith("    if: "))
            self.assertEqual(gate.count(MANUAL), 1)
            self.assertIn("ref: " + "$" + "{{ github.event.pull_request.head.sha || github.sha }}", part)
            self.assertIn('run: test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"', part)

    def test_qa005_keeps_both_ux_and_split_instrumentation_gates(self):
        source = (ROOT / ".github/workflows/qa005-emulator.yml").read_text()
        self.assertIn("branches: [main, feat/phase1-agentic-phone]", source)
        self.assertNotIn("  push:", source)
        self.assertNotIn("pull_request_target", source)
        self.assertIn("permissions:\n  contents: read", source)
        self.assertIn("cancel-in-progress: false", source)
        gate = next(x for x in source.splitlines() if x.startswith("    if: "))
        self.assertEqual(gate.count(MANUAL), 1)
        self.assertIn("QA-STACK-008: require executed UX rehearsal instrumentation", source)
        self.assertIn("QA-STACK-011: require complete split instrumentation evidence", source)
        self.assertLess(source.index("QA-STACK-008: require executed UX rehearsal instrumentation"),
                        source.index("QA-STACK-011: require complete split instrumentation evidence"))
        self.assertLess(source.index("QA-STACK-011: require complete split instrumentation evidence"),
                        source.index("Verify launcher runtime and recovery route"))
        self.assertIn("--require-ux-rehearsal", source)

    def test_security_ledger_and_admission_modules_survive_reconciliation(self):
        for name in ("core/action_reservation.py", "core/command_admission.py",
                     "core/owner_enrollment_registry.py",
                     "scripts/qa_stack011_instrumentation_evidence.py",
                     "tests/test_qa_stack011_instrumentation_evidence.py",
                     "tests/test_qa_stack035_scoped_dispatch.py"):
            self.assertTrue((ROOT / name).is_file(), name)
        gate = (ROOT / "tests/test_qa005_workflow_gate.py").read_text()
        self.assertIn("MemoryVaultManifestBoundaryTest", gate)
        self.assertIn("MemoryVaultKeySpecContractTest", gate)
        self.assertIn("AgentPlanPreviewActivityTest", gate)


if __name__ == "__main__":
    unittest.main()
