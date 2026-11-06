#!/usr/bin/env python3
"""
MrNothing OS — Core Agent Brain
Autonomous command loop. Runs locally on Android via Termux.
"""

import os, sys, json, time, subprocess, threading
from pathlib import Path

VERSION = "1.0.0"
HOME = Path.home() / "mrnothing"
AGENTS_DIR = HOME / "agents"
MODULES_DIR = HOME / "modules"
LOG_FILE = HOME / "logs" / "core.log"
CONFIG_FILE = HOME / "config.json"

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

def list_agents():
    agents = []
    if AGENTS_DIR.exists():
        for d in AGENTS_DIR.iterdir():
            if d.is_dir() and (d / "agent.py").exists():
                agents.append(d.name)
    return agents

def run_agent(name, args=""):
    agent_path = AGENTS_DIR / name / "agent.py"
    if not agent_path.exists():
        log(f"Agent '{name}' not found", "ERROR")
        return
    log(f"Starting agent: {name}")
    subprocess.Popen(
        [sys.executable, str(agent_path)] + args.split(),
        cwd=str(AGENTS_DIR / name)
    )

def notify(title, msg):
    try:
        subprocess.run(
            ["termux-notification", "--title", title, "--content", msg],
            capture_output=True, timeout=5
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
    for agent_name in config.get("agents_enabled", []):
        agent_path = AGENTS_DIR / agent_name / "agent.py"
        if agent_path.exists():
            log(f"Auto-starting agent: {agent_name}")
            run_agent(agent_name)

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
