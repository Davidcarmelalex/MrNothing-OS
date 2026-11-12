# SEC-023B0 — Dormant MemoryVault admission policy (2026-11-09)

**Scope:** `feat/phase1-agentic-phone`, scoped PR from `f42af837bcb8eed478cadbc472b7571441449a7a`. **Status:** code proposed, not approved, not wired to Android, not persistent memory.

## What is implemented

A pure-JVM `MemoryVaultAdmissionPolicy` checks a trusted Android caller/owner snapshot: exact app UID, Android primary owner profile (user 0), lowercase SHA-256 signing identity, foreground owner UI, unlocked device, explicit memory consent, and a claimed cryptographic owner-authentication result. `MemoryVaultOwnerIntentRegistry` supports one process-local, object-identity-bound intent per operation, with a 30-second monotonic deadline, single-use claim, replacement, cancellation, rollback denial, and synchronized concurrent claims. Sixteen synthetic JUnit tests cover these controls.

**Critical trust boundary:** all snapshot values must be collected by a future trusted Android platform adapter, never parsed from an LLM, Binder caller-provided payload, Python bridge, or HTTP message. The `authenticatedKeyUse` Boolean is *not* cryptographic proof; it must only be set after a verified Android Keystore CryptoObject operation, under a fresh owner-visible system authentication. Until then the policy is a tested prototype, not an authorization system. Tokens are not cryptographically random, not serializable IPC capabilities, and not a persistent replay ledger.

## Explicitly not implemented

No Android Service or exported Binder API, no Keystore key generation or AES-GCM, no owner credential UI, no encrypted record storage, no agent bridge, no read/write/export/delete functionality, no background access, no consent enrollment, no hardware test. `PaperClip.save_memory()` remains disabled; existing plaintext files are not touched. No root, firmware, physical Pixel, or release operations.

## Independent acceptance gates

1. Security reviewer validates that caller UID/user/profile and signing identity are obtained directly from platform APIs, and that no caller can spoof trusted snapshot values.
2. Android engineer integrates a non-exported native boundary and proves per-use Keystore CryptoObject authentication and key invalidation, including negative Binder tests.
3. QA runs Gradle/JUnit, static/security checks and emulator tests; hardware engineer later validates Pixel 9 Pro credential, StrongBox, lock state and recovery.
4. Independent supervisor signs off before any persistence or executor integration. SEC-023A canonical schema and SEC-023 design are separate draft PRs (#14/#13), not merged into this branch.

M1/M2/M6 remain in progress; M3 partial; M4 not started; M5 not accepted; M7/M8 blocked. The repository `PROJECT-ADAPTER.md` is project-specific. Upstream shared `SKILL.md` is absent/unverified and not claimed installed.
