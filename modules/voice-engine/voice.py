#!/usr/bin/env python3
"""
MrNothing Voice Engine — Whisper STT + TTS
Local speech recognition via OpenAI Whisper (open source).
TTS via termux-tts-speak or pyttsx3.
"""
import os, sys, subprocess, time, json
from pathlib import Path

VERSION = "1.0.0"
HOME = Path.home() / "mrnothing"
AUDIO_DIR = HOME / "audio"
LOG = HOME / "logs" / "voice.log"

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] [VOICE] {msg}")

def speak(text):
    """Text-to-speech output."""
    # Try termux-tts-speak first (native Android TTS)
    try:
        result = subprocess.run(
            ["termux-tts-speak", text],
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    # Fallback: pyttsx3
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        return True
    except ImportError:
        pass

    # Last resort: espeak
    try:
        subprocess.run(["espeak", text], capture_output=True, timeout=10)
        return True
    except FileNotFoundError:
        log("No TTS available. Install termux-api or run: pip install pyttsx3")
        return False

def record_audio(duration=5, output_file=None):
    """Record audio via termux-microphone-record."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    if not output_file:
        output_file = AUDIO_DIR / f"recording_{int(time.time())}.wav"
    try:
        log(f"Recording {duration}s of audio...")
        subprocess.run(
            ["termux-microphone-record", "-f", str(output_file), "-d", str(duration)],
            timeout=duration + 5
        )
        return output_file if Path(output_file).exists() else None
    except FileNotFoundError:
        log("termux-microphone-record not found. Install termux-api package.")
        return None
    except Exception as e:
        log(f"Recording error: {e}")
        return None

def transcribe(audio_file):
    """Transcribe audio using OpenAI Whisper (local)."""
    try:
        import whisper
        log("Loading Whisper model (tiny — fast on mobile)...")
        model = whisper.load_model("tiny")
        log(f"Transcribing {audio_file}...")
        result = model.transcribe(str(audio_file))
        return result["text"].strip()
    except ImportError:
        log("Whisper not installed. Run: pip install openai-whisper")
        return None
    except Exception as e:
        log(f"Transcription error: {e}")
        return None

def listen_and_respond(callback=None):
    """Full loop: record → transcribe → callback → speak response."""
    audio = record_audio(duration=5)
    if not audio:
        speak("Microphone not available.")
        return None

    text = transcribe(audio)
    if not text:
        speak("Could not transcribe audio.")
        return None

    log(f"Heard: {text}")

    if callback:
        response = callback(text)
        if response:
            speak(response)
        return response

    return text

def main():
    print(f"\n[VOICE ENGINE v{VERSION}] Whisper STT + Android TTS")
    print("Commands: speak <text>, listen, test, status, exit\n")

    while True:
        try:
            cmd = input("voice> ").strip()
            if not cmd: continue
            parts = cmd.split(None, 1)

            if parts[0] == "exit": break

            elif parts[0] == "speak" and len(parts) > 1:
                speak(parts[1])

            elif parts[0] == "listen":
                print("Listening for 5 seconds...")
                text = listen_and_respond()
                if text:
                    print(f"Transcribed: {text}")

            elif parts[0] == "test":
                speak("MrNothing voice engine online. Systems nominal.")

            elif parts[0] == "status":
                # Check what's available
                tts_ok = subprocess.run(["which", "termux-tts-speak"],
                                        capture_output=True).returncode == 0
                mic_ok = subprocess.run(["which", "termux-microphone-record"],
                                        capture_output=True).returncode == 0
                whisper_ok = False
                try:
                    import whisper
                    whisper_ok = True
                except: pass
                print(f"  TTS (termux-tts-speak): {'✓' if tts_ok else '✗'}")
                print(f"  Microphone:             {'✓' if mic_ok else '✗'}")
                print(f"  Whisper STT:            {'✓' if whisper_ok else '✗'}")

            else:
                print("Commands: speak <text>, listen, test, status, exit")

        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    main()
