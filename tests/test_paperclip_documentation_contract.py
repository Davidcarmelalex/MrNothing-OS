"""Guard current PaperClip memory threat-model claims against source behavior."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "paperclip_docs_contract_under_test", ROOT / "agents" / "paperclip" / "agent.py"
)
AGENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AGENT)


class PaperclipDocumentationContractTests(unittest.TestCase):
    def test_active_threat_register_describes_memory_without_plaintext_persistence(self):
        model = (ROOT / "docs" / "THREAT-MODEL.md").read_text(encoding="utf-8")
        risk = next(line for line in model.splitlines() if line.startswith("| TM-15 "))
        data = next(line for line in model.splitlines() if line.startswith("| Local model artifacts and PaperClip memory |"))
        self.assertIn("requires explicit per-session opt-in", risk)
        self.assertIn("never automatically loads/deletes legacy", risk)
        self.assertIn("No encrypted persistent memory provider", risk)
        self.assertIn("memory defaults off", data)
        self.assertIn("disables plaintext disk saves", data)
        self.assertIn("neither loaded nor deleted automatically", data)
        self.assertNotIn("conversation memory remains local plaintext JSON", risk + data)

    def test_documented_fail_closed_behavior_matches_memory_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "memory.json"
            original = b'{"conversations":[{"content":"synthetic secret"}]}'
            legacy.write_bytes(original)
            with patch.object(AGENT, "MEMORY_FILE", legacy):
                session = AGENT.load_memory()
                self.assertIs(session["session_opt_in"], False)
                self.assertEqual(session["conversations"], [])
                self.assertFalse(AGENT.remember(session, "user", "not opted in"))
                session["session_opt_in"] = True
                for i in range(AGENT.MAX_SESSION_MEMORY_ENTRIES + 3):
                    self.assertTrue(AGENT.remember(session, "user", f"synthetic-{i}"))
                self.assertEqual(len(session["conversations"]), AGENT.MAX_SESSION_MEMORY_ENTRIES)
                with self.assertRaises(RuntimeError):
                    AGENT.save_memory(session)
                AGENT.clear_memory(session)
                self.assertFalse(session["session_opt_in"])
                self.assertEqual(session["conversations"], [])
                self.assertEqual(legacy.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
