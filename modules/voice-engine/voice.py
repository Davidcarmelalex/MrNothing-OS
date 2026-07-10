#!/usr/bin/env python3
"""
MrNothing OS — Voice Engine Module
Text-to-speech and speech-to-text wrappers using Termux API.
Falls back to espeak on systems without Termux.
"""
import subprocess, shutil, os
from pathlib import Path
from datetime import datetime

HOME = Path.home() / "mrnothing"
LOG = HOME / "logs" / "voice.log"
AUDIO_DIR = HOME / "audio"


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [VOICE] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def _has_termux() -> bool:
    return shutil.which("termux-tts-speak") is not None


def _has_espeak() -> bool:
    return shutil.which("espeak") is not None


def speak(text: str, engine: str = "auto") -> bool:
    """Text-to-speech."""
    if engine == "auto":
        engine = "termux" if _has_termux() else "espeak" if _has_espeak() else "print"

    try:
        if engine == "termux":
            subprocess.run(["termux-tts-speak", text], timeout=30, check=True)
            log(f"TTS (termux): {text[:50]}...")
            return True
        elif engine == "espeak":
            subprocess.run(["espeak", text], timeout=30, check=True)
            log(f"TTS (espeak): {text[:50]}...")
            return True
        else:
            print(f"[TTS] {text}")
            return True
    except Exception as e:
        log(f"TTS error: {e}")
        return False


def listen(duration: int = 5) -> str:
    """Speech-to-text. Requires Termux API."""
    if not _has_termux():
        log("STT requires Termux API. Install: pkg install termux-api")
        return ""

    try:
        result = subprocess.run(
            ["termux-speech-to-text", "-l", "en", "-t", str(duration)],
            capture_output=True, text=True, timeout=duration + 10
        )
        text = result.stdout.strip()
        log(f"STT heard: {text[:50]}...")
        return text
    except Exception as e:
        log(f"STT error: {e}")
        return ""


def save_tts(text: str, filename: Optional[str] = None) -> Optional[Path]:
    """Save TTS to audio file."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        filename = f"tts_{datetime.now().strftime('%H%M%S')}.wav"
    path = AUDIO_DIR / filename

    if _has_termux():
        try:
            subprocess.run(
                ["termux-tts-speak", "-f", str(path), text],
                timeout=30, check=True
            )
            log(f"Saved TTS: {path}")
            return path
        except Exception as e:
            log(f"Save TTS error: {e}")
    return None


def main():
    print("\n[MrNothing Voice Engine]")
    print(f"Termux TTS: {'available' if _has_termux() else 'not available'}")
    print(f"eSpeak: {'available' if _has_espeak() else 'not available'}")
    print("Commands: speak <text>, listen, exit\n")

    while True:
        try:
            cmd = input("voice> ").strip()
            if cmd == "exit":
                break
            elif cmd.startswith("speak "):
                speak(cmd[6:])
            elif cmd == "listen":
                text = listen()
                print(f"Heard: {text}")
            else:
                print("Commands: speak <text>, listen, exit")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    from typing import Optional
    main()
