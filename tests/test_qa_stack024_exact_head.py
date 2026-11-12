"""QA-STACK-024: reject CI evidence not tied to the event source commit."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPRESSION = "${{ github.event.pull_request.head.sha || github.sha }}"
ASSERTION = 'run: test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"'


def exact_head_gate(job):
    """Require a single checkout and assertion before any SDK or artifact work."""
    checkout = job.find("- uses: actions/checkout@")
    gate = job.find("- name: Assert checked-out source is the exact event head")
    setup = job.find("- uses: actions/setup-")
    return (
        checkout >= 0 and gate > checkout and setup > gate
        and job.count("- uses: actions/checkout@") == 1
        and job.count("- name: Assert checked-out source is the exact event head") == 1
        and "persist-credentials: false" in job[checkout:gate]
        and "ref: " + EXPRESSION in job[checkout:gate]
        and "EXPECTED_SHA: " + EXPRESSION in job[gate:setup]
        and ASSERTION in job[gate:setup]
    )


class ExactHeadEmulatorAndReproTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qa = (ROOT / ".github/workflows/qa005-emulator.yml").read_text()
        cls.ci = (ROOT / ".github/workflows/ci003-reproducibility.yml").read_text()

    def test_emulator_checks_exact_event_head_before_sdk_and_device(self):
        job = self.qa.split("  emulator-smoke:", 1)[1]
        self.assertTrue(exact_head_gate(job))
        self.assertIn("cancel-in-progress: false", self.qa)
        self.assertNotIn("pull_request_target", self.qa)

    def test_both_repro_jobs_check_exact_event_head(self):
        build = self.ci.split("  build:", 1)[1].split("  verify-independent-runners:", 1)[0]
        verifier = self.ci.split("  verify-independent-runners:", 1)[1]
        for name, job in (("builder", build), ("verifier", verifier)):
            with self.subTest(job=name):
                self.assertTrue(exact_head_gate(job))
        self.assertNotIn("pull_request_target", self.ci)

    def test_mutated_or_missing_source_provenance_fails_gate(self):
        job = self.qa.split("  emulator-smoke:", 1)[1]
        self.assertTrue(exact_head_gate(job))
        for mutated in (
            job.replace("EXPECTED_SHA: " + EXPRESSION, "EXPECTED_SHA: ${{ github.sha }}"),
            job.replace(ASSERTION, "run: echo verified"),
            job.replace("ref: " + EXPRESSION, "ref: ${{ github.ref }}"),
            job.replace("persist-credentials: false", "persist-credentials: true"),
        ):
            with self.subTest(mutated=mutated != job):
                self.assertFalse(exact_head_gate(mutated))


if __name__ == "__main__":
    unittest.main()
