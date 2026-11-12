# AGENT-006M — PaperClip inference prompt argv privacy

**Date:** 2026-11-09
**Repository/branch:** Davidcarmelalex/MrNothing-OS / `feat/phase1-agentic-phone`
**Parent source head:** `003e376f3fe7a5439d22dee3ff6a72d6e97676a4`
**Status:** bounded mitigation; independent review and physical-device validation pending.

## Finding

The standalone PaperClip Termux inference helper previously passed the complete user prompt to `llama-cli -p PROMPT`. On Linux/Android this places potentially sensitive text in the child process argument vector, observable through process-inspection interfaces according to platform privileges. Disabling plaintext `memory.json` in AGENT-006L did not close this separate disclosure path.

## Bounded implementation

Retain the existing strict local model/executable checks, shell-free fixed arguments, prompt-length validation, timeout, and failure redaction. Replace `-p PROMPT` with `-f /dev/stdin`, and pass the exact validated prompt as `subprocess.run(input=prompt, text=True)`. The prompt no longer appears in the constructed child argv and no prompt file is written by this Python code.

The CLI `-f FILE` interface is documented by llama.cpp; compatibility with the actual user-installed binary and Android/Termux `/dev/stdin` must still be tested before claiming production acceptance. A synthetic local child validates the pipe handoff only; it is not a real model-inference test.

## Verification and limitations

- Offline targeted PaperClip suite: 21/21 passed on isolated maverix-vps clone.
- Full `bash scripts/phase1-preflight.sh`: 917/917 Python tests passed; launcher source gate passed.
- `git diff --check` and Python compilation passed.
- No actual GGUF model, microphone, device, network access, or physical Pixel was used.
- CI, Android builds, emulator and reproducibility for the new commit require exact-head GitHub evidence.
- Stdin data remains in process memory and may be exposed to a same-UID/privileged attacker. Child stdout/stderr, model behavior and OS swap are not certified as confidential. This change does not create an Android sandbox or production inference provider.
- Real llama-cli version compatibility and prompt echo behavior remain open hardware/runtime gates.

**Independent reviewer:** verify argument-vector confidentiality, pipe EOF behavior, Termux compatibility, absence of new disk writes, and fail-closed behavior when the installed CLI lacks `-f`. No executor integration is authorized.

**Milestones:** M1/M2/M6 in progress, M3 partial, M4 not started, M5 not accepted, M7/M8 blocked. No milestone complete.
