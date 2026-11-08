#!/usr/bin/env python3
"""
PaperClip Agent — Local AI Reasoning Engine
Uses only user-provided local GGUF models through a local llama.cpp executable.
It never downloads model files or contacts a model hub.
"""
import os, time, subprocess
from pathlib import Path
from datetime import datetime

VERSION = "1.0.0"
AGENT_NAME = "paperclip"
HOME = Path.home() / "mrnothing"
MODELS_DIR = HOME / "models"
LOG = HOME / "logs" / "paperclip.log"
MEMORY_FILE = HOME / "agents" / AGENT_NAME / "memory.json"
MAX_PROMPT_CHARS = 8192
MAX_GENERATION_TOKENS = 256
INFERENCE_TIMEOUT_SECONDS = 120

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [PAPERCLIP] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f: f.write(line + "\n")

# Persistent plaintext conversation storage is intentionally disabled.
# Existing memory.json files are never read, migrated, overwritten, or deleted.
# A reviewed encrypted, owner-authenticated storage provider is required first.
MAX_SESSION_MEMORY_ENTRIES = 100

def load_memory():
    """Start a fresh opt-out session; never read legacy plaintext memory."""
    return {"conversations": [], "facts": [], "session_opt_in": False}

def save_memory(mem):
    """Fail closed if a legacy caller attempts persistent plaintext storage."""
    raise RuntimeError("Persistent PaperClip memory is disabled pending secure storage")

def clear_memory(mem):
    """Forget this process's session history and revoke memory opt-in."""
    if type(mem) is not dict:
        raise TypeError("Invalid memory session")
    mem["conversations"] = []
    mem["facts"] = []
    mem["session_opt_in"] = False

def remember(mem, role, content):
    """Retain bounded text in RAM only after explicit per-session opt-in."""
    if type(mem) is not dict or mem.get("session_opt_in") is not True:
        return False
    if role not in ("user", "assistant") or type(content) is not str:
        return False
    if not content or len(content) > MAX_PROMPT_CHARS or "\x00" in content:
        return False
    conversations = mem.get("conversations")
    if type(conversations) is not list:
        return False
    conversations.append({"role": role, "content": content, "ts": time.time()})
    del conversations[:-MAX_SESSION_MEMORY_ENTRIES]
    return True

def check_model():
    """Return a direct-child local GGUF model; reject symlinks and path escapes."""
    if HOME.is_symlink() or MODELS_DIR.is_symlink() or not MODELS_DIR.is_dir():
        return None
    try:
        home_root = HOME.resolve(strict=True)
        models_root = MODELS_DIR.resolve(strict=True)
        if models_root.parent != home_root:
            return None
        candidates = sorted(models_root.glob("*.gguf"))
    except (OSError, RuntimeError):
        return None

    for candidate in candidates:
        if candidate.is_symlink() or not candidate.is_file():
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if resolved.parent == models_root and resolved.suffix.lower() == ".gguf":
            return resolved
    return None


def _local_llama_binary():
    """Resolve only the expected local executable; never search PATH."""
    if HOME.is_symlink():
        return None
    try:
        home_root = HOME.resolve(strict=True)
        bin_dir = HOME / "bin"
        if bin_dir.is_symlink() or not bin_dir.is_dir():
            return None
        bin_root = bin_dir.resolve(strict=True)
        if bin_root.parent != home_root:
            return None
        candidate = bin_root / "llama-cli"
        if candidate.is_symlink() or not candidate.is_file():
            return None
        resolved = candidate.resolve(strict=True)
        if resolved.parent != bin_root or not os.access(resolved, os.X_OK):
            return None
        return resolved
    except (OSError, RuntimeError):
        return None


def infer_llama_cpp(prompt, model_path):
    """Run bounded inference with the fixed local llama.cpp executable only."""
    if (
        type(prompt) is not str
        or not prompt.strip()
        or len(prompt) > MAX_PROMPT_CHARS
        or "\x00" in prompt
    ):
        return None
    if not isinstance(model_path, (str, Path)):
        return None

    if HOME.is_symlink() or MODELS_DIR.is_symlink():
        return None
    try:
        home_root = HOME.resolve(strict=True)
        models_root = MODELS_DIR.resolve(strict=True)
        if models_root.parent != home_root:
            return None
        candidate = Path(model_path)
        if candidate.is_symlink() or not candidate.is_file():
            return None
        resolved_model = candidate.resolve(strict=True)
        if resolved_model.parent != models_root or resolved_model.suffix.lower() != ".gguf":
            return None
    except (OSError, RuntimeError, TypeError, ValueError):
        return None

    llama_bin = _local_llama_binary()
    if llama_bin is None:
        return None

    argv = [
        str(llama_bin),
        "-m", str(resolved_model),
        # Read the prompt from a pipe, not argv (/proc/<pid>/cmdline).
        # llama-cli supports -f FILE; /dev/stdin is an in-memory pipe on Android/Linux.
        "-f", "/dev/stdin",
        "-n", str(MAX_GENERATION_TOKENS),
        "--temp", "0.7",
        "-q",
    ]
    try:
        result = subprocess.run(
            argv,
            shell=False,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=INFERENCE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        log(f"Local inference failed: {type(error).__name__}")
        return None

    if result.returncode != 0:
        log("Local inference failed: llama.cpp returned a non-zero status")
        return None
    return (result.stdout or "").strip() or None


def think(prompt, mem):
    """Reason locally only; use deterministic fallback when no local model is ready."""
    response = None
    if type(prompt) is not str:
        response = "[Prompt rejected: expected text.]"
    elif len(prompt) > MAX_PROMPT_CHARS or "\x00" in prompt:
        response = f"[Prompt rejected: local limit is {MAX_PROMPT_CHARS} characters.]"
    else:
        model = check_model()
        if model:
            log("Using a local GGUF model; filename redacted")
            response = infer_llama_cpp(prompt, model)

        if not response:
            p = prompt.lower()
            if "hello" in p or "hi" in p:
                response = "Hello. PaperClip online. How can I assist you?"
            elif "status" in p:
                response = f"MrNothing OS running. Session memory: {len(mem['conversations'])} exchanges stored."
            elif "help" in p:
                response = "I can reason, remember, and assist with tasks. Ask me anything."
            else:
                response = f"[No local model loaded. Place a trusted .gguf model in {MODELS_DIR}]"

    remember(mem, "assistant", response)
    return response

def main():
    print(f"\n[PAPERCLIP v{VERSION}] Local AI Reasoning Agent")
    model = check_model()
    if model:
        print(f"Model loaded: {model.name}")
    else:
        print(f"No model found. Place a GGUF model in: {MODELS_DIR}")
        print("Add only a model you have independently verified; PaperClip never downloads model files.")
    print("Session memory is OFF by default; nothing is saved to disk.")
    print("Commands: 'memory on', 'memory off', 'memory', 'forget', 'exit'.\n")

    mem = load_memory()
    if MEMORY_FILE.exists() or MEMORY_FILE.is_symlink():
        print("WARNING: A legacy plaintext memory file exists. It was NOT read,")
        print("migrated, changed, or deleted. Owner-controlled cleanup is required.")

    try:
        while True:
            try:
                user_input = input("you> ").strip()
                if not user_input: continue
                command = user_input.lower()
                if command == "exit": break
                if command == "memory on":
                    mem["session_opt_in"] = True
                    print("Session-only memory enabled. It will not be saved to disk.")
                    continue
                if command in ("memory off", "forget"):
                    clear_memory(mem)
                    print("Session memory cleared and disabled.")
                    continue
                if command == "memory":
                    if not mem["session_opt_in"]:
                        print("Session memory is off. Type 'memory on' to opt in.")
                        continue
                    convs = mem.get("conversations", [])[-5:]
                    for c in convs:
                        role = c["role"].upper()
                        print(f"  [{role}]: {c['content'][:100]}")
                    continue
    
                remember(mem, "user", user_input)
                log("Processing prompt locally; content redacted")
                response = think(user_input, mem)
                print(f"paperclip> {response}\n")
    
            except (KeyboardInterrupt, EOFError):
                break
    finally:
        # Release session references on exit, EOF, or unexpected errors.
        # This does not guarantee secure erasure of Python/OS memory.
        clear_memory(mem)

if __name__ == "__main__":
    main()
