"""Static regression gates for CI-003 reproducibility workflow concurrency.

These checks protect evidence collection; they do not claim a build ran.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ci003-reproducibility.yml"


class CI003WorkflowGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_new_commit_does_not_cancel_active_independent_builders(self):
        self.assertIn(
            "group: ci003-${{ github.event.pull_request.number || github.ref }}",
            self.workflow,
        )
        self.assertIn("cancel-in-progress: false", self.workflow)
        self.assertNotIn("cancel-in-progress: true", self.workflow)

    def test_independent_builder_matrix_does_not_fail_fast(self):
        self.assertIn("fail-fast: false", self.workflow)
        self.assertIn("builder: [runner-a, runner-b]", self.workflow)

    def test_each_run_checks_out_the_exact_event_commit(self):
        self.assertIn(
            "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
            self.workflow,
        )


if __name__ == "__main__":
    unittest.main()
