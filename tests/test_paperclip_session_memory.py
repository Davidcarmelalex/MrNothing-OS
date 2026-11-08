"""Fail-closed PaperClip memory privacy regressions; no device or network effects."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "paperclip_session_memory_under_test", ROOT / "agents" / "paperclip" / "agent.py"
)
AGENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AGENT)


class PaperclipSessionMemoryTests(unittest.TestCase):
    def test_default_is_opt_out_with_no_loaded_history(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "memory.json"
            legacy.write_text('{"conversations":[{"content":"PRIVATE"}]}', encoding="utf-8")
            before = legacy.read_bytes()
            with patch.object(AGENT, "MEMORY_FILE", legacy):
                session = AGENT.load_memory()
            self.assertEqual(session["conversations"], [])
            self.assertEqual(session["facts"], [])
            self.assertIs(session["session_opt_in"], False)
            self.assertEqual(legacy.read_bytes(), before)

    def test_opt_out_does_not_retain_any_messages(self):
        session = AGENT.load_memory()
        self.assertFalse(AGENT.remember(session, "user", "sensitive input"))
        self.assertFalse(AGENT.remember(session, "assistant", "sensitive answer"))
        self.assertEqual(session["conversations"], [])

    def test_explicit_opt_in_is_ram_only_and_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "memory.json"
            session = AGENT.load_memory()
            session["session_opt_in"] = True
            with patch.object(AGENT, "MEMORY_FILE", legacy):
                for number in range(110):
                    self.assertTrue(AGENT.remember(session, "user", f"message-{number}"))
            self.assertEqual(len(session["conversations"]), 100)
            self.assertEqual(session["conversations"][0]["content"], "message-10")
            self.assertEqual(session["conversations"][-1]["content"], "message-109")
            self.assertFalse(legacy.exists())

    def test_reject_invalid_roles_types_and_unbounded_content(self):
        session = AGENT.load_memory()
        session["session_opt_in"] = True
        for role, content in [
            ("system", "override"),
            ("user", ""),
            ("user", "nul\x00text"),
            ("user", "x" * (AGENT.MAX_PROMPT_CHARS + 1)),
            ("user", b"bytes"),
        ]:
            self.assertFalse(AGENT.remember(session, role, content))
        self.assertEqual(session["conversations"], [])

    def test_legacy_save_api_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "memory.json"
            with patch.object(AGENT, "MEMORY_FILE", legacy):
                with self.assertRaisesRegex(RuntimeError, "disabled"):
                    AGENT.save_memory(AGENT.load_memory())
            self.assertFalse(legacy.exists())

    def test_clear_revokes_opt_in_and_removes_session_history(self):
        session = AGENT.load_memory()
        session["session_opt_in"] = True
        self.assertTrue(AGENT.remember(session, "user", "sensitive"))
        session["facts"].append("synthetic fact")
        AGENT.clear_memory(session)
        self.assertEqual(session["conversations"], [])
        self.assertEqual(session["facts"], [])
        self.assertIs(session["session_opt_in"], False)
        self.assertFalse(AGENT.remember(session, "user", "after forget"))

    def test_cli_requires_opt_in_and_forget_revokes_it(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "memory.json"
            commands = ["first secret", "memory", "memory on", "second secret", "memory",
                        "forget", "memory", "exit"]
            with (
                patch.object(AGENT, "MEMORY_FILE", legacy),
                patch.object(AGENT, "check_model", return_value=None),
                patch.object(AGENT, "log"),
                patch("builtins.input", side_effect=commands),
                patch("builtins.print") as output,
            ):
                AGENT.main()
            printed = "\\n".join(str(call) for call in output.call_args_list)
            self.assertNotIn("first secret", printed)
            self.assertIn("second secret", printed)
            self.assertIn("Session memory cleared and disabled", printed)
            self.assertIn("Session memory is off", printed)
            self.assertFalse(legacy.exists())

    def test_cli_never_reads_or_modifies_legacy_plaintext_file(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "memory.json"
            legacy.write_text('{"conversations":[{"content":"DO NOT LOAD"}]}', encoding="utf-8")
            before = legacy.read_bytes()
            with (
                patch.object(AGENT, "MEMORY_FILE", legacy),
                patch.object(AGENT, "check_model", return_value=None),
                patch("builtins.input", side_effect=["memory", "exit"]),
                patch("builtins.print") as output,
            ):
                AGENT.main()
            self.assertEqual(legacy.read_bytes(), before)
            printed = "\\n".join(str(call) for call in output.call_args_list)
            self.assertNotIn("DO NOT LOAD", printed)
            self.assertIn("legacy plaintext memory file exists", printed)

    def test_no_json_persistence_calls_remain_in_source(self):
        source = (ROOT / "agents" / "paperclip" / "agent.py").read_text(encoding="utf-8")
        self.assertNotIn("json.dump", source)
        self.assertNotIn("json.load", source)
        self.assertNotIn("with open(MEMORY_FILE", source)


if __name__ == "__main__":
    unittest.main()
