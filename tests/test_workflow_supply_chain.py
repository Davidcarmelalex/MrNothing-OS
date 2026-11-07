"""Guard GitHub Actions workflows against mutable action and runner references."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
EXPECTED_ACTIONS = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",  # v7.0.1
    "actions/setup-python": "6d4fd22b20465ccc0f7354476588e8df7c9ca0e0",  # v7.1.0
    "actions/setup-java": "77dd5b2ce225ea11469928ac317850245a74ae78",  # v6.2.0
    "actions/upload-artifact": "cf430e030ddbb5b0abf93d22962f4752f3646cd9",  # v7.0.2
    "actions/download-artifact": "9000827ccba6bdab643e8b6fd33ac0654aef8333",  # v8.0.2
}
USE_RE = re.compile(r"^\s*-\s*uses:\s*([^\s#]+)", re.MULTILINE)


class WorkflowSupplyChainTests(unittest.TestCase):
    def workflows(self):
        files = sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml"))
        self.assertGreaterEqual(len(files), 1)
        return files

    def test_all_actions_use_reviewed_full_commit_shas(self):
        for path in self.workflows():
            content = path.read_text(encoding="utf-8")
            refs = USE_RE.findall(content)
            self.assertTrue(refs, f"{path} has no action references")
            for ref in refs:
                self.assertIn("@", ref, f"{path}: malformed action ref {ref}")
                action, sha = ref.rsplit("@", 1)
                self.assertIn(action, EXPECTED_ACTIONS, f"{path}: unreviewed action {action}")
                self.assertRegex(sha, r"^[0-9a-f]{40}$", f"{path}: mutable/non-SHA ref {ref}")
                self.assertEqual(sha, EXPECTED_ACTIONS[action], f"{path}: unexpected commit for {action}")

    def test_checkout_never_persists_repository_credentials(self):
        for path in self.workflows():
            content = path.read_text(encoding="utf-8")
            checkouts = len(re.findall(r"^\s*-\s*uses:\s*actions/checkout@", content, re.MULTILINE))
            disabled = len(re.findall(r"^\s+persist-credentials:\s*false\s*$", content, re.MULTILINE))
            self.assertEqual(disabled, checkouts, f"{path}: every checkout must disable credential persistence")
            self.assertNotRegex(content, r"(?m)^\s+persist-credentials:\s*true\s*$")

    def test_workflows_use_read_only_contents_permission(self):
        for path in self.workflows():
            content = path.read_text(encoding="utf-8")
            self.assertRegex(content, r"(?m)^permissions:\n\s+contents:\s+read\s*$")
            self.assertNotRegex(content, r"(?m)^permissions:\s+write-all\s*$")

    def test_runner_image_label_is_explicit(self):
        for path in self.workflows():
            content = path.read_text(encoding="utf-8")
            labels = re.findall(r"(?m)^\s+runs-on:\s*(\S+)\s*$", content)
            self.assertTrue(labels, f"{path}: no runner labels found")
            self.assertEqual(set(labels), {"ubuntu-24.04"}, f"{path}: runner label must be explicit")
            self.assertNotIn("ubuntu-latest", labels)


if __name__ == "__main__":
    unittest.main()
