"""AGENT-006O: bounded in-place RAM history cleanup (offline only)."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "paperclip_alias_cleanup_under_test", ROOT / "agents" / "paperclip" / "agent.py"
)
AGENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AGENT)


class PaperclipAliasCleanupTests(unittest.TestCase):
    def test_forget_clears_history_list_and_entry_aliases(self):
        session = AGENT.load_memory()
        session["session_opt_in"] = True
        self.assertTrue(AGENT.remember(session, "user", "synthetic secret"))
        history = session["conversations"]
        entry = history[0]
        facts = session["facts"]
        facts.append({"content": "synthetic private fact"})
        fact_entry = facts[0]

        AGENT.clear_memory(session)

        self.assertIs(session["conversations"], history)
        self.assertIs(session["facts"], facts)
        self.assertEqual(history, [])
        self.assertEqual(facts, [])
        self.assertEqual(entry, {})
        self.assertEqual(fact_entry, {})
        self.assertIs(session["session_opt_in"], False)
        self.assertFalse(AGENT.remember(session, "user", "after revocation"))

    def test_bounded_eviction_clears_mutable_evicted_entry_alias(self):
        session = AGENT.load_memory()
        session["session_opt_in"] = True
        self.assertTrue(AGENT.remember(session, "user", "old private message"))
        evicted = session["conversations"][0]
        for i in range(AGENT.MAX_SESSION_MEMORY_ENTRIES):
            self.assertTrue(AGENT.remember(session, "user", f"message-{i}"))
        self.assertEqual(len(session["conversations"]), AGENT.MAX_SESSION_MEMORY_ENTRIES)
        self.assertEqual(evicted, {})
        self.assertEqual(session["conversations"][0]["content"], "message-0")
        AGENT.clear_memory(session)

    def test_invalid_memory_container_is_reset_without_disk_effect(self):
        session = {"conversations": "malformed", "facts": None, "session_opt_in": True}
        AGENT.clear_memory(session)
        self.assertEqual(session["conversations"], [])
        self.assertEqual(session["facts"], [])
        self.assertIs(session["session_opt_in"], False)
        with self.assertRaises(TypeError):
            AGENT.clear_memory([])


if __name__ == "__main__":
    unittest.main()
