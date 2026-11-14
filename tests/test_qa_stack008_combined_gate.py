"""QA-STACK-008: combined security/UX candidate must retain both deny-only boundaries.

Source and workflow checks only; emulator, Android JVM and hardware require separate evidence.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/qa-stack008-ux-memoryvault-combined-20261111"


class CombinedCandidateGate(unittest.TestCase):
    def test_both_instrumentation_classes_present_once(self):
        gradle = (ROOT / "android/app/build.gradle.kts").read_text()
        self.assertEqual(1, gradle.count('"tech.mrnothing.os.MemoryVaultManifestBoundaryTest"'))
        self.assertEqual(1, gradle.count('"tech.mrnothing.os.AgentPlanPreviewActivityTest"'))
        start = gradle.index('testInstrumentationRunnerArguments["class"] = listOf(')
        end = gradle.index(').joinToString(",")', start)
        configured = re.findall(r'"tech\.mrnothing\.os\.\w+"', gradle[start:end])
        self.assertEqual(8, len(configured))
        self.assertEqual(8, len(set(configured)))

    def test_vault_disabled_and_preview_not_exported(self):
        manifest = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text()
        self.assertRegex(manifest, r'<service\s+android:name="\.MemoryVaultService"\s+android:exported="false"\s+android:enabled="false"\s*/>')
        self.assertRegex(manifest, r'<activity\s+android:name="\.AgentPlanPreviewActivity"\s+android:exported="false"\s*/>')

    def test_exact_head_ci_scope_for_single_combined_branch(self):
        for name in ("ci003-reproducibility.yml", "qa005-emulator.yml"):
            source = (ROOT / ".github/workflows" / name).read_text()
            self.assertIn(f"github.head_ref == '{BRANCH}'", source)
            self.assertIn("github.base_ref == 'feat/phase1-agentic-phone'", source)
            self.assertIn("github.event.pull_request.head.repo.full_name == 'Davidcarmelalex/MrNothing-OS'", source)
            self.assertIn("github.event.pull_request.head.sha || github.sha", source)
            self.assertIn("cancel-in-progress: false", source)

    def test_rehearsal_remains_non_authorizing(self):
        supervisor = (ROOT / "android/app/src/main/java/tech/mrnothing/os/AgentNoOpSupervisor.kt").read_text()
        self.assertIn("val authorized: Boolean get() = false", supervisor)
        self.assertIn("val deviceActionsExecuted: Boolean get() = false", supervisor)
        self.assertIn("BLOCKED_NO_VERIFIED_SESSION", supervisor)
        self.assertNotIn("Runtime.getRuntime()", supervisor)
        self.assertNotIn("startActivityForResult", supervisor)


if __name__ == "__main__":
    unittest.main()
