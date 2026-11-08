"""AGENT-006N: session teardown and model-name privacy regressions (offline)."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "agents" / "paperclip" / "agent.py"
SPEC = importlib.util.spec_from_file_location("paperclip_cleanup_under_test", MODULE_PATH)
AGENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AGENT)


class PaperclipSessionCleanupTests(unittest.TestCase):
    def _exercise_exit(self, ending, raises=None):
        memory = {"conversations": [], "facts": ["synthetic private fact"], "session_opt_in": False}
        seen = []

        def respond(prompt, mem):
            self.assertEqual(prompt, "synthetic private prompt")
            self.assertTrue(mem["session_opt_in"])
            self.assertEqual(mem["conversations"][0]["content"], prompt)
            seen.append(True)
            return "synthetic response"

        with tempfile.TemporaryDirectory() as temporary:
            legacy = Path(temporary) / "memory.json"
            legacy.write_text('{"legacy":"preserve synthetic secret"}', encoding="utf-8")
            original = legacy.read_bytes()
            with (
                patch.object(AGENT, "load_memory", return_value=memory),
                patch.object(AGENT, "MEMORY_FILE", legacy),
                patch.object(AGENT, "check_model", return_value=None),
                patch.object(AGENT, "think", side_effect=respond),
                patch.object(AGENT, "log"),
                patch("builtins.print"),
                patch("builtins.input", side_effect=["memory on", "synthetic private prompt", ending]),
            ):
                if raises is not None:
                    with self.assertRaises(raises):
                        AGENT.main()
                else:
                    AGENT.main()
            self.assertEqual(legacy.read_bytes(), original)

        self.assertEqual(seen, [True], "test must exercise opted-in memory before teardown")
        self.assertEqual(memory["conversations"], [])
        self.assertEqual(memory["facts"], [])
        self.assertIs(memory["session_opt_in"], False)

    def test_explicit_exit_clears_opted_in_session(self):
        self._exercise_exit("exit")

    def test_eof_clears_opted_in_session(self):
        self._exercise_exit(EOFError())

    def test_interrupt_clears_opted_in_session(self):
        self._exercise_exit(KeyboardInterrupt())

    def test_unexpected_exception_clears_opted_in_session_and_propagates(self):
        self._exercise_exit(RuntimeError("synthetic failure"), RuntimeError)

    def test_model_filename_is_not_written_to_event_log(self):
        memory = AGENT.load_memory()
        sensitive_name = "synthetic-private-owner-notes.gguf"
        with (
            patch.object(AGENT, "check_model", return_value=Path(sensitive_name)),
            patch.object(AGENT, "infer_llama_cpp", return_value="safe synthetic reply"),
            patch.object(AGENT, "log") as log,
        ):
            self.assertEqual(AGENT.think("synthetic prompt", memory), "safe synthetic reply")
        self.assertTrue(log.called)
        self.assertNotIn(sensitive_name, repr(log.call_args_list))

    def test_legacy_persistent_save_remains_disabled(self):
        with self.assertRaises(RuntimeError):
            AGENT.save_memory({"session_opt_in": True, "conversations": [], "facts": []})


    def test_model_filename_is_hidden_in_startup_banner(self):
        memory = AGENT.load_memory()
        sensitive_name = "synthetic-private-owner-notes.gguf"
        with tempfile.TemporaryDirectory() as temporary:
            missing_legacy = Path(temporary) / "memory.json"
            with (
                patch.object(AGENT, "load_memory", return_value=memory),
                patch.object(AGENT, "MEMORY_FILE", missing_legacy),
                patch.object(AGENT, "check_model", return_value=Path(sensitive_name)),
                patch.object(AGENT, "log"),
                patch("builtins.input", return_value="exit"),
                patch("builtins.print") as output,
            ):
                AGENT.main()
        self.assertNotIn(sensitive_name, repr(output.call_args_list))
        self.assertIs(memory["session_opt_in"], False)


if __name__ == "__main__":
    unittest.main()
