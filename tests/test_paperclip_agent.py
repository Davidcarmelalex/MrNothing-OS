"""Security regressions for PaperClip's offline-only local inference boundary."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "agents" / "paperclip" / "agent.py"
SPEC = importlib.util.spec_from_file_location("paperclip_agent_under_test", MODULE_PATH)
AGENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AGENT)


class PaperclipOfflineInferenceTests(unittest.TestCase):
    def test_model_selection_accepts_only_direct_regular_local_gguf(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "mrnothing"
            models = home / "models"
            models.mkdir(parents=True)
            outside = Path(temporary) / "outside.gguf"
            outside.write_bytes(b"outside")
            (models / "00-link.gguf").symlink_to(outside)
            local = models / "01-local.gguf"
            local.write_bytes(b"local")
            with patch.object(AGENT, "HOME", home), patch.object(AGENT, "MODELS_DIR", models):
                self.assertEqual(AGENT.check_model(), local.resolve())

    def test_model_selection_rejects_symlinked_models_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "mrnothing"
            home.mkdir()
            target = root / "external-models"
            target.mkdir()
            (target / "model.gguf").write_bytes(b"model")
            models_link = home / "models"
            models_link.symlink_to(target, target_is_directory=True)
            with patch.object(AGENT, "HOME", home), patch.object(AGENT, "MODELS_DIR", models_link):
                self.assertIsNone(AGENT.check_model())

    def test_local_llama_binary_requires_expected_executable(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "mrnothing"
            binary = home / "bin" / "llama-cli"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"synthetic executable placeholder")
            binary.chmod(0o700)
            with patch.object(AGENT, "HOME", home):
                self.assertEqual(AGENT._local_llama_binary(), binary.resolve())

    def test_local_llama_binary_has_no_path_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "mrnothing"
            home.mkdir()
            with patch.object(AGENT, "HOME", home), patch.object(AGENT.subprocess, "run") as run:
                self.assertIsNone(AGENT._local_llama_binary())
                run.assert_not_called()

    def test_local_llama_binary_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "mrnothing"
            bin_dir = home / "bin"
            bin_dir.mkdir(parents=True)
            outside = root / "llama-cli"
            outside.write_bytes(b"outside")
            outside.chmod(0o700)
            (bin_dir / "llama-cli").symlink_to(outside)
            with patch.object(AGENT, "HOME", home):
                self.assertIsNone(AGENT._local_llama_binary())

    def test_inference_uses_only_fixed_local_argv_with_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "mrnothing"
            models = home / "models"
            bin_dir = home / "bin"
            models.mkdir(parents=True)
            bin_dir.mkdir()
            model = models / "model.gguf"
            model.write_bytes(b"synthetic model")
            binary = bin_dir / "llama-cli"
            binary.write_bytes(b"synthetic executable")
            binary.chmod(0o700)
            completed = subprocess.CompletedProcess([], 0, "local answer\n", "")
            with (
                patch.object(AGENT, "HOME", home),
                patch.object(AGENT, "MODELS_DIR", models),
                patch.object(AGENT.subprocess, "run", return_value=completed) as run,
            ):
                self.assertEqual(AGENT.infer_llama_cpp("hello", model), "local answer")
            argv = run.call_args.args[0]
            self.assertEqual(argv[0], str(binary.resolve()))
            self.assertEqual(argv[1:], [
                "-m", str(model.resolve()), "-f", "/dev/stdin",
                "-n", "256", "--temp", "0.7", "-q",
            ])
            self.assertNotIn("hello", argv)
            self.assertEqual(run.call_args.kwargs["input"], "hello")
            self.assertIs(run.call_args.kwargs["shell"], False)
            self.assertEqual(run.call_args.kwargs["timeout"], 120)
            self.assertIs(run.call_args.kwargs["check"], False)

    def test_prompt_pipe_works_with_local_synthetic_executable(self):
        """Verify the pipe handoff with a real child, without invoking a model."""
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "mrnothing"
            models = home / "models"
            bin_dir = home / "bin"
            models.mkdir(parents=True)
            bin_dir.mkdir()
            model = models / "model.gguf"
            model.write_bytes(b"synthetic model")
            binary = bin_dir / "llama-cli"
            binary.write_text(
                "#!/usr/bin/env python3\\n"
                "import sys\\n"
                "assert sys.argv[sys.argv.index('-f') + 1] == '/dev/stdin'\\n"
                "assert 'private test prompt' not in sys.argv\\n"
                "assert sys.stdin.read() == 'private test prompt'\\n"
                "print('pipe accepted')\\n",
                encoding="utf-8",
            )
            binary.chmod(0o700)
            with patch.object(AGENT, "HOME", home), patch.object(AGENT, "MODELS_DIR", models):
                self.assertEqual(
                    AGENT.infer_llama_cpp("private test prompt", model), "pipe accepted"
                )

    def test_inference_rejects_symlinked_model_before_subprocess(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "mrnothing"
            models = home / "models"
            bin_dir = home / "bin"
            models.mkdir(parents=True)
            bin_dir.mkdir()
            outside = root / "outside.gguf"
            outside.write_bytes(b"outside")
            model_link = models / "model.gguf"
            model_link.symlink_to(outside)
            binary = bin_dir / "llama-cli"
            binary.write_bytes(b"synthetic executable")
            binary.chmod(0o700)
            with (
                patch.object(AGENT, "HOME", home),
                patch.object(AGENT, "MODELS_DIR", models),
                patch.object(AGENT.subprocess, "run") as run,
            ):
                self.assertIsNone(AGENT.infer_llama_cpp("hello", model_link))
                run.assert_not_called()

    def test_oversized_prompt_is_rejected_before_subprocess(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "mrnothing"
            models = home / "models"
            bin_dir = home / "bin"
            models.mkdir(parents=True)
            bin_dir.mkdir()
            model = models / "model.gguf"
            model.write_bytes(b"model")
            binary = bin_dir / "llama-cli"
            binary.write_bytes(b"executable")
            binary.chmod(0o700)
            with (
                patch.object(AGENT, "HOME", home),
                patch.object(AGENT, "MODELS_DIR", models),
                patch.object(AGENT.subprocess, "run") as run,
            ):
                self.assertIsNone(AGENT.infer_llama_cpp("x" * (AGENT.MAX_PROMPT_CHARS + 1), model))
                run.assert_not_called()

    def test_no_model_uses_rule_based_fallback_without_process_or_network(self):
        memory = {"conversations": [], "facts": []}
        with (
            patch.object(AGENT, "check_model", return_value=None),
            patch.object(AGENT, "remember") as remember,
            patch.object(AGENT.subprocess, "run") as run,
        ):
            answer = AGENT.think("hello", memory)
        self.assertEqual(answer, "Hello. PaperClip online. How can I assist you?")
        remember.assert_called_once_with(memory, "assistant", answer)
        run.assert_not_called()

    def test_source_has_no_transformers_or_model_hub_fallback(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("transformers", source.lower())
        self.assertNotIn("TinyLlama/", source)
        self.assertNotIn("huggingface", source.lower())
        self.assertNotIn('"which", "llama-cli"', source)
        self.assertNotIn("infer_transformers", source)

    def test_prompt_content_is_not_written_to_prompt_log(self):
        secret_prompt = "private phrase that must not enter logs"
        memory = {"conversations": [], "facts": []}
        with (
            patch("builtins.input", side_effect=[secret_prompt, "exit"]),
            patch.object(AGENT, "load_memory", return_value=memory),
            patch.object(AGENT, "check_model", return_value=None),
            patch.object(AGENT, "remember"),
            patch.object(AGENT, "think", return_value="safe response"),
            patch.object(AGENT, "log") as log,
        ):
            AGENT.main()
        self.assertTrue(log.called)
        self.assertNotIn(secret_prompt, repr(log.call_args_list))


if __name__ == "__main__":
    unittest.main()
