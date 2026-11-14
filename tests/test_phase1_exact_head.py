"""Fail-closed regression for exact source commit in Phase 1 CI."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/phase1-checks.yml"
EXPRESSION = "${{ github.event.pull_request.head.sha || github.sha }}"


class Phase1ExactHeadTests(unittest.TestCase):
    def setUp(self):
        self.source = WORKFLOW.read_text(encoding="utf-8")

    def test_both_jobs_checkout_exact_head_and_verify_it(self):
        self.assertIn("  python-policy:", self.source)
        self.assertIn("  android:", self.source)
        jobs = [
            self.source.split("  python-policy:", 1)[1].split("  android:", 1)[0],
            self.source.split("  android:", 1)[1],
        ]
        for job in jobs:
            with self.subTest(job=job[:35]):
                self.assertEqual(job.count("uses: actions/checkout@"), 1)
                self.assertIn("persist-credentials: false", job)
                self.assertIn("ref: " + EXPRESSION, job)
                self.assertIn("EXPECTED_SHA: " + EXPRESSION, job)
                self.assertIn('run: test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"', job)

    def test_workflow_cannot_use_privileged_pull_request_target(self):
        self.assertIn("  pull_request:", self.source)
        self.assertNotIn("pull_request_target", self.source)
        self.assertIn("  contents: read", self.source)


if __name__ == "__main__":
    unittest.main()
