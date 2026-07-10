#!/usr/bin/env python3
"""
MrNothing OS — WhatsApp Module
Send messages via Termux API or WhatsApp Web fallback.
"""
import subprocess, shutil, json
from pathlib import Path
from datetime import datetime

HOME = Path.home() / "mrnothing"
LOG = HOME / "logs" / "whatsapp.log"
CONTACTS_FILE = HOME / "modules" / "whatsapp" / "contacts.json"


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [WA] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def _has_termux() -> bool:
    return shutil.which("termux-sms-send") is not None


def load_contacts() -> dict:
    if CONTACTS_FILE.exists():
        with open(CONTACTS_FILE) as f:
            return json.load(f)
    return {}


def save_contacts(contacts: dict):
    CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTACTS_FILE, "w") as f:
        json.dump(contacts, f, indent=2)


def send_message(phone: str, message: str) -> bool:
    """Send WhatsApp message via Termux."""
    try:
        subprocess.run(
            ["termux-open-url", f"https://wa.me/{phone}?text={message}"],
            timeout=10, check=True
        )
        log(f"Sent to {phone}: {message[:30]}...")
        return True
    except Exception as e:
        log(f"Send error: {e}")
        print(f"Fallback — open manually: https://wa.me/{phone}?text={message}")
        return False


def send_sms(phone: str, message: str) -> bool:
    """Send SMS via Termux."""
    if not _has_termux():
        log("SMS requires Termux API")
        return False
    try:
        subprocess.run(
            ["termux-sms-send", "-n", phone, message],
            timeout=10, check=True
        )
        log(f"SMS sent to {phone}")
        return True
    except Exception as e:
        log(f"SMS error: {e}")
        return False


def add_contact(name: str, phone: str):
    contacts = load_contacts()
    contacts[name] = phone
    save_contacts(contacts)
    log(f"Added contact: {name} -> {phone}")


def main():
    print("\n[MrNothing WhatsApp Module]")
    print("Commands: send <name/phone> <msg>, sms <phone> <msg>, add <name> <phone>, contacts, exit\n")

    contacts = load_contacts()

    while True:
        try:
            cmd = input("wa> ").strip().split(None, 2)
            if not cmd:
                continue

            if cmd[0] == "exit":
                break
            elif cmd[0] == "contacts":
                for name, phone in contacts.items():
                    print(f"  {name}: {phone}")
            elif cmd[0] == "add" and len(cmd) == 3:
                add_contact(cmd[1], cmd[2])
            elif cmd[0] == "send" and len(cmd) == 3:
                recipient = contacts.get(cmd[1], cmd[1])
                send_message(recipient, cmd[2])
            elif cmd[0] == "sms" and len(cmd) == 3:
                send_sms(cmd[1], cmd[2])
            else:
                print("Commands: send <name/phone> <msg>, sms <phone> <msg>, add <name> <phone>, contacts, exit")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
