"""QA-STACK-002: offline synthetic Git ancestry and sibling overlap regressions."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("pr_stack_ancestry_gate",
                                              SCRIPTS / "pr_stack_ancestry_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
ROOT = "feat/phase1-agentic-phone"


def pr(number, head, base, sha):
    return {"number": number, "state": "open", "draft": True,
            "head": {"ref": head, "sha": sha}, "base": {"ref": base}}


class AncestryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "ci@example.invalid")
        self.git("config", "user.name", "Synthetic CI")
        self.root = self.commit("root.txt", "root")
        self.ref(ROOT, self.root)
        self.git("checkout", "-q", "-b", "feat/a")
        self.a = self.commit("shared.txt", "a")
        self.ref("feat/a", self.a)
        self.git("checkout", "-q", "-b", "feat/b")
        self.b = self.commit("unique.txt", "b")
        self.ref("feat/b", self.b)
        self.git("checkout", "-q", "-b", "feat/c", self.root)
        self.c = self.commit("shared.txt", "c")
        self.ref("feat/c", self.c)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args],
                                       stderr=subprocess.STDOUT).decode().strip()

    def commit(self, name, content):
        (self.repo / name).write_text(content)
        self.git("add", name)
        self.git("commit", "-qm", name)
        return self.git("rev-parse", "HEAD")

    def ref(self, branch, sha):
        self.git("update-ref", "refs/remotes/origin/" + branch, sha)

    def chain(self):
        return [pr(2, "feat/b", "feat/a", self.b),
                pr(1, "feat/a", ROOT, self.a)]

    def test_chain_ancestry_and_incremental_files(self):
        result = gate.audit(self.repo, self.chain(), self.root)
        self.assertEqual([x["number"] for x in result["parent_first"]], [1, 2])
        self.assertEqual(result["parent_first"][1]["incremental_files"],
                         ["unique.txt"])
        self.assertEqual(result["status"], "ancestry_verified_not_merge_approved")

    def test_sibling_overlap_reported_not_approved(self):
        result = gate.audit(self.repo, [pr(1, "feat/a", ROOT, self.a),
                                        pr(3, "feat/c", ROOT, self.c)], self.root)
        self.assertEqual(result["sibling_overlap_pairs"], 1)
        self.assertEqual(result["overlaps"][0]["paths"], ["shared.txt"])
        self.assertEqual(result["status"], "review_required")

    def test_stale_head_blocked(self):
        with self.assertRaisesRegex(gate.AncestryError, "stale head"):
            gate.audit(self.repo, [pr(1, "feat/a", ROOT, self.b)], self.root)

    def test_parent_not_ancestor_blocked(self):
        with self.assertRaisesRegex(gate.AncestryError, "not ancestor"):
            gate.audit(self.repo, [pr(3, "feat/c", "feat/a", self.c),
                                   pr(1, "feat/a", ROOT, self.a)], self.root)

    def test_missing_remote_ref_blocked(self):
        with self.assertRaises(gate.AncestryError):
            gate.audit(self.repo, [pr(4, "feat/missing", ROOT, self.a)], self.root)

    def test_stale_root_blocked(self):
        with self.assertRaisesRegex(gate.AncestryError, "root remote ref"):
            gate.audit(self.repo, self.chain(), self.a)

    def test_invalid_snapshot_sha_blocked(self):
        with self.assertRaisesRegex(ValueError, "SHA"):
            gate.audit(self.repo, [pr(1, "feat/a", ROOT, "invalid")], self.root)

    def test_read_only_refs(self):
        before = self.git("show-ref")
        gate.audit(self.repo, self.chain(), self.root)
        self.assertEqual(self.git("show-ref"), before)

    def test_cli_success_and_block(self):
        path = self.repo / "pulls.json"
        path.write_text(json.dumps(self.chain()))
        cmd = [sys.executable, str(SCRIPTS / "pr_stack_ancestry_gate.py"),
               "--input", str(path), "--repo", str(self.repo),
               "--root-sha", self.root]
        good = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)["pr_count"], 2)
        bad = subprocess.run(cmd[:-1] + [self.a], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(json.loads(bad.stderr)["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
