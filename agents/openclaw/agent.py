#!/usr/bin/env python3
"""OpenClaw — legacy, opt-in network diagnostics prototype.

Network scans are disabled by default. A scan requires an exact private IPv4
address in MRNOTHING_OPENCLAW_ALLOWED_TARGETS and a fresh interactive
confirmation bound to that address. This module is not an Android executor,
a sandbox, or proof that the operator owns a target.
"""
import hmac
import ipaddress
import json
import math
import os
import shutil
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

VERSION = "1.1.0"
HOME = Path.home() / "mrnothing"
LOG = HOME / "logs" / "openclaw.log"
REPORTS_DIR = HOME / "reports" / "openclaw"
ALLOWED_TARGETS_ENV = "MRNOTHING_OPENCLAW_ALLOWED_TARGETS"
MAX_ALLOWED_TARGETS = 32
MAX_ALLOWLIST_CHARS = 1024
MAX_ARG_COUNT = 32
MAX_ARG_CHARS = 4096
MAX_COMMAND_TIMEOUT_SECONDS = 60
PING_TIMEOUT_SECONDS = 10
NMAP_TIMEOUT_SECONDS = 60
CURL_TIMEOUT_SECONDS = 8

_ALLOWED_EXECUTABLES = frozenset({"ping", "nmap", "curl", "termux-wifi-connectioninfo"})
_AVAILABLE_TOOLS = tuple(sorted(_ALLOWED_EXECUTABLES))
_PRIVATE_SCAN_NETWORKS = tuple(
    ipaddress.ip_network(value)
    for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "169.254.0.0/16")
)
_COMMON_PORTS = (22, 80, 443, 8080, 3000, 5000)


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [OPENCLAW] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _canonical_private_ipv4(value):
    """Return a canonical private/local IPv4 literal; reject names and URLs."""
    if type(value) is not str or not value or len(value) > 15:
        return None
    try:
        address = ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        return None
    if not any(address in network for network in _PRIVATE_SCAN_NETWORKS):
        return None
    return str(address)


def _load_allowed_targets():
    """Load a bounded exact-IP allowlist. Any malformed entry denies all."""
    raw = os.environ.get(ALLOWED_TARGETS_ENV, "")
    if not raw or len(raw) > MAX_ALLOWLIST_CHARS:
        return frozenset()
    entries = raw.split(",")
    if not entries or len(entries) > MAX_ALLOWED_TARGETS:
        return frozenset()
    normalized = []
    for entry in entries:
        if not entry or entry != entry.strip():
            return frozenset()
        target = _canonical_private_ipv4(entry)
        if target is None:
            return frozenset()
        normalized.append(target)
    return frozenset(normalized)


def run(argv, timeout=30):
    """Run one fixed-tool argv command without a shell and with bounded input."""
    if not isinstance(argv, (list, tuple)) or not argv or len(argv) > MAX_ARG_COUNT:
        return "[ERROR] invalid argv"
    if any(type(arg) is not str or not arg or "\x00" in arg for arg in argv):
        return "[ERROR] invalid argv"
    if argv[0] not in _ALLOWED_EXECUTABLES:
        return "[ERROR] executable not allowlisted"
    if sum(len(arg) for arg in argv) > MAX_ARG_CHARS:
        return "[ERROR] argv too large"
    if type(timeout) not in (int, float) or not math.isfinite(timeout):
        return "[ERROR] invalid timeout"
    if timeout <= 0 or timeout > MAX_COMMAND_TIMEOUT_SECONDS:
        return "[ERROR] invalid timeout"
    try:
        result = subprocess.run(
            list(argv), shell=False, capture_output=True, text=True,
            timeout=timeout, check=False,
        )
        output = result.stdout.strip() or result.stderr.strip()
        if output:
            return output
        return "" if result.returncode == 0 else f"[EXIT {result.returncode}]"
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except (OSError, ValueError) as exc:
        return f"[ERROR] {exc}"


def check_tools():
    """Inspect local executable availability without invoking a shell."""
    return {tool: bool(shutil.which(tool)) for tool in _AVAILABLE_TOOLS}


def confirm_scan(target):
    """Require a one-time exact-target typed confirmation in the CLI."""
    challenge = f"SCAN {target}"
    print("Only scan systems you own or are expressly authorized to test.")
    print("This action sends network probes to the allowlisted private address.")
    try:
        answer = input(f"Type {challenge!r} to continue: ")
    except (EOFError, KeyboardInterrupt):
        return False
    return type(answer) is str and hmac.compare_digest(answer, challenge)


def _denied(target, reason):
    safe_target = target[:64] if type(target) is str else ""
    return {
        "target": safe_target, "timestamp": time.time(), "status": "DENIED",
        "reason": reason, "results": {},
    }


def _manual_port_check(target):
    open_ports = []
    for port in _COMMON_PORTS:
        connection = None
        try:
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.settimeout(1.0)
            if connection.connect_ex((target, port)) == 0:
                open_ports.append(port)
        except OSError:
            continue
        finally:
            if connection is not None:
                connection.close()
    return f"Open ports: {open_ports}"


def scan_network(target, confirm=None):
    """Scan one explicitly allowlisted private IPv4 target after confirmation.

    Direct callers must supply a confirmation callback returning exact Boolean True.
    """
    canonical = _canonical_private_ipv4(target)
    if canonical is None:
        return _denied(target, "INVALID_OR_NON_PRIVATE_IPV4")
    if canonical not in _load_allowed_targets():
        return _denied(canonical, "TARGET_NOT_ALLOWLISTED")
    if not callable(confirm):
        return _denied(canonical, "INTERACTIVE_CONFIRMATION_REQUIRED")
    try:
        approved = confirm(canonical) is True
    except Exception:
        approved = False
    if not approved:
        return _denied(canonical, "CONFIRMATION_DENIED")

    # No subprocess, socket, report directory or log side effect occurs before
    # exact-target allowlisting and fresh confirmation both succeed.
    log(f"Authorized private IPv4 scan: {canonical}")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.time()
    report = {
        "target": canonical,
        "timestamp": timestamp,
        "status": "COMPLETED",
        "authorization": {"allowlist": "exact-private-ipv4", "interactive_confirmation": True},
        "results": {},
    }
    if shutil.which("ping"):
        report["results"]["ping"] = run(
            ["ping", "-c", "3", "-W", "2", canonical], timeout=PING_TIMEOUT_SECONDS
        )
    else:
        report["results"]["ping"] = "ping unavailable"
    if shutil.which("nmap"):
        report["results"]["ports"] = run(
            ["nmap", "-T4", "--top-ports", "20", "--", canonical],
            timeout=NMAP_TIMEOUT_SECONDS,
        )
    else:
        report["results"]["ports"] = _manual_port_check(canonical)
    if shutil.which("curl"):
        url = f"http://{canonical}/"
        report["results"]["http_headers"] = run(
            ["curl", "-sI", "--max-time", "5", "--", url], timeout=CURL_TIMEOUT_SECONDS
        )
    else:
        report["results"]["http_headers"] = "curl unavailable"

    report_file = REPORTS_DIR / f"{canonical.replace('.', '_')}_{int(timestamp)}.json"
    with open(report_file, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    log(f"Report saved: {report_file}")
    return report


def wifi_info():
    """Read local Termux Wi-Fi connection details on explicit CLI request."""
    return run(["termux-wifi-connectioninfo"], timeout=10)


def main():
    print(f"\n[OPENCLAW v{VERSION}] Security Intelligence Agent")
    tools = check_tools()
    available = [tool for tool, ok in tools.items() if ok]
    print(f"Available tools: {', '.join(available) if available else 'none'}")
    print(
        f"Network scans are disabled unless {ALLOWED_TARGETS_ENV} contains "
        "exact private IPv4 addresses; each scan also requires typed confirmation."
    )
    print("Commands: scan <private-ipv4>, wifi, tools, reports, exit\n")
    while True:
        try:
            command = input("openclaw> ").strip()
            parts = command.split()
            if not parts:
                continue
            if parts[0] == "exit":
                break
            if parts[0] == "tools":
                for tool, ok in tools.items():
                    status = "✓" if ok else "✗"
                    print(f"  {status} {tool}")
            elif parts[0] == "scan" and len(parts) == 2:
                result = scan_network(parts[1], confirm=confirm_scan)
                if result["status"] == "DENIED":
                    print(f"Scan refused: {result['reason']}")
                    continue
                print(f"\n--- Scan Results for {result['target']} ---")
                for key, value in result["results"].items():
                    print(f"\n[{key.upper()}]\n{value}")
            elif parts[0] == "wifi":
                print(wifi_info())
            elif parts[0] == "reports":
                reports = list(REPORTS_DIR.glob("*.json")) if REPORTS_DIR.exists() else []
                if reports:
                    for report in reports[-5:]:
                        print(f"  {report.name}")
                else:
                    print("No reports yet. Run an authorized scan first.")
            else:
                print("Unknown command. Try: scan <private-ipv4>, wifi, tools, reports, exit")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
