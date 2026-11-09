# AGENT-006H — PaperClip offline inference and legacy external-effect inventory

**Status:** Implemented on `feat/phase1-agentic-phone`; exact-head CI is triggered by the implementation commit.
**Audit baseline:** `0f849e9d0fbbafba6c75bc69de2f8fa50432217b` (2026-11-08).
**Scope:** legacy Termux/Python entrypoints and their separation from the native Android command path.

**Historical snapshot notice (2026-11-09):** The memory, voice and network rows below describe the AGENT-006H audit baseline, not the latest feature-branch behavior. AGENT-006L disables PaperClip plaintext persistence and requires per-session RAM opt-in; AGENT-006O adds best-effort mutable-reference clearing; AGENT-006J/K subsequently harden network and voice. Existing legacy memory.json is preserved but not automatically loaded. No encrypted memory provider or Android executor has been approved. Consult the current docs/THREAT-MODEL.md TM-15 and section 8 for active memory controls.

## 1. Finding and bounded correction

At the audit baseline, `agents/paperclip/agent.py` described a local-only model but fell back to:

```python
pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", ...)
```

That remote model identifier can cause Transformers to contact a model hub and retrieve model/config artifacts during ordinary prompt handling. It did not mean the prompt itself was necessarily uploaded, but it contradicted the repository's no-implicit-network/local-only claim and introduced unpinned model-artifact retrieval.

AGENT-006H removes the Transformers/model-hub fallback. PaperClip now:

- Selects only a direct-child `.gguf` file in its expected local models directory.
- Rejects symlinked model directories, model files and executable paths.
- Resolves only `$HOME/mrnothing/bin/llama-cli`; it no longer searches `PATH` or invokes `which`.
- Uses a fixed argv list with `shell=False`, a 120-second timeout and a 256-token generation cap.
- Rejects non-text, NUL-containing and over-8,192-character prompts before process invocation.
- Uses its deterministic rule-based fallback when no verified local model/executable is available; it does not download a substitute.
- Redacts prompt content from the PaperClip processing log.

A local model and executable are still user-supplied code/data. This change does not verify model signatures, provenance, safety or output quality and is not a sandbox.

## 2. Legacy external-effect inventory

| Component | Observed effect surface | Current control / status | Required gate before agent integration |
|---|---|---|---|
| PaperClip | Local model process; persistent conversation memory; model-hub retrieval existed at baseline | Remote fallback removed; local GGUF/direct executable paths and bounded argv only. Memory remains plaintext local JSON capped at 100 conversation entries. | Model provenance/signature policy; explicit memory opt-in, encryption, retention/deletion and process isolation. |
| HERMES legacy shell | Starts arbitrary non-shell executables as the Termux user | Exact command-bound interactive confirmation, argv parsing, `shell=False`, bounds/timeouts; scheduled shell tasks are not run unattended. | Replace with typed capabilities; no arbitrary executable tool in native registry; cancellation and privilege separation. |
| Core agent launcher | Starts direct-child Python agents with Termux-user privileges | Rejects traversal/symlinks and bounds argv; configured startup requires exact-list confirmation. Manual CLI `run` is an explicit interactive command but not a strong authorization boundary. | Per-agent capability manifest and lifecycle control; never treat this as Android permission or sandbox enforcement. |
| OpenClaw | Private-network probes and local tool invocation | Fixed executable allowlist, argv-only `shell=False`, bounded timeouts, exact private IPv4 allowlist and per-target typed confirmation. | Prove target authorization separately; network rate limits/audit; keep disconnected from Android router. |
| Network module | Public-IP lookup via `curl`, speed test via `speedtest-cli`, arbitrary-host ping and fixed-host connectivity monitoring | Standalone CLI; commands can cause outbound traffic. No agent registry or per-target confirmation is present in this module. | Explicit per-operation disclosure and opt-in; exact target allowlist; bounded probes; no unattended monitoring. |
| Voice engine | Microphone capture via `termux-speech-to-text`; TTS via Termux/eSpeak; transcript and speech prefixes are logged | Standalone CLI; `listen` requires an interactive command but there is no Android permission provider or visible native capture lifecycle. | Android runtime permission, visible recording state, bounded duration, immediate stop/revocation, no transcript logging by default and retention/deletion controls. |
| WhatsApp/SMS | SMS through Termux API; WhatsApp compose URL | SMS requires exact recipient/message-bound typed challenge; WhatsApp only opens compose and owner taps Send. | Strong Android owner/session binding, durable audit/idempotency and delivery-state honesty before integration. |
| Web3 wallet | Private keys are serialized in plaintext `wallets.json`; if `eth_account` is unavailable, fallback creates unrelated random address/private-key strings | Standalone legacy CLI; no native signer or agent integration. The fallback is not a valid cryptographic wallet derivation. | Block use with real funds; remove plaintext key persistence and invalid fallback; design an audited hardware-backed signer and recovery process. |
| Android native command path | Potential device actions through Kotlin router | `CommandRouter` remains fail-closed; no production executor, AccessibilityService, MediaProjection provider, shell bridge or device action is connected. | Independent AGENT-006C review, platform permission provider, external-effect journal, idempotency, cancellation and per-action consent. |

## 3. Native capability allowlist status

The current native Android external-effect allowlist is **empty**. No legacy Termux module is approved for registration as a native device-action tool. This document is an audit record, not a runtime policy engine; it does not itself enforce module isolation. The Kotlin `CommandRouter` fail-closed behavior and the absence of a connected executor remain the actual current boundary.

## 4. Regression tests and execution limits

New tests in `tests/test_paperclip_agent.py` cover local direct-child GGUF selection, symlink rejection, fixed local executable resolution, no PATH fallback, argv-only invocation, prompt bounds, no model-hub fallback and prompt-log redaction. Subprocess boundaries are mocked. Existing threat-model structural tests now require unique threat IDs through TM-15.

No network probe, model download, model execution, SMS, WhatsApp message, microphone capture, wallet generation/signing, Termux installation, Android installation or physical-device operation was performed by this audit or its tests.

## 5. Residual blockers and next work

- **Critical wallet blocker:** plaintext private-key persistence and the invalid fallback must be removed before the wallet can be used with real funds or exposed to an agent.
- **Network module:** add explicit target-scoped owner consent and safe rate limits before any agent exposure.
- **Voice module:** add Android-mediated microphone permission, visible recording lifecycle, cancellation and transcript-retention controls.
- **PaperClip memory:** conversation history remains plaintext local JSON; explicit opt-in, encryption and deletion controls are not yet implemented.
- **Independent review:** AGENT-006C remains pending. This legacy-module inventory does not approve an Android executor or change the stop condition.

Milestones remain M1/M2/M6 IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7 BLOCKED and M8 BLOCKED. No milestone is COMPLETE.
