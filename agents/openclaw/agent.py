#!/usr/bin/env python3
"""
OpenClaw — Security Intelligence Agent
Network scanning, vulnerability assessment, OSINT gathering.
Requires: nmap, curl, git (installed via pkg in Termux)
"""
import os, sys, subprocess, json, socket, time
from pathlib import Path
from datetime import datetime

VERSION = "1.0.0"
HOME = Path.home() / "mrnothing"
LOG = HOME / "logs" / "openclaw.log"
REPORTS_DIR = HOME / "reports" / "openclaw"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [OPENCLAW] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f: f.write(line + "\n")

def run(cmd, timeout=30):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() or result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR] {e}"

def check_tools():
    tools = {}
    for tool in ["nmap", "curl", "nc", "ping", "dig", "whois"]:
        result = run(f"which {tool}")
        tools[tool] = bool(result and not result.startswith("["))
    return tools

def scan_network(target):
    log(f"Scanning target: {target}")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {"target": target, "timestamp": time.time(), "results": {}}

    # Ping check
    ping = run(f"ping -c 3 -W 2 {target}")
    report["results"]["ping"] = ping

    # Port scan (basic)
    nmap_check = run("which nmap")
    if nmap_check:
        ports = run(f"nmap -T4 --top-ports 20 {target}", timeout=60)
        report["results"]["ports"] = ports
    else:
        # Manual port check for common ports
        open_ports = []
        for port in [22, 80, 443, 8080, 3000, 5000]:
            try:
                s = socket.socket()
                s.settimeout(1)
                if s.connect_ex((target, port)) == 0:
                    open_ports.append(port)
                s.close()
            except: pass
        report["results"]["ports"] = f"Open ports: {open_ports}"

    # DNS lookup
    dns = run(f"dig +short {target}")
    report["results"]["dns"] = dns

    # HTTP headers
    headers = run(f"curl -sI --max-time 5 http://{target}")
    report["results"]["http_headers"] = headers[:500] if headers else "No response"

    # Save report
    report_file = REPORTS_DIR / f"{target.replace('.','_')}_{int(time.time())}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    log(f"Report saved: {report_file}")
    return report

def wifi_info():
    result = run("termux-wifi-connectioninfo")
    return result

def main():
    print(f"\n[OPENCLAW v{VERSION}] Security Intelligence Agent")
    tools = check_tools()
    available = [t for t, ok in tools.items() if ok]
    print(f"Available tools: {', '.join(available) if available else 'none — run pkg install nmap'}")
    print("Commands: scan <target>, wifi, tools, reports, exit\n")

    while True:
        try:
            cmd = input("openclaw> ").strip()
            parts = cmd.split()
            if not parts: continue

            if parts[0] == "exit": break
            elif parts[0] == "tools":
                for t, ok in tools.items():
                    status = "✓" if ok else "✗"
                    print(f"  {status} {t}")
            elif parts[0] == "scan" and len(parts) > 1:
                target = parts[1]
                print(f"Scanning {target}... (this may take 30-60s)")
                report = scan_network(target)
                print(f"\n--- Scan Results for {target} ---")
                for k, v in report["results"].items():
                    print(f"\n[{k.upper()}]\n{v}")
            elif parts[0] == "wifi":
                print(wifi_info())
            elif parts[0] == "reports":
                reports = list(REPORTS_DIR.glob("*.json")) if REPORTS_DIR.exists() else []
                if reports:
                    for r in reports[-5:]:
                        print(f"  {r.name}")
                else:
                    print("No reports yet. Run a scan first.")
            else:
                print("Unknown command. Try: scan <ip/domain>, wifi, tools, reports, exit")

        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    main()
