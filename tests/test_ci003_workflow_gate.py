"""Static regression gates for reproducible, resilient Android CI setup."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CI003_WORKFLOW = ROOT / ".github/workflows/ci003-reproducibility.yml"
PHASE1_WORKFLOW = ROOT / ".github/workflows/phase1-checks.yml"
DOWNLOADER = ROOT / "scripts/download_gradle_distribution.sh"
EXPECTED_GRADLE_SHA256 = "d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab"


class CI003WorkflowGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = CI003_WORKFLOW.read_text(encoding="utf-8")
        cls.phase1_workflow = PHASE1_WORKFLOW.read_text(encoding="utf-8")
        cls.downloader = DOWNLOADER.read_text(encoding="utf-8")

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

    def test_phase1_and_ci003_share_the_pinned_gradle_downloader(self):
        invocation = "bash ../scripts/download_gradle_distribution.sh 8.9"
        self.assertIn(invocation, self.workflow)
        self.assertIn(invocation, self.phase1_workflow)
        self.assertNotIn("curl -fsSL --retry 3", self.workflow + self.phase1_workflow)

    def test_both_android_jobs_pin_the_same_temurin_build(self):
        expected = "java-version: '17.0.21+9'"
        self.assertIn(expected, self.workflow)
        self.assertIn(expected, self.phase1_workflow)
        self.assertNotIn("17.0.13+11", self.workflow)

    def test_downloader_uses_only_allowlisted_https_sources_and_checksum(self):
        for host in (
            "services.gradle.org",
            "downloads.gradle.org",
            "downloads.gradle-dn.com",
        ):
            self.assertIn(host, self.downloader)
        self.assertIn(EXPECTED_GRADLE_SHA256, self.downloader)
        self.assertIn("--proto '=https'", self.downloader)
        self.assertIn("--proto-redir '=https'", self.downloader)
        self.assertIn("--tlsv1.2", self.downloader)
        self.assertIn("--retry 5", self.downloader)
        self.assertIn("--retry-connrefused", self.downloader)
        self.assertIn('gradle-${version}-bin.zip', self.downloader)
        self.assertIn('for url in "${urls[@]}"', self.downloader)
        self.assertNotIn("${dollar}", self.downloader)
        self.assertIn("sha256sum --check --status", self.downloader)
        self.assertLess(
            self.downloader.index("sha256sum --check --status"),
            self.downloader.index("mv -f --"),
        )
        self.assertNotRegex(self.downloader, r"(?i)--insecure|--location-trusted")

    def test_downloader_rejects_unpinned_versions_without_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "gradle.zip"
            result = subprocess.run(
                ["bash", str(DOWNLOADER), "9.0", str(destination)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 64)
        self.assertFalse(destination.exists())

    def test_downloader_fails_over_only_to_official_hosts(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            bin_path = temporary_path / "bin"
            bin_path.mkdir()
            call_log = temporary_path / "curl-calls.txt"
            fake_curl = bin_path / "curl"
            fake_curl.write_text(
                "#!/usr/bin/env bash\n"
                "for arg in \"$@\"; do last=\"$arg\"; done\n"
                "printf '%s\\n' \"$last\" >> \"$CURL_CALL_LOG\"\n"
                "exit 22\n",
                encoding="utf-8",
            )
            fake_curl.chmod(0o755)
            destination = temporary_path / "gradle.zip"
            environment = os.environ.copy()
            environment["PATH"] = str(bin_path) + os.pathsep + environment["PATH"]
            environment["CURL_CALL_LOG"] = str(call_log)
            result = subprocess.run(
                ["bash", str(DOWNLOADER), "8.9", str(destination)],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            calls = call_log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(result.returncode, 69)
        self.assertEqual(
            calls,
            [
                "https://services.gradle.org/distributions/gradle-8.9-bin.zip",
                "https://downloads.gradle.org/distributions/gradle-8.9-bin.zip",
                "https://downloads.gradle-dn.com/distributions/gradle-8.9-bin.zip",
            ],
        )
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
