#!/usr/bin/env python3
"""
Hermes Agent — Task Automation & Communication
Part of MrNothing OS autonomous agent framework
"""
import os, json, time, subprocess, threading
from pathlib import Path
from datetime import datetime

VERSION = "1.0.0"
AGENT_NAME = "hermes"
HOME = Path.home() / "mrnothing"
LOG = HOME / "logs" / "hermes.log"

TASKS_FILE = HOME / "agents" / AGENT_NAME / "tasks.json"

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
                       capture_output=True, timeout=5)
    except: pass

def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE) as f:
            return json.load(f)
    return {"scheduled": [], "completed": []}

def save_tasks(tasks):
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def execute_task(task):
    log(f"Executing task: {task.get('name', 'unnamed')}")
    task_type = task.get("type", "shell")

    if task_type == "shell":
        cmd = task.get("command", "")
        if cmd:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            log(f"Result: {result.stdout.strip() or result.stderr.strip()}")
            notify("Hermes", f"Task done: {task.get('name', cmd[:30])}")
            return result.returncode == 0

    elif task_type == "notify":
        notify(task.get("title", "Hermes"), task.get("body", ""))
        return True

    return False

def schedule_loop():
    log("Hermes scheduler online")
    while True:
        tasks = load_tasks()
        now = time.time()
        for task in tasks.get("scheduled", []):
            run_at = task.get("run_at", 0)
            if run_at and now >= run_at and not task.get("done"):
                success = execute_task(task)
                task["done"] = True
                task["completed_at"] = now
                tasks["completed"].append(task)
        tasks["scheduled"] = [t for t in tasks["scheduled"] if not t.get("done")]
        save_tasks(tasks)
        time.sleep(60)

def interactive():
    print(f"\n[HERMES v{VERSION}] Task Automation Agent")
    print("Commands: add, list, run <id>, clear, exit\n")
    tasks = load_tasks()

    while True:
        try:
            cmd = input("hermes> ").strip().lower()
            if cmd == "exit": break
            elif cmd == "list":
                sched = tasks.get("scheduled", [])
                if not sched:
                    print("No scheduled tasks.")
                for i, t in enumerate(sched):
                    print(f"  [{i}] {t.get('name')} — {t.get('type')} — {t.get('command','')}")
            elif cmd == "add":
                name = input("Task name: ")
                cmd_str = input("Shell command: ")
                tasks["scheduled"].append({"name": name, "type": "shell", "command": cmd_str, "run_at": 0})
                save_tasks(tasks)
                print(f"Task '{name}' added.")
            elif cmd.startswith("run "):
                idx = int(cmd.split()[1])
                t = tasks["scheduled"][idx]
                execute_task(t)
            elif cmd == "clear":
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
