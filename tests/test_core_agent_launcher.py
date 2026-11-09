import hashlib
import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core import main as core


class CoreAgentLauncherSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "agents"
        self.root.mkdir()
        self.safe = self.root / "hermes"
        self.safe.mkdir()
        (self.safe / "agent.py").write_text("print('safe')", encoding="utf-8")
        self.patch_root = patch.object(core, "AGENTS_DIR", self.root)
        self.patch_root.start()

    def tearDown(self):
        self.patch_root.stop()
        self.temp.cleanup()

    def test_resolver_accepts_only_direct_regular_agent_file(self):
        self.assertEqual(core._resolve_agent_path("hermes"), (self.safe / "agent.py").resolve())

    def test_resolver_rejects_traversal_absolute_and_invalid_names(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "agent.py").write_text("raise SystemExit", encoding="utf-8")
        for name in ("../outside", "../../tmp/outside", "/tmp/outside", ".", "..", "Hermes", "bad/name", "", None, 7):
            with self.subTest(name=name):
                self.assertIsNone(core._resolve_agent_path(name))

    def test_resolver_rejects_symlinked_agent_directory(self):
        outside = Path(self.temp.name) / "outside-dir"
        outside.mkdir()
        (outside / "agent.py").write_text("raise SystemExit", encoding="utf-8")
        (self.root / "escape").symlink_to(outside, target_is_directory=True)
        self.assertIsNone(core._resolve_agent_path("escape"))

    def test_resolver_rejects_symlinked_agent_file(self):
        outside = Path(self.temp.name) / "outside.py"
        outside.write_text("raise SystemExit", encoding="utf-8")
        (self.safe / "agent.py").unlink()
        (self.safe / "agent.py").symlink_to(outside)
        self.assertIsNone(core._resolve_agent_path("hermes"))

    def test_list_agents_excludes_symlinks_and_invalid_directories(self):
        outside = Path(self.temp.name) / "outside-dir"
        outside.mkdir()
        (outside / "agent.py").write_text("pass", encoding="utf-8")
        (self.root / "escape").symlink_to(outside, target_is_directory=True)
        (self.root / "missing").mkdir()
        self.assertEqual(core.list_agents(), ["hermes"])

    def test_run_agent_uses_resolved_path_argv_and_no_shell(self):
        process = Mock()
        with patch.object(core, "log"), patch.object(core.subprocess, "Popen", return_value=process) as popen:
            result = core.run_agent("hermes", '--mode "safe test"')
        self.assertIs(result, process)
        args, kwargs = popen.call_args
        self.assertEqual(args[0], [core.sys.executable, str((self.safe / "agent.py").resolve()), "--mode", "safe test"])
        self.assertEqual(kwargs["cwd"], str((self.safe / "agent.py").resolve().parent))
        self.assertIs(kwargs["shell"], False)

    def test_run_agent_rejects_path_traversal_before_process_creation(self):
        with patch.object(core, "log"), patch.object(core.subprocess, "Popen") as popen:
            self.assertIsNone(core.run_agent("../outside"))
        popen.assert_not_called()

    def test_run_agent_rejects_malformed_or_oversized_arguments(self):
        bad = ("'", "x\nid", "x" * (core.MAX_AGENT_ARGUMENT_CHARS + 1))
        for args in bad:
            with patch.object(core, "log"), patch.object(core.subprocess, "Popen") as popen:
                self.assertIsNone(core.run_agent("hermes", args))
            popen.assert_not_called()

    def test_configured_agent_list_fails_closed_on_any_invalid_entry(self):
        self.assertEqual(core._configured_agent_names(["hermes"]), ["hermes"])
        self.assertEqual(core._configured_agent_names(["hermes", "../outside"]), [])
        self.assertEqual(core._configured_agent_names(["hermes", "hermes"]), [])
        self.assertEqual(core._configured_agent_names("hermes"), [])
        self.assertEqual(core._configured_agent_names(["hermes"] * (core.MAX_AGENT_STARTS + 1)), [])

    def test_start_confirmation_is_bound_to_exact_agent_list(self):
        names = ["hermes"]
        material = "\x00".join(("mrnothing-agent-start-v1", *names))
        expected = "START AGENTS " + hashlib.sha256(material.encode()).hexdigest()[:16].upper()
        with patch("builtins.input", return_value=expected):
            self.assertTrue(core._confirm_agent_start(names))
        with patch("builtins.input", return_value="START AGENTS 0000000000000000"):
            self.assertFalse(core._confirm_agent_start(names))
        with patch("builtins.input", side_effect=EOFError):
            self.assertFalse(core._confirm_agent_start(names))

    def test_startup_does_not_start_when_auto_boot_disabled(self):
        with patch.object(core, "_confirm_agent_start") as confirm, patch.object(core, "run_agent") as run:
            self.assertEqual(core.start_configured_agents({"auto_boot": False, "agents_enabled": ["hermes"]}), [])
        confirm.assert_not_called()
        run.assert_not_called()

    def test_startup_requires_exact_confirmation_before_any_agent_starts(self):
        with patch.object(core, "_confirm_agent_start", return_value=False) as confirm, patch.object(core, "run_agent") as run, patch.object(core, "log"):
            self.assertEqual(core.start_configured_agents({"auto_boot": True, "agents_enabled": ["hermes"]}), [])
        confirm.assert_called_once_with(["hermes"])
        run.assert_not_called()

    def test_startup_starts_only_validated_agents_after_confirmation(self):
        with patch.object(core, "_confirm_agent_start", return_value=True) as confirm, patch.object(core, "run_agent", return_value=Mock()) as run:
            self.assertEqual(core.start_configured_agents({"auto_boot": True, "agents_enabled": ["hermes"]}), ["hermes"])
        confirm.assert_called_once_with(["hermes"])
        run.assert_called_once_with("hermes")

    def test_startup_does_not_prompt_for_invalid_or_unavailable_agent_list(self):
        with patch.object(core, "_confirm_agent_start") as confirm, patch.object(core, "run_agent") as run:
            self.assertEqual(core.start_configured_agents({"auto_boot": True, "agents_enabled": ["hermes", "../outside"]}), [])
        confirm.assert_not_called()
        run.assert_not_called()

    def test_confirmation_and_startup_api_do_not_accept_injected_callbacks(self):
        self.assertEqual(list(inspect.signature(core._confirm_agent_start).parameters), ["names"])
        self.assertEqual(list(inspect.signature(core.start_configured_agents).parameters), ["config"])


if __name__ == "__main__":
    unittest.main()
