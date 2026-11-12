#!/usr/bin/env python3
"""
Hermes Agent — Task Automation & Communication

Legacy Termux prototype. Scheduled shell commands are never run unattended.
Interactive shell tasks require an explicit, command-bound owner confirmation.
This is not a sandbox and is not connected to the native Android executor.
"""
import os, json, time, subprocess, threading
import hashlib
import shlex
from pathlib import Path
from datetime import datetime

VERSION = "1.1.0"
AGENT_NAME = "hermes"
HOME = Path.home() / "mrnothing"
LOG = HOME / "logs" / "hermes.log"

TASKS_FILE = HOME / "agents" / AGENT_NAME / "tasks.json"
MAX_SHELL_COMMAND_CHARS = 2048
SHELL_COMMAND_TIMEOUT_SECONDS = 30
_SHELL_EXECUTABLES = frozenset({
    "sh", "ash", "bash", "dash", "zsh", "fish", "csh", "tcsh", "ksh",
    "cmd", "powershell", "pwsh",
})


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [HERMES] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def notify(title, body):
    try:
        subprocess.run(["termux-notification", "--title", title, "--content", body],
                       capture_output=True, timeout=5, check=False)
    except Exception:
        pass


def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE) as f:
            return json.load(f)
    return {"scheduled": [], "completed": []}


def save_tasks(tasks):
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def _parse_shell_argv(command):
    """Parse one command without a shell; reject control characters and shells."""
    if (
        type(command) is not str
        or not command.strip()
        or len(command) > MAX_SHELL_COMMAND_CHARS
        or any(ord(char) < 32 or ord(char) == 127 for char in command)
    ):
        return None
    try:
        argv = shlex.split(command, posix=True)
    except ValueError:
        return None
    if not argv or any(not arg or "\x00" in arg for arg in argv):
        return None
    executable = Path(argv[0]).name.lower()
    if executable in _SHELL_EXECUTABLES:
        return None
    if (
        executable in {"busybox", "toybox"}
        and len(argv) > 1
        and argv[1].lower() in _SHELL_EXECUTABLES
    ):
        return None
    return argv


def _confirm_shell_command(command):
    """Require an interactive confirmation bound to the exact command text."""
    digest = hashlib.sha256(command.encode("utf-8")).hexdigest()[:10]
    expected = f"RUN {digest}"
    print("\n[HERMES] This task launches a local executable; it is not sandboxed.")
    print("[HERMES] Shell interpretation is disabled. Review the exact command:")
    print(command)
    try:
        response = input(f"Type {expected!r} to authorize this exact command: ").strip()
    except (EOFError, KeyboardInterrupt):
        return False
    return response == expected


def execute_task(task):
    if type(task) is not dict:
        log("Rejected invalid task record")
        return False

    log(f"Task requested: {task.get('name', 'unnamed')}")
    task_type = task.get("type", "shell")

    if task_type == "shell":
        command = task.get("command")
        argv = _parse_shell_argv(command)
        if argv is None:
            log("Blocked invalid command or shell-interpreter invocation")
            return False
        try:
            approved = _confirm_shell_command(command)
        except Exception:
            log("Blocked shell task: confirmation could not be obtained")
            return False
        if approved is not True:
            log("Shell task declined; no command was executed")
            return False

        log(f"Executing owner-confirmed argv task: {task.get('name', 'unnamed')}")
        try:
            result = subprocess.run(
                argv,
                shell=False,
                capture_output=True,
                text=True,
                timeout=SHELL_COMMAND_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            log(f"Command timed out after {SHELL_COMMAND_TIMEOUT_SECONDS} seconds")
            return False
        except OSError as error:
            log(f"Command could not start: {type(error).__name__}")
            return False

        output = (result.stdout or result.stderr or "").strip()
        if output:
            log(f"Result: {output[:4000]}")
        if result.returncode == 0:
            notify("Hermes", f"Task done: {task.get('name', 'command')}")
        return result.returncode == 0

    if task_type == "notify":
        notify(task.get("title", "Hermes"), task.get("body", ""))
        return True

    log("Rejected unsupported task type")
    return False


def schedule_loop():
    log("Hermes scheduler online; unattended shell execution is disabled")
    while True:
        tasks = load_tasks()
        now = time.time()
        changed = False
        for task in tasks.get("scheduled", []):
            run_at = task.get("run_at", 0)
            if run_at and now >= run_at and not task.get("done"):
                if task.get("type", "shell") == "shell":
                    if not task.get("approval_required"):
                        task["approval_required"] = True
                        task["approval_required_at"] = now
                        notify(
                            "Hermes approval required",
                            f"Task {task.get('name', 'unnamed')} is due. "
                            "No shell command was executed; review it in interactive mode.",
                        )
                        changed = True
                    continue

                success = execute_task(task)
                task["done"] = True
                task["completed_at"] = now
                task["success"] = bool(success)
                tasks.setdefault("completed", []).append(task)
                changed = True

        if changed:
            tasks["scheduled"] = [task for task in tasks["scheduled"] if not task.get("done")]
            save_tasks(tasks)
        time.sleep(60)


def interactive():
    print(f"\n[HERMES v{VERSION}] Task Automation Agent")
    print("Commands: add, list, run <id>, clear, exit\n")

    while True:
        try:
            cmd = input("hermes> ").strip().lower()
            if cmd == "exit":
                break
            elif cmd == "list":
                tasks = load_tasks()
                sched = tasks.get("scheduled", [])
                if not sched:
                    print("No scheduled tasks.")
                for i, task in enumerate(sched):
                    approval = " — interactive approval required" if task.get("approval_required") else ""
                    print(
                        f"  [{i}] {task.get('name')} — {task.get('type')} — "
                        f"{task.get('command', '')}{approval}"
                    )
            elif cmd == "add":
                name = input("Task name: ")
                cmd_str = input("Command (argv only; no shell interpretation): ")
                tasks = load_tasks()
                tasks.setdefault("scheduled", []).append({
                    "name": name,
                    "type": "shell",
                    "command": cmd_str,
                    "run_at": 0,
                })
                save_tasks(tasks)
                print(f"Task '{name}' added. Run it interactively to review and approve.")
            elif cmd.startswith("run "):
                idx = int(cmd.split()[1])
                tasks = load_tasks()
                task = tasks["scheduled"][idx]
                execute_task(task)
            elif cmd == "clear":
                tasks = load_tasks()
                tasks["completed"] = []
                save_tasks(tasks)
                print("Completed tasks cleared.")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    import sys
    if "--daemon" in sys.argv:
        schedule_loop()
    else:
        t = threading.Thread(target=schedule_loop, daemon=True)
        t.start()
        interactive()
