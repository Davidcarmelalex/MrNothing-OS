# AGENT-006N — PaperClip session teardown and filename privacy

**Scope:** legacy `agents/paperclip/agent.py` only; no Android permission, network service, model download, persistent memory provider, or real device executor is enabled.

## Finding and bounded change

PaperClip already defaults memory to off and disables plaintext disk persistence, but an opted-in session previously relied on Python process termination to release references when the user exited, input ended, or an unexpected exception occurred. Its inference path also logged the selected local GGUF filename and displayed it in the startup banner, which could encode owner-private information.

- Wrap the interactive loop in `try/finally`, calling `clear_memory(mem)` for explicit exit, EOF, KeyboardInterrupt, and unexpected exceptions.
- Keep exception propagation and all existing consent semantics. Do not read, migrate, overwrite, or delete legacy `memory.json`.
- Replace the filename-bearing inference log and startup banner with fixed redacted messages.
- Add seven offline regressions in `tests/test_paperclip_session_cleanup.py`. They exercise a real opted-in in-memory prompt before teardown, preserve a synthetic legacy file byte-for-byte, and verify no filename reaches the event logger or startup banner.
- No external model, microphone, wallet, network target, or Android device is used by these tests.

## Security limitations

Clearing Python list references is **not cryptographic erasure**. Copies may remain in Python allocator arenas, native model memory, process swap, terminal scrollback, or operating-system buffers. The owner-visible terminal can still display responses. A model binary and model files remain trusted local inputs, not independently verified binaries. This change does not create encrypted persistent memory or verify a hardware-backed key.

## Independent acceptance gate

A separate reviewer must inspect the exact implementation SHA, verify the tests actually ran, challenge exception paths and legacy-file preservation, and record findings. Before persistent memory is re-enabled, a separate design and implementation review must cover Android Keystore key wrapping, fresh owner authentication, authenticated encryption, atomic crash-safe storage, retention/export/delete controls, rollback, backup/sync policy, migration of existing plaintext files only after informed consent, and hardware validation.

**Milestones:** M1/M2/M6 in progress; M3 partial; M4 not started; M5 not accepted; M7/M8 blocked. No milestone complete, no independent approval claimed. Upstream shared `SKILL.md` remains unverified; local `PROJECT-ADAPTER.md` is project-specific.
