"""QA-STACK-035: exact-head manual CI dispatch only on a named scoped branch.

These static checks do not substitute for hosted emulator/reproducibility evidence.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/qa-stack035-exact-head-emulator-repro-20261112"
REPO = "Davidcarmelalex/MrNothing-OS"
CLAUSE = (
    "(github.event_name == 'workflow_dispatch' && "
    f"github.ref == 'refs/heads/{BRANCH}' && "
    f"github.repository == '{REPO}')"
)
EXACT_HEAD = "${{ github.event.pull_request.head.sha || github.sha }}"


class ScopedExactHeadDispatchTests(unittest.TestCase):
    def _read(self, filename):
        source = (ROOT / ".github/workflows" / filename).read_text()
        self.assertIn("  workflow_dispatch:", source)
        self.assertIn("permissions:\n  contents: read", source)
        self.assertNotIn("pull_request_target", source)
        self.assertNotIn("contents: write", source)
        return source

    def _assert_job(self, job):
        guard = next(line for line in job.splitlines() if line.startswith("    if: "))
        self.assertEqual(guard.count(CLAUSE), 1)
        self.assertIn("github.event_name == 'workflow_dispatch'", guard)
        self.assertIn("github.repository == 'Davidcarmelalex/MrNothing-OS'", guard)
        self.assertIn("persist-credentials: false", job)
        self.assertIn("ref: " + EXACT_HEAD, job)
        self.assertIn("EXPECTED_SHA: " + EXACT_HEAD, job)
        self.assertIn('run: test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"', job)

    def test_emulator_scoped_dispatch(self):
        source = self._read("qa005-emulator.yml")
        self.assertNotIn("  push:", source)
        self.assertIn("cancel-in-progress: false", source)
        self._assert_job(source.split("  emulator-smoke:", 1)[1])

    def test_both_reproducibility_jobs_scoped(self):
        source = self._read("ci003-reproducibility.yml")
        self.assertIn("cancel-in-progress: false", source)
        build = source.split("  build:", 1)[1].split("  verify-independent-runners:", 1)[0]
        verifier = source.split("  verify-independent-runners:", 1)[1]
        self._assert_job(build)
        self._assert_job(verifier)

    def test_manual_gate_requires_all_three_conditions(self):
        for name in ("qa005-emulator.yml", "ci003-reproducibility.yml"):
            source = self._read(name)
            for guard in (x for x in source.splitlines() if x.startswith("    if: ")):
                self.assertEqual(guard.count(CLAUSE), 1)
                for missing in ("workflow_dispatch", "refs/heads/" + BRANCH, REPO):
                    with self.subTest(workflow=name, missing=missing):
                        mutated = guard.replace(CLAUSE, CLAUSE.replace(missing, "invalid"))
                        self.assertNotIn(CLAUSE, mutated)
                        self.assertNotEqual(guard, mutated)


if __name__ == "__main__":
    unittest.main()
