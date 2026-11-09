"""Offline tests for PaperClip content-free, symlink-resistant event logging."""
import importlib.util
import io
import fcntl
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "agents" / "paperclip" / "agent.py"
SPEC = importlib.util.spec_from_file_location("paperclip_secure_log_under_test", MODULE)
AGENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AGENT)
EVENT = "Processing prompt locally; content redacted"


class PaperclipSecureLoggingTests(unittest.TestCase):
    def test_private_log_created_without_secret_content(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            with patch.object(AGENT, "HOME", home):
                self.assertTrue(AGENT.log(EVENT))
                self.assertTrue(AGENT.log(EVENT))
            log = home / "logs" / "paperclip.log"
            self.assertEqual(log.read_text().count(EVENT), 2)
            self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE((home / "logs").stat().st_mode), 0o700)

    def test_existing_readable_directories_are_tightened(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            logs = home / "logs"
            logs.mkdir(parents=True)
            home.chmod(0o755)
            logs.chmod(0o755)
            with patch.object(AGENT, "HOME", home):
                self.assertTrue(AGENT.log(EVENT))
            self.assertEqual(stat.S_IMODE(home.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(logs.stat().st_mode), 0o700)

    def test_group_writable_home_refuses_without_log_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            home.mkdir()
            home.chmod(0o770)
            with patch.object(AGENT, "HOME", home):
                self.assertFalse(AGENT.log(EVENT))
            self.assertFalse((home / "logs").exists())
            self.assertEqual(stat.S_IMODE(home.stat().st_mode), 0o770)

    def test_world_writable_logs_refuses_without_log_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            logs = home / "logs"
            logs.mkdir(parents=True)
            logs.chmod(0o777)
            with patch.object(AGENT, "HOME", home):
                self.assertFalse(AGENT.log(EVENT))
            self.assertFalse((logs / "paperclip.log").exists())
            self.assertEqual(stat.S_IMODE(logs.stat().st_mode), 0o777)

    def test_log_cap_preserves_existing_records_and_refuses_overflow(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            with patch.object(AGENT, "HOME", home):
                self.assertTrue(AGENT.log(EVENT))
                log_path = home / "logs" / "paperclip.log"
                original = log_path.read_bytes()
                with patch.object(AGENT, "MAX_LOG_BYTES", len(original)):
                    self.assertFalse(AGENT.log(EVENT))
                self.assertEqual(log_path.read_bytes(), original)

    def test_too_small_cap_creates_no_event_record(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            with patch.object(AGENT, "HOME", home), patch.object(AGENT, "MAX_LOG_BYTES", 1):
                self.assertFalse(AGENT.log(EVENT))
            self.assertEqual((home / "logs" / "paperclip.log").read_bytes(), b"")

    def test_existing_oversized_log_is_never_truncated(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            logs = home / "logs"
            logs.mkdir(parents=True)
            path = logs / "paperclip.log"
            original = b"legacy-log" * 50
            path.write_bytes(original)
            with patch.object(AGENT, "HOME", home), patch.object(AGENT, "MAX_LOG_BYTES", 32):
                self.assertFalse(AGENT.log(EVENT))
            self.assertEqual(path.read_bytes(), original)

    def test_contended_log_lock_fails_closed_without_append(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            with patch.object(AGENT, "HOME", home):
                self.assertTrue(AGENT.log(EVENT))
                path = home / "logs" / "paperclip.log"
                original = path.read_bytes()
                with path.open("rb") as reader:
                    fcntl.flock(reader.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.assertFalse(AGENT.log(EVENT))
                    self.assertEqual(path.read_bytes(), original)
                    fcntl.flock(reader.fileno(), fcntl.LOCK_UN)
                self.assertTrue(AGENT.log(EVENT))
                self.assertGreater(path.stat().st_size, len(original))

    def test_broken_stdout_pipe_does_not_interrupt_file_logging(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            with patch.object(AGENT, "HOME", home), patch("builtins.print", side_effect=BrokenPipeError):
                self.assertTrue(AGENT.log(EVENT))
            self.assertIn(EVENT, (home / "logs" / "paperclip.log").read_text())

    def test_closed_stdout_does_not_interrupt_file_logging(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            with patch.object(AGENT, "HOME", home), patch("builtins.print", side_effect=ValueError("closed")):
                self.assertTrue(AGENT.log(EVENT))
            self.assertIn(EVENT, (home / "logs" / "paperclip.log").read_text())

    def test_close_errors_do_not_turn_successful_telemetry_into_exception(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            real_close = os.close

            def close_then_fail(fd):
                real_close(fd)
                raise OSError("synthetic close error after close")

            with patch.object(AGENT, "HOME", home), patch.object(AGENT.os, "close", side_effect=close_then_fail):
                self.assertTrue(AGENT.log(EVENT))
            self.assertIn(EVENT, (home / "logs" / "paperclip.log").read_text())

    def test_close_errors_do_not_mask_unsafe_target_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            target = Path(temp) / "target"
            target.mkdir()
            home.symlink_to(target, target_is_directory=True)
            real_close = os.close

            def close_then_fail(fd):
                real_close(fd)
                raise OSError("synthetic close error after close")

            with patch.object(AGENT, "HOME", home), patch.object(AGENT.os, "close", side_effect=close_then_fail):
                self.assertFalse(AGENT.log(EVENT))
            self.assertEqual(list(target.iterdir()), [])

    def test_unapproved_event_is_not_printed_or_persisted(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            out = io.StringIO()
            with patch.object(AGENT, "HOME", home), redirect_stdout(out):
                self.assertFalse(AGENT.log("secret user prompt"))
                self.assertFalse(AGENT.log(None))
            self.assertEqual(out.getvalue(), "")
            self.assertFalse(home.exists())

    def test_symlinked_home_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            external = root / "external"
            external.mkdir()
            (root / "mrnothing").symlink_to(external, target_is_directory=True)
            with patch.object(AGENT, "HOME", root / "mrnothing"):
                self.assertFalse(AGENT.log(EVENT))
            self.assertEqual(list(external.iterdir()), [])

    def test_symlinked_logs_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "mrnothing"
            home.mkdir()
            external = root / "external"
            external.mkdir()
            (home / "logs").symlink_to(external, target_is_directory=True)
            with patch.object(AGENT, "HOME", home):
                self.assertFalse(AGENT.log(EVENT))
            self.assertEqual(list(external.iterdir()), [])

    def test_symlinked_log_file_cannot_modify_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "mrnothing"
            (home / "logs").mkdir(parents=True)
            target = root / "private.txt"
            target.write_text("untouched")
            (home / "logs" / "paperclip.log").symlink_to(target)
            with patch.object(AGENT, "HOME", home):
                self.assertFalse(AGENT.log(EVENT))
            self.assertEqual(target.read_text(), "untouched")

    def test_hardlinked_log_file_cannot_modify_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "mrnothing"
            (home / "logs").mkdir(parents=True)
            target = root / "private.txt"
            target.write_text("untouched")
            os.link(target, home / "logs" / "paperclip.log")
            with patch.object(AGENT, "HOME", home):
                self.assertFalse(AGENT.log(EVENT))
            self.assertEqual(target.read_text(), "untouched")

    def test_fifo_log_fails_without_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            (home / "logs").mkdir(parents=True)
            os.mkfifo(home / "logs" / "paperclip.log")
            with patch.object(AGENT, "HOME", home):
                self.assertFalse(AGENT.log(EVENT))

    def test_existing_regular_log_is_tightened_to_owner_only(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "mrnothing"
            (home / "logs").mkdir(parents=True)
            path = home / "logs" / "paperclip.log"
            path.write_text("existing\n")
            path.chmod(0o644)
            with patch.object(AGENT, "HOME", home):
                self.assertTrue(AGENT.log(EVENT))
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertTrue(path.read_text().startswith("existing\n"))


if __name__ == "__main__":
    unittest.main()
