import copy
import hashlib
import unittest
from unittest.mock import Mock, patch
import subprocess

from agents.hermes import agent


class StopScheduler(Exception):
    pass


class LegacyHermesApprovalTests(unittest.TestCase):
    def test_shell_task_is_blocked_without_interactive_approval(self):
        with patch.object(agent, "log"), patch.object(agent.subprocess, "run") as run:
            self.assertFalse(agent.execute_task({
                "type": "shell", "command": "echo hello"
            }))
        run.assert_not_called()

    def test_shell_task_is_blocked_when_owner_declines(self):
        confirm = Mock(return_value=False)
        with patch.object(agent, "log"), patch.object(agent.subprocess, "run") as run:
            self.assertFalse(agent.execute_task(
                {"type": "shell", "command": "echo hello"},
                confirm_shell=confirm,
            ))
        confirm.assert_called_once_with("echo hello")
        run.assert_not_called()

    def test_shell_task_requires_literal_true_from_confirmation(self):
        confirm = Mock(return_value=1)
        with patch.object(agent, "log"), patch.object(agent.subprocess, "run") as run:
            self.assertFalse(agent.execute_task(
                {"type": "shell", "command": "echo hello"},
                confirm_shell=confirm,
            ))
        run.assert_not_called()

    def test_approved_command_uses_argv_without_shell_and_has_timeout(self):
        fake_result = Mock(returncode=0, stdout="ok", stderr="")
        confirm = Mock(return_value=True)
        with (
            patch.object(agent, "log"),
            patch.object(agent, "notify"),
            patch.object(agent.subprocess, "run", return_value=fake_result) as run,
        ):
            self.assertTrue(agent.execute_task(
                {"type": "shell", "command": "echo hello"},
                confirm_shell=confirm,
            ))
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["echo", "hello"])
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["timeout"], agent.SHELL_COMMAND_TIMEOUT_SECONDS)
        confirm.assert_called_once_with("echo hello")

    def test_shell_interpreter_is_rejected_before_confirmation(self):
        confirm = Mock(return_value=True)
        with patch.object(agent, "log"), patch.object(agent.subprocess, "run") as run:
            self.assertFalse(agent.execute_task(
                {"type": "shell", "command": "/system/bin/sh -c id"},
                confirm_shell=confirm,
            ))
        confirm.assert_not_called()
        run.assert_not_called()

    def test_busybox_shell_is_rejected(self):
        self.assertIsNone(agent._parse_shell_argv("busybox sh -c id"))

    def test_control_characters_and_oversized_commands_are_rejected(self):
        self.assertIsNone(agent._parse_shell_argv("echo first\nsecond"))
        self.assertIsNone(agent._parse_shell_argv("x" * (agent.MAX_SHELL_COMMAND_CHARS + 1)))

    def test_unmatched_quotes_are_rejected(self):
        self.assertIsNone(agent._parse_shell_argv("echo 'unfinished"))

    def test_timeout_fails_closed(self):
        confirm = Mock(return_value=True)
        with (
            patch.object(agent, "log"),
            patch.object(
                agent.subprocess, "run",
                side_effect=subprocess.TimeoutExpired(cmd=["echo"], timeout=30),
            ),
        ):
            self.assertFalse(agent.execute_task(
                {"type": "shell", "command": "echo hello"},
                confirm_shell=confirm,
            ))

    def test_notify_task_remains_available_without_shell_approval(self):
        with patch.object(agent, "log"), patch.object(agent, "notify") as notify:
            self.assertTrue(agent.execute_task({
                "type": "notify", "title": "Test", "body": "Ready"
            }))
        notify.assert_called_once_with("Test", "Ready")

    def test_confirmation_challenge_is_bound_to_exact_command(self):
        command = "echo hello"
        expected = "RUN " + hashlib.sha256(command.encode("utf-8")).hexdigest()[:10]
        with patch("builtins.input", return_value=expected):
            self.assertTrue(agent._confirm_shell_command(command))
        with patch("builtins.input", return_value="RUN 0000000000"):
            self.assertFalse(agent._confirm_shell_command(command))

    def test_scheduler_defers_due_shell_task_without_executing_it(self):
        tasks = {
            "scheduled": [{
                "name": "unsafe scheduled task",
                "type": "shell",
                "command": "echo must-not-run",
                "run_at": 1,
            }],
            "completed": [],
        }
        saved = []
        with (
            patch.object(agent, "log"),
            patch.object(agent, "load_tasks", return_value=tasks),
            patch.object(agent, "save_tasks", side_effect=lambda value: saved.append(copy.deepcopy(value))),
            patch.object(agent, "notify") as notify,
            patch.object(agent, "execute_task") as execute,
            patch.object(agent.time, "time", return_value=10.0),
            patch.object(agent.time, "sleep", side_effect=StopScheduler),
        ):
            with self.assertRaises(StopScheduler):
                agent.schedule_loop()
        execute.assert_not_called()
        notify.assert_called_once()
        self.assertTrue(saved[-1]["scheduled"][0]["approval_required"])
        self.assertEqual(saved[-1]["scheduled"][0]["approval_required_at"], 10.0)

    def test_scheduler_does_not_repeat_approval_notification(self):
        tasks = {
            "scheduled": [{
                "name": "unsafe scheduled task",
                "type": "shell",
                "command": "echo must-not-run",
                "run_at": 1,
                "approval_required": True,
            }],
            "completed": [],
        }
        saved = []
        with (
            patch.object(agent, "log"),
            patch.object(agent, "load_tasks", return_value=tasks),
            patch.object(agent, "save_tasks", side_effect=lambda value: saved.append(copy.deepcopy(value))),
            patch.object(agent, "notify") as notify,
            patch.object(agent, "execute_task") as execute,
            patch.object(agent.time, "time", return_value=10.0),
            patch.object(agent.time, "sleep", side_effect=StopScheduler),
        ):
            with self.assertRaises(StopScheduler):
                agent.schedule_loop()
        execute.assert_not_called()
        notify.assert_not_called()
        self.assertEqual(saved, [])

    def test_invalid_task_record_is_rejected(self):
        with patch.object(agent, "log"):
            self.assertFalse(agent.execute_task([]))


if __name__ == "__main__":
    unittest.main()
