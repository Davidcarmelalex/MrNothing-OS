"""QA-STACK-025: bounded, explicit manual CI verification for PR #54."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/qa-stack024-ci003-qa005-head-20261112"
REPOSITORY = "Davidcarmelalex/MrNothing-OS"
CLAUSE = (
    "(github.event_name == 'workflow_dispatch' && "
    f"github.ref == 'refs/heads/{BRANCH}' && "
    f"github.repository == '{REPOSITORY}')"
)
EXACT_HEAD = "${{ github.event.pull_request.head.sha || github.sha }}"


class ScopedDispatchTests(unittest.TestCase):
    def _workflow(self, filename):
        text = (ROOT / '.github/workflows' / filename).read_text()
        self.assertIn('  workflow_dispatch:', text)
        self.assertIn('permissions:\n  contents: read', text)
        self.assertNotIn('pull_request_target:', text)
        return text

    def _assert_guarded(self, job):
        gate = next(line.strip() for line in job.splitlines() if line.startswith('    if: '))
        self.assertEqual(gate.count(CLAUSE), 1)
        self.assertIn('github.event_name == \'workflow_dispatch\'', gate)
        self.assertIn('github.repository ==', gate)
        self.assertIn('github.ref ==', gate)
        self.assertIn('persist-credentials: false', job)
        self.assertIn('ref: ' + EXACT_HEAD, job)
        self.assertIn('EXPECTED_SHA: ' + EXACT_HEAD, job)
        self.assertIn('run: test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"', job)

    def test_qa005_manual_dispatch_is_scoped(self):
        text = self._workflow('qa005-emulator.yml')
        self.assertIn('cancel-in-progress: false', text)
        self._assert_guarded(text.split('  emulator-smoke:', 1)[1])

    def test_ci003_builder_and_verifier_both_scoped(self):
        text = self._workflow('ci003-reproducibility.yml')
        self.assertIn('cancel-in-progress: false', text)
        build = text.split('  build:', 1)[1].split('  verify-independent-runners:', 1)[0]
        verify = text.split('  verify-independent-runners:', 1)[1]
        self._assert_guarded(build)
        self._assert_guarded(verify)

    def test_no_unbounded_manual_dispatch_or_privileged_permissions(self):
        for name in ('qa005-emulator.yml', 'ci003-reproducibility.yml'):
            text = self._workflow(name)
            guarded = [line for line in text.splitlines() if line.startswith('    if: ')]
            self.assertEqual(len(guarded), 1 if name.startswith('qa005') else 2)
            for line in guarded:
                self.assertIn(CLAUSE, line)
                self.assertNotIn('|| true', line)
            self.assertNotIn('contents: write', text)
            self.assertNotIn('id-token: write', text)


if __name__ == '__main__':
    unittest.main()
