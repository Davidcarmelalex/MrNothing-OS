#!/usr/bin/env python3
"""MrNothing Network Intelligence Module"""
import subprocess, json, socket, time
from pathlib import Path

HOME = Path.home() / "mrnothing"
REPORTS = HOME / "reports" / "network"

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except: return "[ERROR]"

def wifi_scan():
    return run("termux-wifi-scaninfo")

def my_ip():
    return run("curl -s --max-time 5 https://api.ipify.org")

def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return "unknown"

def port_scan(host, ports=[22,80,443,8080,3000,5000,8888]):
    open_ports = []
    for port in ports:
        try:
            s = socket.socket()
            s.settimeout(0.5)
            if s.connect_ex((host, port)) == 0:
                open_ports.append(port)
            s.close()
        except: pass
    return open_ports

def main():
    print("\n[NETWORK v1.0] Intelligence Module")
    print("Commands: wifi, myip, localip, portscan <host>, exit\n")
    while True:
        try:
            cmd = input("network> ").strip().split()
            if not cmd: continue
            if cmd[0] == "exit": break
            elif cmd[0] == "wifi": print(wifi_scan())
            elif cmd[0] == "myip": print(f"Public IP: {my_ip()}")
            elif cmd[0] == "localip": print(f"Local IP: {local_ip()}")
            elif cmd[0] == "portscan" and len(cmd) > 1:
                host = cmd[1]
                print(f"Scanning {host}...")
                ports = port_scan(host)
                print(f"Open ports: {ports if ports else 'none found'}")
            else: print("Unknown command")
        except (KeyboardInterrupt, EOFError): break

if __name__ == "__main__":
    main()
