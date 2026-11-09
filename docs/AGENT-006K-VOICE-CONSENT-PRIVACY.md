# AGENT-006K — legacy voice consent and transcript privacy

**Date:** 2026-11-09  
**Branch:** feat/phase1-agentic-phone  
**Audited parent:** d07390768eae1747fe759726b7d524d50a291299  
**Scope:** modules/voice-engine/voice.py, offline regression tests, threat model and roadmap.

## Finding
The legacy Termux voice module accepted a microphone-capture call without a fresh internal confirmation, logged the first 50 characters of captured transcripts and TTS content, and allowed caller-supplied audio filenames without a protected retention/deletion design. The file also referenced Optional only in its __main__ guard, which could cause a NameError when imported as a library.

## Bounded implementation
- Each listen call requires an exact local typed challenge bound to a duration from 1 to 15 seconds. EOF, interruption, malformed durations, absent Termux STT executable or declined confirmation fail closed.
- The prompt discloses microphone access and possible use of an installed speech provider. The caller cannot inject a confirmation callback. No unattended microphone capture is authorized.
- The STT subprocess uses a fixed argv list, shell=False, check=True and a bounded timeout; transcripts must be nonempty, contain no NUL and fit 4,096 characters. Transcripts are returned to the explicitly requesting caller but not persisted or written to event logs.
- TTS input is limited to 1,000 characters, NUL and option-like leading dash input is rejected, and subprocess output is suppressed. TTS text and exception details are not logged. Auto mode no longer silently prints speech text when no backend exists.
- Executable discovery rejects symlink aliases, non-files and non-executable paths; however PATH selection remains a same-user trust assumption.
- save_tts is deliberately disabled pending a reviewed encrypted/protected audio retention and deletion design. Existing audio files are not touched.
- Event logs contain only fixed status codes. The explicit interactive CLI still displays the recognized transcript to the requesting terminal; terminal scrollback is outside this module's retention guarantees.

## Tests
12 offline unittest cases cover denial before subprocess, strict duration and challenge matching, bounded argv/timeout, transcript rejection, TTS redaction, audio persistence disablement, executable symlink rejection and no unintended fallback echo. All subprocess/input boundaries are mocked. No microphone capture, audio playback, Termux installation, device action or network request is performed by the tests.

## Residual security limitations
Typed terminal confirmation is **not** Android system-credential authentication. Termux STT may use an external provider; no local-only speech processing is established. Terminating the CLI process does not prove that a separate speech provider stopped recording. The module has no Android runtime permission provider, visible native capture indicator, platform revocation callback, encrypted transcript store, or independently reviewed retention/deletion policy. The native Android action executor remains disconnected. Do not register this module as an agent device capability.

## Gate and milestones
Independent security review must challenge PATH/executable trust, transcript output to callers, speech-provider disclosure, terminal confirmation spoofing and microphone cancellation. Physical Pixel 9 Pro validation is absent. M1/M2/M6 remain IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7 BLOCKED and M8 BLOCKED. No milestone is COMPLETE.
