"""QA-STACK-003 synthetic merge-tree conflict and no-ref-mutation regressions."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("pr_stack_merge_simulator",
                                              SCRIPTS / "pr_stack_merge_simulator.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
ROOT = "feat/phase1-agentic-phone"


def pr(number, branch, sha):
    return {"number": number, "state": "open", "draft": True,
            "head": {"ref": branch, "sha": sha}, "base": {"ref": ROOT}}


class MergeSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Synthetic")
        self.git("config", "user.email", "ci@example.invalid")
        self.commit("shared.txt", "original\n")
        self.base = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "-b", ROOT)
        self.root = self.commit("shared.txt", "root change\n")
        self.ref(ROOT, self.root)
        self.git("checkout", "-q", "-b", "feat/conflict", self.base)
        self.conflict = self.commit("shared.txt", "other change\n")
        self.ref("feat/conflict", self.conflict)
        self.git("checkout", "-q", "-b", "feat/clean", self.base)
        self.clean = self.commit("other.txt", "unrelated\n")
        self.ref("feat/clean", self.clean)
        self.git("checkout", "-q", "--detach", self.root)

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

    def test_clean_divergent_change_needs_review(self):
        report = gate.audit(self.repo, [pr(1, "feat/clean", self.clean)], self.root, [1])
        row = report["results"][0]
        self.assertEqual(row["merge_tree"], "clean_simulation")
        self.assertFalse(row["root_is_ancestor"])
        self.assertEqual(row["overlap_with_root"], [])
        self.assertEqual(report["status"], "review_required_not_merge_approved")

    def test_conflicting_change_blocks(self):
        report = gate.audit(self.repo, [pr(2, "feat/conflict", self.conflict)], self.root, [2])
        self.assertEqual(report["status"], "blocked_conflicts")
        self.assertEqual(report["results"][0]["merge_tree"], "conflict")
        self.assertEqual(report["results"][0]["overlap_with_root"], ["shared.txt"])

    def test_stale_head_rejected(self):
        with self.assertRaisesRegex(gate.SimulationError, "stale head"):
            gate.audit(self.repo, [pr(1, "feat/clean", self.conflict)], self.root, [1])

    def test_stale_root_rejected(self):
        with self.assertRaisesRegex(gate.SimulationError, "root ref changed"):
            gate.audit(self.repo, [pr(1, "feat/clean", self.clean)], self.base, [1])

    def test_missing_or_non_draft_rejected(self):
        with self.assertRaisesRegex(gate.SimulationError, "missing or not open draft"):
            gate.audit(self.repo, [pr(1, "feat/clean", self.clean)], self.root, [3])
        row = pr(1, "feat/clean", self.clean)
        row["draft"] = False
        with self.assertRaisesRegex(gate.SimulationError, "missing or not open draft"):
            gate.audit(self.repo, [row], self.root, [1])

    def test_wrong_base_rejected(self):
        row = pr(1, "feat/clean", self.clean)
        row["base"]["ref"] = "main"
        with self.assertRaisesRegex(gate.SimulationError, "unexpected parent"):
            gate.audit(self.repo, [row], self.root, [1])

    def test_duplicate_selection_rejected(self):
        with self.assertRaisesRegex(gate.SimulationError, "invalid PR selection"):
            gate.audit(self.repo, [pr(1, "feat/clean", self.clean)], self.root, [1, 1])

    def test_no_refs_head_or_worktree_mutated(self):
        before_refs = self.git("show-ref")
        before_head = self.git("rev-parse", "HEAD")
        before_status = self.git("status", "--porcelain")
        gate.audit(self.repo, [pr(1, "feat/clean", self.clean),
                               pr(2, "feat/conflict", self.conflict)], self.root, [1, 2])
        self.assertEqual(before_refs, self.git("show-ref"))
        self.assertEqual(before_head, self.git("rev-parse", "HEAD"))
        self.assertEqual(before_status, self.git("status", "--porcelain"))

    def test_cli_exit_codes(self):
        snapshot = self.repo / "snapshot.json"
        snapshot.write_text(json.dumps([pr(1, "feat/clean", self.clean),
                                        pr(2, "feat/conflict", self.conflict)]))
        cmd = [sys.executable, str(SCRIPTS / "pr_stack_merge_simulator.py"),
               "--input", str(snapshot), "--repo", str(self.repo),
               "--root-sha", self.root]
        good = subprocess.run(cmd + ["--pr", "1"], capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)["selected_count"], 1)
        bad = subprocess.run(cmd + ["--pr", "2"], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1, bad.stderr)
        self.assertEqual(json.loads(bad.stdout)["status"], "blocked_conflicts")
        missing = subprocess.run(cmd + ["--pr", "3"], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(json.loads(missing.stderr)["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
