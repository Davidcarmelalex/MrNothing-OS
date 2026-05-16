#!/usr/bin/env python3
"""
PaperClip Agent — Local AI Reasoning Engine
Runs Transformers/GGUF models locally on Android CPU via Termux.
No API calls. No cloud. Zero cost.
"""
import os, sys, json, time, subprocess
from pathlib import Path
from datetime import datetime

VERSION = "1.0.0"
AGENT_NAME = "paperclip"
HOME = Path.home() / "mrnothing"
MODELS_DIR = HOME / "models"
LOG = HOME / "logs" / "paperclip.log"
MEMORY_FILE = HOME / "agents" / AGENT_NAME / "memory.json"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [PAPERCLIP] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f: f.write(line + "\n")

def load_memory():
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE) as f: return json.load(f)
    return {"conversations": [], "facts": []}

def save_memory(mem):
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w") as f: json.dump(mem, f, indent=2)

def remember(mem, role, content):
    mem["conversations"].append({"role": role, "content": content, "ts": time.time()})
    if len(mem["conversations"]) > 100:
        mem["conversations"] = mem["conversations"][-100:]
    save_memory(mem)

def check_model():
    """Check if a local model is available."""
    model_paths = list(MODELS_DIR.glob("*.gguf")) + list(MODELS_DIR.glob("*.bin"))
    return model_paths[0] if model_paths else None

def infer_llama_cpp(prompt, model_path):
    """Run inference via llama.cpp if installed."""
    llama_bin = Path.home() / "mrnothing" / "bin" / "llama-cli"
    if not llama_bin.exists():
        llama_bin = subprocess.run(["which", "llama-cli"], capture_output=True, text=True).stdout.strip()
    if not llama_bin:
        return None
    result = subprocess.run(
        [str(llama_bin), "-m", str(model_path), "-p", prompt, "-n", "256", "--temp", "0.7", "-q"],
        capture_output=True, text=True, timeout=120
    )
    return result.stdout.strip()

def infer_transformers(prompt):
    """Fallback: use transformers pipeline if available."""
    try:
        from transformers import pipeline
        log("Loading local transformer model (first run may be slow)...")
        gen = pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                       device=-1, max_new_tokens=200)
        result = gen(prompt, do_sample=True, temperature=0.7)
        return result[0]["generated_text"][len(prompt):]
    except ImportError:
        return None
    except Exception as e:
        log(f"Transformers error: {e}")
        return None

def think(prompt, mem):
    """Main reasoning function."""
    model = check_model()
    response = None

    if model:
        log(f"Using model: {model.name}")
        response = infer_llama_cpp(prompt, model)

    if not response:
        response = infer_transformers(prompt)

    if not response:
        # Fallback: rule-based responses
        p = prompt.lower()
        if "hello" in p or "hi" in p:
            response = "Hello. PaperClip online. How can I assist you?"
        elif "status" in p:
            response = f"MrNothing OS running. Memory: {len(mem['conversations'])} exchanges stored."
        elif "help" in p:
            response = "I can reason, remember, and assist with tasks. Ask me anything."
        else:
            response = f"[No local model loaded. Place a .gguf model in {MODELS_DIR}]"

    remember(mem, "assistant", response)
    return response

def main():
    print(f"\n[PAPERCLIP v{VERSION}] Local AI Reasoning Agent")
    model = check_model()
    if model:
        print(f"Model loaded: {model.name}")
    else:
        print(f"No model found. Place a GGUF model in: {MODELS_DIR}")
        print("Recommended: TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf (~700MB)")
    print("Type 'exit' to quit, 'memory' to see history.\n")

    mem = load_memory()

    while True:
        try:
            user_input = input("you> ").strip()
            if not user_input: continue
            if user_input.lower() == "exit": break
            if user_input.lower() == "memory":
                convs = mem.get("conversations", [])[-5:]
                for c in convs:
                    role = c["role"].upper()
                    print(f"  [{role}]: {c['content'][:100]}")
                continue

            remember(mem, "user", user_input)
            log(f"Thinking about: {user_input[:50]}...")
            response = think(user_input, mem)
            print(f"paperclip> {response}\n")

        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    main()
