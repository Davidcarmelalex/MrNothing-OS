"""Offline tests for PaperClip content-free, symlink-resistant event logging."""
import importlib.util
import io
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
