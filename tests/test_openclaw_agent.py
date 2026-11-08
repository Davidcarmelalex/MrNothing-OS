import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from agents.openclaw import agent


class OpenClawSafetyTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop(agent.ALLOWED_TARGETS_ENV, None)

    def tearDown(self):
        self.env.stop()

    def _allow(self, target="192.168.56.10"):
        os.environ[agent.ALLOWED_TARGETS_ENV] = target

    def test_target_parser_accepts_only_private_ipv4_literals(self):
        self.assertEqual(agent._canonical_private_ipv4("192.168.56.10"), "192.168.56.10")
        self.assertEqual(agent._canonical_private_ipv4("10.0.0.7"), "10.0.0.7")
        self.assertIsNone(agent._canonical_private_ipv4("example.com"))
        self.assertIsNone(agent._canonical_private_ipv4("https://192.168.56.10"))
        self.assertIsNone(agent._canonical_private_ipv4("192.168.56.10;id"))
        self.assertIsNone(agent._canonical_private_ipv4("8.8.8.8"))
        self.assertIsNone(agent._canonical_private_ipv4("-n"))

    def test_allowlist_is_exact_and_malformed_entry_denies_all(self):
        self._allow("192.168.56.10,10.0.0.7")
        self.assertEqual(agent._load_allowed_targets(), frozenset({"192.168.56.10", "10.0.0.7"}))
        self._allow("192.168.56.10,8.8.8.8")
        self.assertEqual(agent._load_allowed_targets(), frozenset())
        self._allow("192.168.56.10, 10.0.0.7")
        self.assertEqual(agent._load_allowed_targets(), frozenset())


    def test_missing_allowlist_denies_before_confirmation_or_network(self):
        with patch.object(agent, "confirm_scan") as confirm, patch.object(agent, "run") as run, patch.object(agent.socket, "socket") as sock:
            result = agent.scan_network("192.168.56.10")
        self.assertEqual(result["reason"], "TARGET_NOT_ALLOWLISTED")
        confirm.assert_not_called()
        run.assert_not_called()
        sock.assert_not_called()

    def test_invalid_or_public_target_is_denied_even_with_confirmation(self):
        self._allow("192.168.56.10")
        with patch.object(agent, "confirm_scan") as confirm, patch.object(agent, "run") as run, patch.object(agent.socket, "socket") as sock:
            for target in ("192.168.56.10;id", "https://192.168.56.10", "8.8.8.8", "example.com"):
                result = agent.scan_network(target)
                self.assertEqual(result["reason"], "INVALID_OR_NON_PRIVATE_IPV4")
        confirm.assert_not_called()
        run.assert_not_called()
        sock.assert_not_called()

    def test_allowlisted_target_requires_internal_interactive_confirmation(self):
        self._allow()
        with patch.object(agent, "confirm_scan", return_value=False) as confirm, patch.object(agent, "run") as run, patch.object(agent.socket, "socket") as sock:
            result = agent.scan_network("192.168.56.10")
        self.assertEqual(result["reason"], "CONFIRMATION_DENIED")
        confirm.assert_called_once_with("192.168.56.10")
        run.assert_not_called()
        sock.assert_not_called()

    def test_declined_confirmation_has_no_network_or_filesystem_effect(self):
        self._allow()
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(agent, "REPORTS_DIR", Path(temp_dir) / "reports"),
                patch.object(agent, "log") as log,
                patch.object(agent, "confirm_scan", return_value=False),
                patch.object(agent, "run") as run,
                patch.object(agent.socket, "socket") as sock,
            ):
                result = agent.scan_network("192.168.56.10")
            self.assertEqual(result["reason"], "CONFIRMATION_DENIED")
            self.assertFalse((Path(temp_dir) / "reports").exists())
        log.assert_not_called()
        run.assert_not_called()
        sock.assert_not_called()

    def test_confirmation_requires_exact_boolean_true(self):
        self._allow()
        for value in (1, "yes", None, False):
            with patch.object(agent, "confirm_scan", return_value=value), patch.object(agent, "run") as run, patch.object(agent.socket, "socket") as sock:
                result = agent.scan_network("192.168.56.10")
            self.assertEqual(result["reason"], "CONFIRMATION_DENIED")
            run.assert_not_called()
            sock.assert_not_called()

    def test_confirmation_exception_fails_closed(self):
        self._allow()
        def broken(_target):
            raise RuntimeError("confirmation unavailable")
        with patch.object(agent, "confirm_scan", side_effect=broken), patch.object(agent, "run") as run, patch.object(agent.socket, "socket") as sock:
            result = agent.scan_network("192.168.56.10")
        self.assertEqual(result["reason"], "CONFIRMATION_DENIED")
        run.assert_not_called()
        sock.assert_not_called()

    def test_confirmed_scan_uses_fixed_argv_and_no_dns_lookup(self):
        self._allow()
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(agent, "REPORTS_DIR", Path(temp_dir)),
                patch.object(agent, "log"),
                patch.object(agent, "confirm_scan", return_value=True),
                patch.object(agent.shutil, "which", side_effect=lambda name: f"/usr/bin/{name}"),
                patch.object(agent, "run", return_value="ok") as run,
                patch.object(agent.socket, "socket") as sock,
            ):
                result = agent.scan_network("192.168.56.10")
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["authorization"]["allowlist"], "exact-private-ipv4")
        self.assertEqual([entry.args[0][0] for entry in run.call_args_list], ["ping", "nmap", "curl"])
        for entry in run.call_args_list:
            self.assertIsInstance(entry.args[0], list)
            self.assertNotIn("192.168.56.10;id", entry.args[0])
        self.assertNotIn("dig", [entry.args[0][0] for entry in run.call_args_list])
        sock.assert_not_called()

    def test_nmap_fallback_uses_only_literal_ip_after_authorization(self):
        self._allow()
        fake_socket = Mock()
        fake_socket.connect_ex.return_value = 1
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(agent, "REPORTS_DIR", Path(temp_dir)),
                patch.object(agent, "log"),
                patch.object(agent, "confirm_scan", return_value=True),
                patch.object(agent.shutil, "which", side_effect=lambda name: None if name == "nmap" else f"/usr/bin/{name}"),
                patch.object(agent, "run", return_value="ok") as run,
                patch.object(agent.socket, "socket", return_value=fake_socket) as sock,
            ):
                result = agent.scan_network("192.168.56.10")
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(sock.call_count, len(agent._COMMON_PORTS))
        self.assertTrue(all(call_args.args == (agent.socket.AF_INET, agent.socket.SOCK_STREAM) for call_args in sock.call_args_list))
        self.assertTrue(all(call_args.args[0] == ["ping", "-c", "3", "-W", "2", "192.168.56.10"] or call_args.args[0][0] == "curl" for call_args in run.call_args_list))
        self.assertEqual(fake_socket.close.call_count, len(agent._COMMON_PORTS))
    def test_run_rejects_strings_shells_and_unapproved_executables(self):
        with patch.object(agent.subprocess, "run") as run:
            self.assertTrue(agent.run("ping -c 1 127.0.0.1").startswith("[ERROR]"))
            self.assertTrue(agent.run(["sh", "-c", "id"]).startswith("[ERROR]"))
            self.assertTrue(agent.run(["python", "-c", "id"]).startswith("[ERROR]"))
        run.assert_not_called()

    def test_run_executes_argv_with_shell_false_and_timeout(self):
        completed = Mock(returncode=0, stdout="pong", stderr="")
        with patch.object(agent.subprocess, "run", return_value=completed) as run:
            self.assertEqual(agent.run(["ping", "-c", "1", "127.0.0.1"], timeout=5), "pong")
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["ping", "-c", "1", "127.0.0.1"])
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["timeout"], 5)

    def test_run_rejects_invalid_timeout_and_oversized_argv(self):
        with patch.object(agent.subprocess, "run") as run:
            self.assertEqual(agent.run(["ping", "127.0.0.1"], timeout=0), "[ERROR] invalid timeout")
            self.assertEqual(agent.run(["ping", "127.0.0.1"], timeout=61), "[ERROR] invalid timeout")
            self.assertEqual(agent.run(["ping", "x" * (agent.MAX_ARG_CHARS + 1)]), "[ERROR] argv too large")
        run.assert_not_called()

    def test_check_tools_does_not_spawn_which_shell_commands(self):
        with patch.object(agent.shutil, "which", return_value="/usr/bin/tool") as which, patch.object(agent.subprocess, "run") as run:
            tools = agent.check_tools()
        self.assertTrue(all(tools.values()))
        self.assertEqual(which.call_count, len(agent._AVAILABLE_TOOLS))
        run.assert_not_called()

    def test_source_contains_no_shell_true_or_string_command_execution(self):
        source = Path(agent.__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, re.compile(r"shell\s*=\s*True"))
        self.assertIn("shell=False", source)
        self.assertNotIn("dig +short", source)
        self.assertNotIn("confirm=None", source)
        self.assertNotIn("callable(confirm)", source)
        self.assertIn("confirm_scan(canonical)", source)
        self.assertNotIn("confirm(canonical)", source)
        self.assertEqual(agent.scan_network.__code__.co_argcount, 1)

    def test_wifi_info_uses_fixed_local_argv(self):
        with patch.object(agent, "run", return_value="{}") as run:
            self.assertEqual(agent.wifi_info(), "{}")
        run.assert_called_once_with(["termux-wifi-connectioninfo"], timeout=10)

    def test_typed_confirmation_is_exact_and_target_bound(self):
        with patch("builtins.input", return_value="SCAN 192.168.56.10"):
            self.assertTrue(agent.confirm_scan("192.168.56.10"))
        with patch("builtins.input", return_value="SCAN 192.168.56.11"):
            self.assertFalse(agent.confirm_scan("192.168.56.10"))
        with patch("builtins.input", side_effect=EOFError):
            self.assertFalse(agent.confirm_scan("192.168.56.10"))


if __name__ == "__main__":
    unittest.main()
