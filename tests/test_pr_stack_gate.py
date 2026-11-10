"""QA-STACK-001 deterministic offline graph regressions."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/pr_stack_gate.py"
spec = importlib.util.spec_from_file_location("pr_stack_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def pr(n, head, base, *, draft=True, state="open", sha="a" * 40):
    return {"number": n, "state": state, "draft": draft,
            "head": {"ref": head, "sha": sha}, "base": {"ref": base}}


class StackTests(unittest.TestCase):
    def test_parent_first(self):
        result = gate.audit([pr(3, "feat/c", "feat/b"),
                             pr(1, "feat/a", gate.ROOT),
                             pr(2, "feat/b", "feat/a")])
        self.assertEqual([x["number"] for x in result["parent_first"]], [1, 2, 3])
        self.assertEqual(result["max_depth"], 3)

    def test_umbrella_excluded(self):
        result = gate.audit([pr(1, gate.ROOT, "main"), pr(2, "feat/a", gate.ROOT)])
        self.assertEqual(result["pr_count"], 1)

    def test_main_target_excluded(self):
        self.assertEqual(gate.audit([pr(1, "feat/a", "main")])["pr_count"], 0)

    def test_draft_and_roots(self):
        result = gate.audit([pr(1, "feat/a", gate.ROOT),
                             pr(2, "feat/b", gate.ROOT, draft=False)])
        self.assertEqual((result["draft_count"], result["direct_root_count"]), (1, 2))

    def test_closed_ignored(self):
        self.assertEqual(gate.audit([pr(1, "feat/a", gate.ROOT, state="closed")])["pr_count"], 0)

    def test_missing_parent(self):
        with self.assertRaisesRegex(gate.AuditError, "unresolved"):
            gate.audit([pr(1, "feat/a", "feat/missing")])

    def test_cycle(self):
        with self.assertRaisesRegex(gate.AuditError, "cycle"):
            gate.audit([pr(1, "feat/a", "feat/b"), pr(2, "feat/b", "feat/a")])

    def test_duplicate_number(self):
        with self.assertRaisesRegex(gate.AuditError, "duplicate"):
            gate.audit([pr(1, "feat/a", gate.ROOT), pr(1, "feat/b", gate.ROOT)])

    def test_duplicate_head(self):
        with self.assertRaisesRegex(gate.AuditError, "duplicate"):
            gate.audit([pr(1, "feat/a", gate.ROOT), pr(2, "feat/a", gate.ROOT)])

    def test_bad_sha(self):
        with self.assertRaisesRegex(gate.AuditError, "SHA"):
            gate.audit([pr(1, "feat/a", gate.ROOT, sha="short")])

    def test_bad_ref(self):
        with self.assertRaisesRegex(gate.AuditError, "branch"):
            gate.audit([pr(1, "feat/../bad", gate.ROOT)])

    def test_bool_number(self):
        with self.assertRaisesRegex(gate.AuditError, "number"):
            gate.audit([pr(True, "feat/a", gate.ROOT)])

    def test_non_list(self):
        with self.assertRaises(gate.AuditError):
            gate.audit({"invalid": True})

    def test_input_unchanged(self):
        items = [pr(1, "feat/a", gate.ROOT)]
        before = json.dumps(items, sort_keys=True)
        gate.audit(items)
        self.assertEqual(before, json.dumps(items, sort_keys=True))

    def test_cli_success_and_block(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "prs.json"
            path.write_text(json.dumps([pr(1, "feat/a", gate.ROOT)]))
            ok = subprocess.run([sys.executable, str(SCRIPT), "--input", str(path)],
                                capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(json.loads(ok.stdout)["pr_count"], 1)
            path.write_text(json.dumps([pr(1, "feat/a", "feat/missing")]))
            bad = subprocess.run([sys.executable, str(SCRIPT), "--input", str(path)],
                                 capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(json.loads(bad.stderr)["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
