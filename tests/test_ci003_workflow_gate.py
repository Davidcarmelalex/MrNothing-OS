"""Static regression gates for reproducible, resilient Android CI setup."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CI003_WORKFLOW = ROOT / ".github/workflows/ci003-reproducibility.yml"
PHASE1_WORKFLOW = ROOT / ".github/workflows/phase1-checks.yml"
SETTINGS = ROOT / "android/settings.gradle.kts"
DOWNLOADER = ROOT / "scripts/download_gradle_distribution.sh"
EXPECTED_GRADLE_SHA256 = "d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab"


class CI003WorkflowGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = CI003_WORKFLOW.read_text(encoding="utf-8")
        cls.phase1_workflow = PHASE1_WORKFLOW.read_text(encoding="utf-8")
        cls.settings = SETTINGS.read_text(encoding="utf-8")
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
        self.assertIn("$HOME/.gradle/distributions/gradle-8.9-bin.zip", self.workflow)
        self.assertIn("$HOME/.gradle/distributions/gradle-8.9-bin.zip", self.phase1_workflow)
        self.assertNotIn("curl -fsSL --retry 3", self.workflow + self.phase1_workflow)

    def test_both_android_jobs_pin_the_same_temurin_build_and_gradle_cache(self):
        for workflow in (self.workflow, self.phase1_workflow):
            self.assertIn("java-version: '17.0.21+9'", workflow)
            self.assertIn("cache: gradle", workflow)
            self.assertIn("cache-path: |", workflow)
            self.assertIn("~/.gradle/caches", workflow)
            self.assertIn("~/.gradle/distributions", workflow)
            self.assertIn("cache-read-only: ${{ github.event_name == 'pull_request' }}", workflow)
        self.assertNotIn("17.0.13+11", self.workflow)

    def test_plugin_and_maven_repositories_use_official_fallback_order(self):
        repo1 = 'maven { url = uri("https://repo1.maven.org/maven2/") }'
        self.assertEqual(self.settings.count(repo1), 2)
        plugin_portal = self.settings.index("gradlePluginPortal()")
        first_central = self.settings.index("mavenCentral()")
        second_repo1 = self.settings.rindex(repo1)
        second_central = self.settings.rindex("mavenCentral()")
        self.assertLess(plugin_portal, first_central)
        self.assertLess(self.settings.index(repo1), first_central)
        self.assertLess(second_repo1, second_central)

    def test_downloader_uses_allowlisted_https_sources_and_checksum(self):
        for host in ("services.gradle.org", "downloads.gradle.org"):
            self.assertIn(host, self.downloader)
        self.assertNotIn("downloads.gradle-dn.com", self.downloader)
        self.assertIn(EXPECTED_GRADLE_SHA256, self.downloader)
        self.assertIn("--proto '=https'", self.downloader)
        self.assertIn("--proto-redir '=https'", self.downloader)
        self.assertIn("--tlsv1.2", self.downloader)
        self.assertIn("--retry 5", self.downloader)
        self.assertIn("--retry-connrefused", self.downloader)
        self.assertIn("sha256sum --check --status", self.downloader)
        self.assertLess(
            self.downloader.index("sha256sum --check --status"),
            self.downloader.index("mv -f --"),
        )
        self.assertIn('gradle-${version}-bin.zip', self.downloader)
        self.assertIn('for url in "${urls[@]}"', self.downloader)
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
            ],
        )
        self.assertFalse(destination.exists())

    def test_verified_cached_gradle_archive_skips_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            bin_path = temporary_path / "bin"
            bin_path.mkdir()
            destination = temporary_path / "gradle.zip"
            destination.write_bytes(b"cached-archive-fixture")
            fake_hash = bin_path / "sha256sum"
            fake_hash.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            fake_hash.chmod(0o755)
            curl_log = temporary_path / "curl-calls.txt"
            fake_curl = bin_path / "curl"
            fake_curl.write_text(
                "#!/usr/bin/env bash\nprintf called >> \"$CURL_CALL_LOG\"\nexit 22\n",
                encoding="utf-8",
            )
            fake_curl.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = str(bin_path) + os.pathsep + environment["PATH"]
            environment["CURL_CALL_LOG"] = str(curl_log)
            result = subprocess.run(
                ["bash", str(DOWNLOADER), "8.9", str(destination)],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertFalse(curl_log.exists())
        self.assertIn("Cached Gradle 8.9 distribution checksum verified", result.stderr)

    def test_tampered_cached_gradle_archive_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            bin_path = temporary_path / "bin"
            bin_path.mkdir()
            destination = temporary_path / "gradle.zip"
            destination.write_bytes(b"tampered-cache-fixture")
            fake_hash = bin_path / "sha256sum"
            fake_hash.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
            fake_hash.chmod(0o755)
            curl_log = temporary_path / "curl-calls.txt"
            fake_curl = bin_path / "curl"
            fake_curl.write_text(
                "#!/usr/bin/env bash\nprintf called >> \"$CURL_CALL_LOG\"\nexit 22\n",
                encoding="utf-8",
            )
            fake_curl.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = str(bin_path) + os.pathsep + environment["PATH"]
            environment["CURL_CALL_LOG"] = str(curl_log)
            result = subprocess.run(
                ["bash", str(DOWNLOADER), "8.9", str(destination)],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
        self.assertEqual(result.returncode, 65)
        self.assertFalse(curl_log.exists())
        self.assertIn("SHA-256 mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()
