"""QA-STACK-008: cross-stack denial boundaries on the combined candidate.

Source assertions only: JVM, emulator and human review remain separate gates.
"""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android/app/src/main"
REPO = "Davidcarmelalex/MrNothing-OS"
CANDIDATE = "feat/qa-stack008-ux-memoryvault-integration-20261113"
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


class CrossStackBoundaryTests(unittest.TestCase):
    def test_preview_and_vault_manifest_remain_nonexported_and_vault_disabled(self):
        root = ET.parse(ANDROID / "AndroidManifest.xml").getroot()
        app = root.find("application")
        self.assertIsNotNone(app)
        activities = {x.attrib.get(ANDROID_NS + "name"): x for x in app.findall("activity")}
        services = {x.attrib.get(ANDROID_NS + "name"): x for x in app.findall("service")}
        preview = activities[".AgentPlanPreviewActivity"]
        vault = services[".MemoryVaultService"]
        self.assertEqual("false", preview.attrib.get(ANDROID_NS + "exported"))
        self.assertEqual("false", vault.attrib.get(ANDROID_NS + "exported"))
        self.assertEqual("false", vault.attrib.get(ANDROID_NS + "enabled"))
        permissions = {x.attrib.get(ANDROID_NS + "name") for x in root.findall("uses-permission")}
        self.assertEqual({"android.permission.USE_BIOMETRIC"}, permissions)

    def test_offline_preview_does_not_link_to_memoryvault_or_execution(self):
        src = ANDROID / "java/tech/mrnothing/os"
        preview = (src / "AgentPlanPreviewActivity.kt").read_text()
        supervisor = (src / "AgentNoOpSupervisor.kt").read_text()
        for text in (preview, supervisor):
            self.assertNotIn("MemoryVault", text)
            self.assertNotIn("CommandRouter(", text)
            self.assertNotIn("requestPermissions(", text)
            self.assertNotIn("Runtime.getRuntime(", text)
        self.assertIn("val authorized: Boolean get() = false", supervisor)
        self.assertIn("val deviceActionsExecuted: Boolean get() = false", supervisor)
        self.assertIn("rehearsal.cancel()", preview)
        self.assertIn("override fun onStop()", preview)

    def test_hosted_expensive_jobs_are_exact_candidate_and_same_repo_scoped(self):
        for filename, jobs in (
            ("ci003-reproducibility.yml", ("build", "verify-independent-runners")),
            ("qa005-emulator.yml", ("emulator-smoke",)),
        ):
            workflow = (ROOT / ".github/workflows" / filename).read_text()
            self.assertIn("permissions:\n  contents: read", workflow)
            self.assertIn("cancel-in-progress: false", workflow)
            for job in jobs:
                start = workflow.index(f"  {job}:")
                condition = re.search(r"(?m)^    if: (.+)$", workflow[start:])
                self.assertIsNotNone(condition)
                expression = condition.group(1)
                self.assertIn(f"github.head_ref == '{CANDIDATE}'", expression)
                self.assertIn("github.base_ref == 'feat/phase1-agentic-phone'", expression)
                self.assertIn(f"github.event.pull_request.head.repo.full_name == '{REPO}'", expression)


if __name__ == "__main__":
    unittest.main()
