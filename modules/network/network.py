#!/usr/bin/env python3
"""MrNothing OS — consent-gated, bounded legacy network diagnostics.

This Termux CLI prototype is not an Android permission provider or executor.
Network probes are denied unless an exact private IPv4 target is allowlisted
and a fresh interactive confirmation is entered for each operation.
"""
import fcntl
import hmac
import ipaddress
import math
import os
import re
import shutil
import socket
import ssl
import struct
import subprocess
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import (
    HTTPSHandler,
    HTTPRedirectHandler,
    ProxyHandler,
    Request,
    build_opener,
)

HOME = Path.home() / "mrnothing"
LOG = HOME / "logs" / "network.log"

ALLOWED_TARGETS_ENV = "MRNOTHING_NETWORK_ALLOWED_TARGETS"
MAX_ALLOWED_TARGETS = 32
MAX_ALLOWLIST_CHARS = 1024

MAX_PING_COUNT = 3
PING_TIMEOUT_SECONDS = 10
PUBLIC_IP_HOST = "api.ipify.org"
PUBLIC_IP_URL = "https://api.ipify.org/"
PUBLIC_IP_TIMEOUT_SECONDS = 6
MAX_PUBLIC_IP_RESPONSE_BYTES = 45

MAX_MONITOR_DURATION_SECONDS = 300
MIN_MONITOR_INTERVAL_SECONDS = 30
MAX_MONITOR_INTERVAL_SECONDS = 60
MAX_MONITOR_PROBES = 10

_PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(value)
    for value in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
        "169.254.0.0/16",
    )
)


class ProbeRateLimiter:
    """Thread-safe, process-local limiter; not a cross-process security store."""

    def __init__(
        self,
        window_seconds=60.0,
        minimum_target_interval_seconds=10.0,
        maximum_per_target=3,
        maximum_global=6,
    ):
        self._window = float(window_seconds)
        self._minimum_target_interval = float(minimum_target_interval_seconds)
        self._maximum_per_target = int(maximum_per_target)
        self._maximum_global = int(maximum_global)
        self._events = deque()
        self._last_by_target = {}
        self._lock = threading.Lock()

    def acquire(self, target, now=None):
        if type(target) is not str or not target or len(target) > 128:
            return False
        current = time.monotonic() if now is None else now
        if type(current) not in (int, float) or not math.isfinite(current) or current < 0:
            return False

        with self._lock:
            while self._events and current - self._events[0][0] >= self._window:
                self._events.popleft()

            active_targets = {entry_target for _, entry_target in self._events}
            self._last_by_target = {
                key: value for key, value in self._last_by_target.items()
                if key in active_targets
            }

            last = self._last_by_target.get(target)
            if last is not None and current - last < self._minimum_target_interval:
                return False

            target_count = sum(1 for _, entry_target in self._events if entry_target == target)
            if target_count >= self._maximum_per_target or len(self._events) >= self._maximum_global:
                return False

            self._events.append((current, target))
            self._last_by_target[target] = current
            return True


RATE_LIMITER = ProbeRateLimiter()


def log(message):
    """Log fixed status text only; callers must not include targets or payloads."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] [NET] {message}"
    print(line)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        return


def _canonical_private_ipv4(value):
    """Return a canonical private/local IPv4 literal; never resolve hostnames."""
    if type(value) is not str or not value or len(value) > 15 or value != value.strip():
        return None
    try:
        address = ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        return None
    if address.is_multicast or address.is_unspecified:
        return None
    if not any(address in network for network in _PRIVATE_NETWORKS):
        return None
    return str(address)


def _load_allowed_targets():
    """Load a bounded exact private-IPv4 allowlist; malformed input denies all."""
    raw = os.environ.get(ALLOWED_TARGETS_ENV, "")
    if type(raw) is not str or not raw or len(raw) > MAX_ALLOWLIST_CHARS:
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


def _confirm(operation, target, detail):
    """Require an internal exact typed challenge; no caller callback is accepted."""
    challenge = f"ALLOW {operation} {target} {detail}"
    print("This operation sends a network request to the exact target shown.")
    print("Only proceed against systems you own or are expressly authorized to test.")
    try:
        answer = input(f"Type exactly: {challenge}\n> ")
    except (EOFError, KeyboardInterrupt):
        return False
    if type(answer) is not str:
        return False
    return hmac.compare_digest(answer.encode("utf-8"), challenge.encode("utf-8"))


def _resolve_ping_binary():
    """Resolve one executable from PATH and reject symlink/non-regular entries."""
    try:
        candidate = shutil.which("ping")
        if not candidate:
            return None
        path = Path(candidate)
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            return None
        if not os.access(path, os.X_OK):
            return None
        resolved = path.resolve(strict=True)
        if resolved != path:
            return None
        return str(resolved)
    except (OSError, RuntimeError, ValueError):
        return None


def get_local_ip():
    """Read a local interface IPv4 address via ioctl; sends no network packet."""
    try:
        for _index, interface in socket.if_nameindex():
            if not interface or interface == "lo":
                continue
            handle = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                request = struct.pack("256s", interface.encode("utf-8")[:15])
                response = fcntl.ioctl(handle.fileno(), 0x8915, request)
                candidate = socket.inet_ntoa(response[20:24])
                address = ipaddress.IPv4Address(candidate)
                if not address.is_unspecified and not address.is_loopback:
                    return str(address)
            except (OSError, ValueError, struct.error):
                continue
            finally:
                handle.close()
    except (OSError, AttributeError):
        pass
    return "127.0.0.1"


def get_public_ip():
    """Query one fixed HTTPS provider only after exact interactive disclosure/consent."""
    if not RATE_LIMITER.acquire(PUBLIC_IP_HOST):
        return None
    if not _confirm("PUBLIC-IP", PUBLIC_IP_HOST, "HTTPS-GET"):
        return None

    request = Request(
        PUBLIC_IP_URL,
        headers={"User-Agent": "MrNothing-OS-network-diagnostics/1.0"},
        method="GET",
    )
    try:
        opener = build_opener(
            ProxyHandler({}),
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )
        with opener.open(request, timeout=PUBLIC_IP_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return None
            body = response.read(MAX_PUBLIC_IP_RESPONSE_BYTES + 1)
        if len(body) > MAX_PUBLIC_IP_RESPONSE_BYTES:
            return None
        value = body.decode("ascii").strip()
        address = ipaddress.ip_address(value)
        log("Public IP lookup completed; provider response validated")
        return str(address)
    except (HTTPError, URLError, OSError, UnicodeDecodeError, ValueError, TimeoutError):
        log("Public IP lookup failed; details withheld")
        return None


class _NoRedirectHandler(HTTPRedirectHandler):
    """Refuse redirects so a fixed-host consent cannot authorize another host."""

    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def ping_host(host, count=1):
    """Ping one allowlisted private IPv4 literal after fresh exact-target consent."""
    canonical = _canonical_private_ipv4(host)
    if canonical is None:
        return {"host": "", "error": "INVALID_OR_NON_PRIVATE_IPV4"}
    if canonical not in _load_allowed_targets():
        return {"host": canonical, "error": "TARGET_NOT_ALLOWLISTED"}
    if type(count) is not int or count < 1 or count > MAX_PING_COUNT:
        return {"host": canonical, "error": "INVALID_COUNT"}
    if not RATE_LIMITER.acquire(canonical):
        return {"host": canonical, "error": "RATE_LIMITED"}
    if not _confirm("PING", canonical, f"COUNT-{count}"):
        return {"host": canonical, "error": "CONFIRMATION_DENIED"}

    binary = _resolve_ping_binary()
    if binary is None:
        return {"host": canonical, "error": "PING_UNAVAILABLE"}

    argv = [binary, "-n", "-c", str(count), "-W", "2", canonical]
    try:
        result = subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            text=True,
            timeout=PING_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"host": canonical, "error": "TIMEOUT"}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"host": canonical, "error": "PROBE_FAILED"}

    output = (result.stdout or "") + (result.stderr or "")
    loss_match = re.search(r"(\d+(?:\.\d+)?)%\s*packet loss", output, re.IGNORECASE)
    latency_match = re.search(
        r"(?:rtt|round-trip)\s+min/avg/max/(?:mdev|stddev)\s*=\s*[\d.]+/([\d.]+)/",
        output,
        re.IGNORECASE,
    )
    log("Authorized private IPv4 ping completed")
    return {
        "host": canonical,
        "status": "REPLIED" if result.returncode == 0 else "NO_REPLY",
        "packet_loss": f"{loss_match.group(1)}%" if loss_match else "unknown",
        "avg_latency": f"{latency_match.group(1)} ms" if latency_match else "unknown",
        "raw": output[:500],
    }


def speed_test():
    """Disable provider-selected speed tests until one exact target can be consented."""
    return {
        "error": "DISABLED_UNBOUNDED_PROVIDER_SELECTION",
        "note": "Speed-test providers may select multiple external servers; no request was made.",
    }


def monitor_connectivity(host, duration=60, interval=30):
    """Run a short interactive sequence; every probe needs per-probe confirmation."""
    canonical = _canonical_private_ipv4(host)
    if canonical is None:
        return {"status": "DENIED", "error": "INVALID_OR_NON_PRIVATE_IPV4", "results": []}
    if canonical not in _load_allowed_targets():
        return {"status": "DENIED", "error": "TARGET_NOT_ALLOWLISTED", "results": []}
    if type(duration) is not int or duration < 1 or duration > MAX_MONITOR_DURATION_SECONDS:
        return {"status": "DENIED", "error": "INVALID_DURATION", "results": []}
    if (
        type(interval) is not int
        or interval < MIN_MONITOR_INTERVAL_SECONDS
        or interval > MAX_MONITOR_INTERVAL_SECONDS
    ):
        return {"status": "DENIED", "error": "INVALID_INTERVAL", "results": []}

    probe_count = math.ceil(duration / interval)
    if probe_count < 1 or probe_count > MAX_MONITOR_PROBES:
        return {"status": "DENIED", "error": "PROBE_LIMIT_EXCEEDED", "results": []}

    started = time.monotonic()
    deadline = started + duration
    results = []
    for index in range(probe_count):
        scheduled = started + index * interval
        delay = scheduled - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        if time.monotonic() >= deadline:
            break
        result = ping_host(canonical, count=1)
        results.append(result)
        if "error" in result:
            break

    status = "COMPLETED" if results and all("error" not in item for item in results) else "STOPPED"
    return {"status": status, "target": canonical, "results": results}


def main():
    print("\n[MrNothing Network Module]")
    print(f"Ping allowlist: {ALLOWED_TARGETS_ENV} (exact private IPv4 literals only)")
    print("Every ping and public-IP lookup requires a fresh exact typed confirmation.")
    print("Commands: ip, public-ip, ping <private-ipv4> [count 1-3],")
    print("          monitor <private-ipv4> [duration 1-300] [interval 30-60],")
    print("          speed (disabled), exit\n")

    while True:
        try:
            command = input("net> ").strip().split()
            if not command:
                continue

            if command[0] == "exit":
                break
            if command[0] == "ip":
                print(f"  Local: {get_local_ip()}")
                public = get_public_ip()
                if public:
                    print(f"  Public: {public}")
                else:
                    print("  Public: not authorized or unavailable")
            elif command[0] == "public-ip" and len(command) == 1:
                public = get_public_ip()
                print(f"  Public: {public or 'not authorized or unavailable'}")
            elif command[0] == "ping" and len(command) in (2, 3):
                try:
                    count = int(command[2]) if len(command) == 3 else 1
                except ValueError:
                    print("  Invalid count; use 1-3.")
                    continue
                result = ping_host(command[1], count=count)
                for key, value in result.items():
                    print(f"  {key}: {value}")
            elif command[0] == "monitor" and len(command) in (2, 3, 4):
                try:
                    duration = int(command[2]) if len(command) >= 3 else 60
                    interval = int(command[3]) if len(command) == 4 else 30
                except ValueError:
                    print("  Invalid duration or interval.")
                    continue
                result = monitor_connectivity(command[1], duration, interval)
                print(f"  Status: {result['status']}")
                for item in result["results"]:
                    print(f"  Probe: {item}")
                if result.get("error"):
                    print(f"  Refused: {result['error']}")
            elif command[0] == "speed" and len(command) == 1:
                result = speed_test()
                print(f"  {result['error']}: {result['note']}")
            else:
                print("Commands: ip, public-ip, ping <private-ipv4> [1-3],")
                print("          monitor <private-ipv4> [duration 1-300] [interval 30-60],")
                print("          speed (disabled), exit")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
