#!/usr/bin/env python3
"""
MrNothing OS — Network Module
Speed test, connectivity monitoring, IP info.
"""
import subprocess, shutil, socket, json, time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

HOME = Path.home() / "mrnothing"
LOG = HOME / "logs" / "network.log"


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [NET] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def get_public_ip() -> Optional[str]:
    """Get public IP address."""
    try:
        result = subprocess.run(
            ["curl", "-s", "https://api.ipify.org"],
            capture_output=True, text=True, timeout=10
        )
        ip = result.stdout.strip()
        log(f"Public IP: {ip}")
        return ip
    except Exception as e:
        log(f"IP fetch error: {e}")
        return None


def get_local_ip() -> str:
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def ping_host(host: str, count: int = 3) -> Dict:
    """Ping a host and return stats."""
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "2", host],
            capture_output=True, text=True, timeout=count * 3
        )
        output = result.stdout
        # Parse ping output
        packet_loss = "unknown"
        avg_time = "unknown"

        for line in output.split("\n"):
            if "packet loss" in line:
                packet_loss = line.split(",")[2].split("%")[0].strip() + "%"
            if "avg" in line and "/" in line:
                parts = line.split("/")
                if len(parts) >= 5:
                    avg_time = parts[4].split(" ")[0] + " ms"

        return {
            "host": host,
            "packet_loss": packet_loss,
            "avg_latency": avg_time,
            "raw": output[:500],
        }
    except Exception as e:
        return {"host": host, "error": str(e)}


def speed_test() -> Dict:
    """Run speed test."""
    log("Running speed test...")
    try:
        # Try speedtest-cli
        result = subprocess.run(
            ["speedtest-cli", "--simple"],
            capture_output=True, text=True, timeout=120
        )
        lines = result.stdout.strip().split("\n")
        data = {"raw": result.stdout}
        for line in lines:
            if "Ping" in line:
                data["ping"] = line.split(":")[1].strip()
            elif "Download" in line:
                data["download"] = line.split(":")[1].strip()
            elif "Upload" in line:
                data["upload"] = line.split(":")[1].strip()
        log(f"Speed test complete: {data.get('download', 'N/A')} down")
        return data
    except Exception as e:
        log(f"Speed test error: {e}")
        return {"error": str(e), "note": "Install speedtest-cli: pkg install speedtest-cli"}


def monitor_connectivity(interval: int = 60, duration: int = 300):
    """Monitor connectivity for a duration."""
    log(f"Monitoring connectivity for {duration}s (interval: {interval}s)")
    start = time.time()
    while time.time() - start < duration:
        result = ping_host("8.8.8.8", count=1)
        status = "UP" if "error" not in result else "DOWN"
        log(f"Connectivity: {status} (latency: {result.get('avg_latency', 'N/A')})")
        time.sleep(interval)


def main():
    print("\n[MrNothing Network Module]")
    print("Commands: ip, ping <host>, speed, monitor, exit\n")

    while True:
        try:
            cmd = input("net> ").strip().split()
            if not cmd:
                continue

            if cmd[0] == "exit":
                break
            elif cmd[0] == "ip":
                print(f"  Local: {get_local_ip()}")
                pub = get_public_ip()
                if pub:
                    print(f"  Public: {pub}")
            elif cmd[0] == "ping" and len(cmd) > 1:
                result = ping_host(cmd[1])
                for k, v in result.items():
                    print(f"  {k}: {v}")
            elif cmd[0] == "speed":
                result = speed_test()
                for k, v in result.items():
                    print(f"  {k}: {v}")
            elif cmd[0] == "monitor":
                monitor_connectivity()
            else:
                print("Commands: ip, ping <host>, speed, monitor, exit")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
