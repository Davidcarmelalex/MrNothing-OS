#!/usr/bin/env python3
"""Legacy Termux voice helpers. No native Android microphone permission provider.

Microphone access requires fresh, exact interactive approval for each invocation.
Transcripts and TTS text are never written to the application event log.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

HOME = Path.home() / "mrnothing"
LOG = HOME / "logs" / "voice.log"
AUDIO_DIR = HOME / "audio"
MAX_SPEECH_CHARS = 1000
MAX_TRANSCRIPT_CHARS = 4096
MAX_LISTEN_SECONDS = 15
_EVENTS = frozenset({
    "TTS completed", "TTS unavailable", "TTS failed", "TTS input rejected",
    "STT unavailable", "STT denied", "STT completed", "STT failed",
    "STT transcript rejected", "STT duration rejected",
    "Audio persistence disabled",
})


def log(event: str) -> None:
    """Write only a fixed event code; never log speech, transcript or exception text."""
    event = event if event in _EVENTS else "event"
    line = f"[{datetime.now().strftime('%H:%M:%S')}] [VOICE] {event}"
    print(line)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        pass


def _tool(name: str) -> Optional[str]:
    """Resolve an installed executable without shell expansion or symlink aliases."""
    found = shutil.which(name)
    if not found:
        return None
    path = Path(found)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        return None
    if not os.access(path, os.X_OK):
        return None
    return str(path)


def _has_termux() -> bool:
    return _tool("termux-tts-speak") is not None


def _has_espeak() -> bool:
    return _tool("espeak") is not None


def _valid_text(value: object, limit: int) -> bool:
    return type(value) is str and 0 < len(value) <= limit and "\x00" not in value


def speak(text: str, engine: str = "auto") -> bool:
    """Speak bounded text locally. Explicit 'print' is the only text-display mode."""
    if not _valid_text(text, MAX_SPEECH_CHARS) or text.startswith("-") or engine not in ("auto", "termux", "espeak", "print"):
        log("TTS input rejected")
        return False
    if engine == "print":
        print(f"[TTS] {text}")
        return True
    if engine == "auto":
        engine = "termux" if _has_termux() else "espeak" if _has_espeak() else "unavailable"
    name = {"termux": "termux-tts-speak", "espeak": "espeak"}.get(engine)
    executable = _tool(name) if name else None
    if executable is None:
        log("TTS unavailable")
        return False
    try:
        subprocess.run([executable, text], timeout=30, check=True, shell=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        log("TTS failed")
        return False
    log("TTS completed")
    return True


def listen(duration: int = 5) -> str:
    """Capture one consented STT result. No transcript is persisted by this module.

    This terminal prompt is not Android credential authentication, nor proof of
    microphone permission, a local-only speech provider, or a native recording UI.
    """
    if type(duration) is not int or not 1 <= duration <= MAX_LISTEN_SECONDS:
        log("STT duration rejected")
        return ""
    executable = _tool("termux-speech-to-text")
    if executable is None:
        log("STT unavailable")
        return ""
    challenge = f"ALLOW MICROPHONE {duration} SECONDS"
    print("Microphone disclosure: Termux speech recognition may access the microphone "
          "and may use an installed speech provider. No recording is stored here. "
          "Use Android controls to revoke microphone access.")
    try:
        approval = input(f"Type exactly '{challenge}' to start this one capture: ")
    except (EOFError, KeyboardInterrupt):
        log("STT denied")
        return ""
    if approval != challenge:
        log("STT denied")
        return ""
    try:
        result = subprocess.run(
            [executable, "-l", "en", "-t", str(duration)],
            capture_output=True, text=True, timeout=duration + 10,
            check=True, shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        log("STT failed")
        return ""
    transcript = result.stdout.strip()
    if not _valid_text(transcript, MAX_TRANSCRIPT_CHARS):
        log("STT transcript rejected")
        return ""
    log("STT completed")
    return transcript


def save_tts(text: str, filename: Optional[str] = None) -> Optional[Path]:
    """Disabled until protected audio storage, retention and deletion are reviewed."""
    log("Audio persistence disabled")
    return None


def main() -> None:
    print("\n[MrNothing Voice Engine — legacy local CLI]")
    print(f"Termux TTS: {'available' if _has_termux() else 'not available'}")
    print(f"eSpeak: {'available' if _has_espeak() else 'not available'}")
    print("Commands: speak <text>, listen, exit\n")
    while True:
        try:
            cmd = input("voice> ").strip()
            if cmd == "exit":
                break
            if cmd.startswith("speak "):
                speak(cmd[6:])
            elif cmd == "listen":
                transcript = listen()
                if transcript:
                    print(f"Heard: {transcript}")  # Only the requesting local terminal sees it.
            else:
                print("Commands: speak <text>, listen, exit")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
