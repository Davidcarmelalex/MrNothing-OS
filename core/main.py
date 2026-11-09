#!/usr/bin/env python3
"""
MrNothing OS — Core Agent Brain
Autonomous command loop. Runs locally on Android via Termux.
"""

import os, sys, json, time, subprocess, threading
import hashlib
import hmac
import re
import shlex
from pathlib import Path

VERSION = "1.0.0"
HOME = Path.home() / "mrnothing"
AGENTS_DIR = HOME / "agents"
MODULES_DIR = HOME / "modules"
LOG_FILE = HOME / "logs" / "core.log"
CONFIG_FILE = HOME / "config.json"

MAX_AGENT_STARTS = 8
MAX_AGENT_ARGUMENT_CHARS = 2048
MAX_AGENT_ARGUMENT_COUNT = 32
_AGENT_NAME_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}\Z")

BANNER = f"""
╔══════════════════════════════════════╗
║   MrNothing OS v{VERSION}              ║
║   Autonomous Enterprise Agent Core  ║
║   "Nothing runs everything."        ║
╚══════════════════════════════════════╝
"""

def log(msg, level="INFO"):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{level}] {msg}"
    print(entry)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(entry + "\n")
    except:
        pass

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    default = {
        "version": VERSION,
        "agents_enabled": ["hermes", "paperclip"],
        "voice_enabled": False,
        "web3_enabled": False,
        "auto_boot": True,
        "log_level": "INFO"
    }
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(default, f, indent=2)
    return default

def _resolve_agent_path(name):
    """Resolve only a real, direct child agent; reject traversal and symlinks."""
    if type(name) is not str or _AGENT_NAME_RE.fullmatch(name) is None:
        return None
    try:
        if AGENTS_DIR.is_symlink():
            return None
        root = AGENTS_DIR.resolve(strict=True)
        agent_dir = AGENTS_DIR / name
        agent_file = agent_dir / "agent.py"
        if agent_dir.is_symlink() or agent_file.is_symlink():
            return None
        resolved_dir = agent_dir.resolve(strict=True)
        resolved_file = agent_file.resolve(strict=True)
        if resolved_dir.parent != root or resolved_file.parent != resolved_dir:
            return None
        if not resolved_file.is_file():
            return None
        return resolved_file
    except (OSError, RuntimeError):
        return None


def list_agents():
    agents = []
    try:
        if AGENTS_DIR.is_symlink() or not AGENTS_DIR.is_dir():
            return agents
        for entry in AGENTS_DIR.iterdir():
            if _resolve_agent_path(entry.name) is not None:
                agents.append(entry.name)
    except OSError:
        return []
    return sorted(agents)


def _parse_agent_arguments(args):
    """Parse bounded CLI arguments without shell interpretation."""
    if type(args) is not str or len(args) > MAX_AGENT_ARGUMENT_CHARS:
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in args):
        return None
    try:
        argv = shlex.split(args, posix=True)
    except ValueError:
        return None
    if len(argv) > MAX_AGENT_ARGUMENT_COUNT:
        return None
    if any(not arg or "\x00" in arg for arg in argv):
        return None
    if sum(len(arg) for arg in argv) > MAX_AGENT_ARGUMENT_CHARS:
        return None
    return argv


def run_agent(name, args=""):
    agent_path = _resolve_agent_path(name)
    argv = _parse_agent_arguments(args)
    if agent_path is None:
        log(f"Agent '{name}' rejected: name/path is not an installed direct child", "ERROR")
        return None
    if argv is None:
        log(f"Agent '{name}' rejected: invalid or oversized arguments", "ERROR")
        return None
    log(f"Starting agent: {name}")
    try:
        return subprocess.Popen(
            [sys.executable, str(agent_path), *argv],
            cwd=str(agent_path.parent),
            shell=False,
        )
    except OSError as error:
        log(f"Agent '{name}' could not start: {type(error).__name__}", "ERROR")
        return None


def _configured_agent_names(value):
    """Validate the complete startup list; one invalid entry denies the batch."""
    if type(value) is not list or not value or len(value) > MAX_AGENT_STARTS:
        return []
    names = []
    for name in value:
        if name in names or _resolve_agent_path(name) is None:
            return []
        names.append(name)
    return names


def _confirm_agent_start(names):
    """Require one fresh, exact-list confirmation before configured auto-start."""
    if type(names) is not list or not names or len(names) > MAX_AGENT_STARTS:
        return False
    if any(_resolve_agent_path(name) is None for name in names):
        return False
    material = "\x00".join(("mrnothing-agent-start-v1", *names))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16].upper()
    challenge = f"START AGENTS {digest}"
    print("\n[MrNothing] Configured agents will start with this Termux user's privileges.")
    print("Review the exact agent list:")
    for name in names:
        print(f"  - {name}")
    print("This is not a sandbox or Android OS permission grant.")
    try:
        response = input(f"Type {challenge!r} to authorize this startup only: ").strip()
    except (EOFError, KeyboardInterrupt):
        return False
    return type(response) is str and hmac.compare_digest(response, challenge)


def start_configured_agents(config):
    """Start configured agents only after an explicit one-time owner confirmation."""
    if type(config) is not dict or config.get("auto_boot") is not True:
        return []
    names = _configured_agent_names(config.get("agents_enabled"))
    if not names:
        return []
    if not _confirm_agent_start(names):
        log("Configured agent auto-start declined or unavailable; no agents were started")
        return []
    started = []
    for name in names:
        if run_agent(name) is not None:
            started.append(name)
    return started

def notify(title, msg):
    try:
        subprocess.run(
            ["termux-notification", "--title", title, "--content", msg],
            capture_output=True, timeout=5, shell=False
        )
    except:
        pass

def handle_command(cmd, config):
    cmd = cmd.strip().lower()
    parts = cmd.split()
    if not parts:
        return

    if parts[0] in ("help", "?"):
        print("""
Commands:
  status          — System status + active agents
  agents          — List installed agents
  run <agent>     — Start a specific agent
  stop <agent>    — Stop a running agent
  config          — Show current config
  logs            — Tail last 20 log lines
  web3            — Web3 wallet interface
  voice           — Toggle voice mode
  scan            — Network intelligence scan
  version         — Version info
  exit / quit     — Shutdown MrNothing OS
""")

    elif parts[0] == "status":
        agents = list_agents()
        print(f"\n[STATUS] MrNothing OS v{VERSION}")
        print(f"  Home: {HOME}")
        print(f"  Installed agents: {', '.join(agents) if agents else 'none'}")
        print(f"  Voice: {'ON' if config.get('voice_enabled') else 'OFF'}")
        print(f"  Web3: {'ON' if config.get('web3_enabled') else 'OFF'}")
        print()

    elif parts[0] == "agents":
        agents = list_agents()
        if agents:
            print("\nInstalled agents:")
            for a in agents:
                print(f"  • {a}")
        else:
            print("No agents installed. Run installer to download agent packs.")

    elif parts[0] == "run" and len(parts) > 1:
        run_agent(parts[1], " ".join(parts[2:]))

    elif parts[0] == "logs":
        if LOG_FILE.exists():
            lines = LOG_FILE.read_text().splitlines()
            for line in lines[-20:]:
                print(line)
        else:
            print("No logs yet.")

    elif parts[0] == "config":
        print(json.dumps(config, indent=2))

    elif parts[0] == "version":
        print(f"MrNothing OS v{VERSION}")

    elif parts[0] in ("exit", "quit", "q"):
        log("Shutdown requested by user")
        notify("MrNothing OS", "Agent core shutting down")
        sys.exit(0)

    else:
        print(f"Unknown command: '{cmd}'. Type 'help' for commands.")

def main():
    print(BANNER)
    config = load_config()
    log(f"MrNothing OS v{VERSION} starting...")
    notify("MrNothing OS", f"Agent core v{VERSION} online")

    # Auto-start enabled agents
    start_configured_agents(config)

    print("Type 'help' for commands. Type 'exit' to quit.\n")

    while True:
        try:
            cmd = input("mrnothing> ").strip()
            handle_command(cmd, config)
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit.")
        except EOFError:
            break

if __name__ == "__main__":
    main()
