# SEC-023 — Owner-authenticated encrypted PaperClip memory (design gate only)

**Status:** PROPOSED / NOT IMPLEMENTED. **Base:** `feat/phase1-agentic-phone` at `f42af837bcb8eed478cadbc472b7571441449a7a`. **Scope:** Android Pixel 9 Pro, local PaperClip prototype, M3/M6. This document does not enable persistence, grant permissions, or connect an executor.

## 1. Current boundary and threat model

PaperClip's `load_memory()` starts with memory OFF; `save_memory()` raises; `remember()` accepts a maximum of 100 RAM-only entries only after per-session opt-in; `clear_memory()` clears mutable references on opt-out and exit. Pre-existing `memory.json` is never loaded, migrated or deleted automatically. Python reference cleanup is **not** cryptographic erasure. The Termux process does not automatically inherit Android Keystore privileges or a trustworthy Android owner-authentication session.

Threats to address: lost/stolen unlocked phone; Android app/Termux sandbox compromise; copied backup; offline database tampering and rollback; ciphertext swap across users/devices; interrupted writes; revoked owner consent; metadata disclosure; plaintext temporary files; key invalidation after credential change; accidental legacy-file import; prompt-injection requests to export or erase memory. Explicit non-goals: protection against an already-compromised OS/kernel, root attacker, hardware side-channel or guaranteed RAM erasure.

## 2. Trust architecture and ownership

**Android native MemoryVault service (future, private and non-exported)** owns keys and encrypted records. It is the only component allowed to open its app-private storage or call Android Keystore. A separate, authenticated, package-signature-bound IPC interface may later serve PaperClip. Do not expose a general localhost HTTP endpoint, world-readable socket, unrestricted ContentProvider or raw key export. The existing Python/Termux agent remains session-only until this boundary is implemented and independently reviewed.

The Android service must bind each operation to the verified calling UID/package, app signing identity, owner profile, foreground owner-confirmed session, operation type and a one-time challenge. Reject calls from secondary profiles, changed signatures and stale/replayed challenges. IPC does not itself establish owner consent: require an Android system credential or BiometricPrompt CryptoObject-based cryptographic authentication with an explicit visible operation description. No background agent may silently refresh consent or authenticate on behalf of the owner.

**Keystore:** generate a non-exportable AES-256-GCM key in AndroidKeyStore with user authentication required for each cryptographic use (authentication validity duration zero where supported). Use StrongBox only after a capability/attestation check; no silent software fallback if the owner chose hardware-backed-only mode. Define explicit policy for unsupported devices, biometric enrollment changes, lock-screen removal and key invalidation. Do not reuse SEC-020 trust-anchor keys or signing keys as memory-encryption keys. Hardware-backed claims require actual Pixel 9 Pro evidence, not emulator results.

## 3. Data model, encryption and durability

Versioned envelope (canonical CBOR or strictly validated bounded JSON, chosen and frozen before implementation):
- `format_version`, `vault_id` (random 128-bit), `record_id` (random 128-bit), `generation` (monotonic within a trusted ledger), `created_at`, `expires_at`, `key_version`, `nonce` (96-bit unique per encryption key), `ciphertext` and `tag` (128-bit).
- AES-256-GCM authenticated associated data must bind exact canonical `format_version|vault_id|record_id|generation|key_version|owner_profile_id|application_identity`. Reject unknown fields, duplicate fields, oversized payloads, invalid UTF-8 and inconsistent timestamps.
- Limit to 100 conversation entries and 8,192 characters per entry; establish explicit ciphertext/database size caps, record-count cap and total retention TTL. Do not persist model prompts by default merely because an AI response was generated.
- Use a CSPRNG nonce source with collision/reuse tests; never reuse a nonce under the same key. Do not implement deterministic nonces without a reviewed crash-safe monotonic allocator.
- Stage ciphertext in a private same-filesystem temporary file, fsync file, atomic replace, fsync parent directory, then verify authenticated readback. Avoid plaintext temporary files and OS/log/crash-dump output. Use owner-only app-private storage, backup exclusions and explicit retention policy.
- Reject stale or tampered generations. A local ledger cannot defeat a privileged attacker restoring *both* ledger and ciphertext: hardware/remote monotonic anchoring remains a separate gate. Never claim rollback protection without evidence.

## 4. Consent, retention, export, deletion and recovery

Memory defaults OFF after every process start. Owner explicitly enables encrypted persistence in a dedicated Android screen after an informed retention choice (proposed: 7/30/90 days; default 7), with a clear separate switch for RAM-only memory. Every unlock/export/decrypt requires fresh cryptographic owner authentication; background agent reads are denied. Revocation immediately disables IPC admission, clears mutable caches best-effort and closes sessions. Key material is never sent to Python.

Export: owner-initiated foreground action, fresh authentication, explicit destination through Android Storage Access Framework, encrypted portable export with a **separate** owner-provided passphrase and memory-hard KDF (parameters to be independently reviewed); never silently export plaintext to shared storage. Log only a content-free event. Import must authenticate the export and require a separate owner confirmation; never automatically import legacy `memory.json`.

Delete: foreground owner-confirmed operation; revoke access first, delete the Keystore key (cryptographic erasure of encrypted records only), then remove ciphertext and indexes; report partial failures. Flash wear-leveling/backups may retain encrypted bytes, so do not promise physical byte erasure. Never automatically delete pre-existing plaintext legacy files; present a separate review/export/delete ceremony with explicit owner direction.

Recovery: if a key is invalidated, unavailable, or the database is corrupt, **fail closed**, show an owner-readable recovery explanation, and do not silently regenerate a key over existing data. A separately designed recovery mechanism must not bypass owner authentication or silently downgrade StrongBox policy. Crash/power-loss and credential-change tests must cover these states.

## 5. Acceptance gates and specialist ownership

| Gate | Owner | Objective pass condition |
| --- | --- | --- |
| SEC-023A threat/schema | Security + independent verifier | Threat-model review, canonical envelope fixtures, limits, nonce and AAD test vectors approved |
| SEC-023B Android vault | Android + security | Non-exported service, per-use auth, Keystore invalidation, package/UID verification, negative IPC tests |
| SEC-023C consent UX | UX/accessibility | TalkBack spoken walkthrough, 200% text, foreground consent/cancel/revoke, no dark patterns |
| SEC-023D crypto/durability | Security + CI/QA | Authenticated tamper/swap/replay rejection, atomic-crash matrix, nonce uniqueness, no plaintext artifacts |
| SEC-023E bridge | AI/agents + Android | Explicitly scoped, authenticated IPC; denied before consent/after revoke; 20 sandbox scenarios; no native executor |
| SEC-023F hardware/release | Hardware/release + independent verifier | Physical Pixel 9 Pro Keystore/StrongBox evidence, credential-change and reboot tests, backup/recovery drill, release-signing review |

**Required negative tests:** wrong caller UID; changed app signature; replayed/expired challenge; absent owner prompt; background caller; locked phone; malformed/oversized envelope; duplicate nonce; swapped vault/record; modified tag/AAD; stale generation; interrupted write at every fsync/rename point; revoked session; key invalidation; missing StrongBox; legacy-file symlink/hardlink; corrupt database; export cancellation; delete failure; app reinstall/backup restore. Verify with synthetic data only. No emulated Keystore result substitutes for physical hardware acceptance.

**Independent supervisor decision:** PENDING. This is a design artifact, not a verified cryptographic implementation or production permission to persist. Keep `save_memory()` fail-closed until every relevant gate is reviewed and approved. No milestone M1–M8 is declared complete.

## 6. Sequenced next action

First implement SEC-023A canonical schema + offline malformed-input and authenticated-data fixtures **without enabling persistence**. In parallel, request independent security review of SEC-021/SEC-022 command authorization and PRs #10–#12. Do not combine the memory vault with root, system flashing, telephony, device-control integrations or production release.
