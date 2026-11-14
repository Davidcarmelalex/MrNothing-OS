"""QA-STACK-007: exact-head CI gating for one audited integration PR.

Static checks do not substitute for hosted independent runners or emulator evidence.
"""
from pathlib import Path
import unittest

import re

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github/workflows/ci003-reproducibility.yml"
QA = ROOT / ".github/workflows/qa005-emulator.yml"
TARGET = "feat/phase1-agentic-phone"
CANDIDATE = "feat/qa-stack007-exact-head-ci-20261111"
CROSS_STACK = "feat/qa-stack008-ux-memoryvault-integration-20261113"
REPO = "Davidcarmelalex/MrNothing-OS"
PIN = "ref: ${{ github.event.pull_request.head.sha || github.sha }}"


class ScopedWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ci = CI.read_text(encoding="utf-8")
        cls.qa = QA.read_text(encoding="utf-8")

    def test_both_workflows_preserve_main_gate_and_read_only_token(self):
        expected_branches = (
            (self.ci, "[main, feat/phase1-agentic-phone, feat/qa-stack008-ux-memoryvault-integration-20261113, feat/ci003-same-purl-drift-20261114]"),
            (self.qa, "[main, feat/phase1-agentic-phone]"),
        )
        for workflow, branches in expected_branches:
            self.assertIn(f"  pull_request:\n    branches: {branches}\n", workflow)
            self.assertIn("permissions:\n  contents: read", workflow)

    def test_reproducibility_is_opt_in_for_single_same_repo_pr(self):
        self.assertIn("  push:\n    branches: [feat/phase1-agentic-phone]", self.ci)
        for name in ("build", "verify-independent-runners"):
            condition = re.search(r"(?m)^    if: (.+)$", self.ci[self.ci.index(f"  {name}:"):]).group(1)
            self.assertIn(f"github.head_ref == '{CANDIDATE}'", condition)
            self.assertIn(f"github.head_ref == '{CROSS_STACK}'", condition)
            self.assertIn(f"github.base_ref == '{TARGET}'", condition)
            self.assertIn(f"github.event.pull_request.head.repo.full_name == '{REPO}'", condition)
            self.assertIn("github.event_name == 'pull_request'", condition)
            self.assertIn("github.ref == 'refs/heads/feat/phase1-agentic-phone'", condition)
        self.assertIn("builder: [runner-a, runner-b]", self.ci)
        self.assertIn("  verify-independent-runners:\n    if:", self.ci)
        self.assertIn("    needs: build", self.ci)
        self.assertEqual(2, self.ci.count(PIN))

    def test_emulator_runs_only_for_main_or_exact_same_repo_candidate(self):
        self.assertNotIn("  push:", self.qa)
        condition = re.search(r"(?m)^    if: (.+)$", self.qa[self.qa.index("  emulator-smoke:"):]).group(1)
        self.assertIn("github.base_ref == 'main'", condition)
        self.assertIn(f"github.base_ref == '{TARGET}'", condition)
        self.assertIn(f"github.head_ref == '{CANDIDATE}'", condition)
        self.assertIn(f"github.head_ref == '{CROSS_STACK}'", condition)
        self.assertIn(f"github.event.pull_request.head.repo.full_name == '{REPO}'", condition)
        self.assertEqual(1, self.qa.count(PIN))
        self.assertIn("      - '.github/workflows/qa005-emulator.yml'", self.qa)

    def test_expensive_jobs_preserve_resource_and_cleanup_guards(self):
        self.assertIn("cancel-in-progress: false", self.ci)
        self.assertIn("cancel-in-progress: false", self.qa)
        self.assertIn("    timeout-minutes: 35", self.ci)
        self.assertIn("    timeout-minutes: 35", self.qa)
        self.assertIn("trap cleanup EXIT INT TERM", self.qa)
        self.assertIn("ANDROID_SERIAL: emulator-5554", self.qa)
        self.assertNotIn("adb root", self.qa)


if __name__ == "__main__":
    unittest.main()
