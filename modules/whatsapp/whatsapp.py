#!/usr/bin/env python3
"""
MrNothing OS — WhatsApp Module
Send messages via Termux API or WhatsApp Web fallback.
"""
import hashlib
import hmac
import re
import subprocess, shutil, json
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

HOME = Path.home() / "mrnothing"
LOG = HOME / "logs" / "whatsapp.log"
CONTACTS_FILE = HOME / "modules" / "whatsapp" / "contacts.json"
MAX_SMS_CHARS = 1600
MAX_WHATSAPP_MESSAGE_CHARS = 4096
_PHONE_RE = re.compile(r"\+?[1-9][0-9]{7,14}\Z")


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


def _normalize_phone(phone: str):
    """Accept a bounded international-style number; reject options and URI syntax."""
    if type(phone) is not str or len(phone) > 16 or _PHONE_RE.fullmatch(phone) is None:
        return None
    return phone


def _valid_message(message: str, maximum: int) -> bool:
    return (
        type(message) is str
        and bool(message)
        and len(message) <= maximum
        and "\x00" not in message
    )


def _sms_confirmation_challenge(phone: str, message: str) -> str:
    """Bind one typed confirmation to the exact recipient and message."""
    material = (
        b"mrnothing-termux-sms-v1\x00"
        + phone.encode("utf-8")
        + b"\x00"
        + message.encode("utf-8")
    )
    digest = hashlib.sha256(material).hexdigest()[:12].upper()
    return f"SEND SMS {digest}"


def _confirm_sms_send(phone: str, message: str) -> bool:
    """Require an internal, one-time confirmation; no caller-supplied callback."""
    expected = _sms_confirmation_challenge(phone, message)
    print("\n[MrNothing SMS] This sends a real SMS using the Termux user's permissions.")
    print(f"Recipient: {phone}")
    print("Exact message:")
    print(message)
    print("The confirmation is bound to this recipient and message only.")
    try:
        response = input(f"Type {expected!r} to authorize this SMS once: ")
    except (EOFError, KeyboardInterrupt):
        return False
    return type(response) is str and hmac.compare_digest(response.strip(), expected)


def send_message(phone: str, message: str) -> bool:
    """Open a prefilled WhatsApp compose screen; the owner must tap Send."""
    normalized = _normalize_phone(phone)
    if normalized is None or not _valid_message(message, MAX_WHATSAPP_MESSAGE_CHARS):
        log("WhatsApp compose request rejected: invalid recipient or message")
        return False
    digits = normalized.lstrip("+")
    url = f"https://wa.me/{digits}?text={quote(message, safe='')}"
    try:
        subprocess.run(
            ["termux-open-url", url],
            timeout=10,
            check=True,
            shell=False,
        )
        log(f"WhatsApp compose screen opened for {normalized}; owner must review and tap Send")
        return True
    except Exception as error:
        log(f"WhatsApp compose request failed: {type(error).__name__}")
        print(f"Could not open WhatsApp compose screen for {normalized}")
        return False


def send_sms(phone: str, message: str) -> bool:
    """Send one SMS only after exact recipient-and-message owner confirmation."""
    normalized = _normalize_phone(phone)
    if normalized is None or not _valid_message(message, MAX_SMS_CHARS):
        log("SMS rejected: invalid recipient or message")
        return False
    if not _has_termux():
        log("SMS requires Termux API")
        return False
    if not _confirm_sms_send(normalized, message):
        log("SMS cancelled or confirmation unavailable; no message was sent")
        return False
    try:
        subprocess.run(
            ["termux-sms-send", "-n", normalized, message],
            timeout=10,
            check=True,
            shell=False,
        )
        log(f"SMS command completed for {normalized}; carrier delivery is unverified")
        return True
    except Exception as error:
        log(f"SMS command failed: {type(error).__name__}")
        return False


def add_contact(name: str, phone: str):
    contacts = load_contacts()
    contacts[name] = phone
    save_contacts(contacts)
    log(f"Added contact: {name} -> {phone}")


def main():
    print("\n[MrNothing WhatsApp Module]")
    print("Commands: send <name/phone> <msg> (opens compose; owner taps Send), sms <phone> <msg> (exact confirmation required), add <name> <phone>, contacts, exit\n")

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
                print("Commands: send <name/phone> <msg> (opens compose; owner taps Send), sms <phone> <msg> (exact confirmation required), add <name> <phone>, contacts, exit")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
