"""Offline regression coverage for legacy Termux voice privacy and consent."""
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mrnothing_voice_legacy", ROOT / "modules" / "voice-engine" / "voice.py")
voice = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(voice)


class VoiceConsentTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.log_patch = patch.object(voice, "log", side_effect=self.events.append)
        self.log_patch.start()
        self.addCleanup(self.log_patch.stop)

    def test_invalid_duration_rejected_before_tool_lookup(self):
        with patch.object(voice, "_tool") as tool:
            for duration in (0, 16, True, 1.5, "5", None):
                self.assertEqual(voice.listen(duration), "")
            tool.assert_not_called()

    def test_missing_stt_tool_does_not_prompt(self):
        with patch.object(voice, "_tool", return_value=None), patch("builtins.input") as prompt:
            self.assertEqual(voice.listen(), "")
            prompt.assert_not_called()

    def test_declined_capture_never_runs_subprocess(self):
        with patch.object(voice, "_tool", return_value="/safe/stt"), patch("builtins.input", return_value="yes"), patch.object(voice.subprocess, "run") as run:
            self.assertEqual(voice.listen(), "")
            run.assert_not_called()

    def test_eof_denies_capture(self):
        with patch.object(voice, "_tool", return_value="/safe/stt"), patch("builtins.input", side_effect=EOFError), patch.object(voice.subprocess, "run") as run:
            self.assertEqual(voice.listen(), "")
            run.assert_not_called()

    def test_approved_capture_uses_bounded_fixed_argv_and_redacted_log(self):
        secret = "private spoken words"
        with patch.object(voice, "_tool", return_value="/safe/stt"), patch("builtins.input", return_value="ALLOW MICROPHONE 5 SECONDS"), patch.object(voice.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout=secret)) as run:
            self.assertEqual(voice.listen(5), secret)
            args, kwargs = run.call_args
            self.assertEqual(args[0], ["/safe/stt", "-l", "en", "-t", "5"])
            self.assertEqual(kwargs["timeout"], 15)
            self.assertTrue(kwargs["check"])
            self.assertFalse(kwargs["shell"])
            self.assertNotIn(secret, str(self.events))

    def test_stt_exception_does_not_leak_command_or_transcript(self):
        with patch.object(voice, "_tool", return_value="/safe/stt"), patch("builtins.input", return_value="ALLOW MICROPHONE 1 SECONDS"), patch.object(voice.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "sensitive command")):
            self.assertEqual(voice.listen(1), "")
            self.assertNotIn("sensitive", str(self.events))

    def test_oversized_or_empty_transcript_rejected(self):
        with patch.object(voice, "_tool", return_value="/safe/stt"), patch("builtins.input", return_value="ALLOW MICROPHONE 2 SECONDS"), patch.object(voice.subprocess, "run") as run:
            for value in ("", "x" * 4097, "hello\x00world"):
                run.return_value = subprocess.CompletedProcess([], 0, stdout=value)
                self.assertEqual(voice.listen(2), "")

    def test_tts_rejects_invalid_inputs_and_engine(self):
        with patch.object(voice, "_tool") as tool:
            for value, engine in (("", "auto"), ("x" * 1001, "auto"), ("ok\x00", "auto"), ("ok", "unknown"), ("-dangerous", "termux")):
                self.assertFalse(voice.speak(value, engine))
            tool.assert_not_called()

    def test_tts_fixed_argv_and_no_speech_logging(self):
        secret = "confidential TTS phrase"
        with patch.object(voice, "_tool", return_value="/safe/tts"), patch.object(voice.subprocess, "run") as run:
            self.assertTrue(voice.speak(secret, "termux"))
            args, kwargs = run.call_args
            self.assertEqual(args[0], ["/safe/tts", secret])
            self.assertFalse(kwargs["shell"])
            self.assertIs(kwargs["stdout"], subprocess.DEVNULL)
            self.assertNotIn(secret, str(self.events))

    def test_audio_file_persistence_disabled_without_side_effect(self):
        with patch.object(voice, "_tool") as tool, patch.object(voice.subprocess, "run") as run:
            self.assertIsNone(voice.save_tts("private", "../../secret.wav"))
            tool.assert_not_called()
            run.assert_not_called()

    def test_symlinked_executable_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "tool"
            target.write_text("#!/bin/sh\nexit 0\n")
            target.chmod(0o700)
            alias = Path(d) / "alias"
            alias.symlink_to(target)
            with patch.object(voice.shutil, "which", return_value=str(alias)):
                self.assertIsNone(voice._tool("termux-speech-to-text"))

    def test_auto_tts_without_backend_does_not_echo_private_text(self):
        with patch.object(voice, "_has_termux", return_value=False), patch.object(voice, "_has_espeak", return_value=False), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertFalse(voice.speak("private text"))
            self.assertNotIn("private text", output.getvalue())


if __name__ == "__main__":
    unittest.main()
