# SEC-023A — Canonical encrypted-memory envelope, offline preflight

**Status: implementation proposed for review; not approved cryptography.**
**Base:** `feat/phase1-agentic-phone` at `f42af837bcb8eed478cadbc472b7571441449a7a`.
**Design dependency:** draft PR #13, SEC-023 (not merged). This scoped change does not import or install an upstream engineering skill.

## Security boundary and implementation

`core/memory_vault_schema.py` is a dependency-free, side-effect-free Python **schema/fixture library** for synthetic records. It is not the native Android MemoryVault, a Keystore wrapper, an encryptor, an IPC endpoint or a storage provider. PaperClip `save_memory()` remains fail-closed and `load_memory()` remains RAM-only. No real user memory or encryption keys enter this code.

The v1 JSON envelope has exactly ten fields: `format_version`, `vault_id`, `record_id`, `generation`, `created_at`, `expires_at`, `key_version`, `nonce`, `ciphertext`, `tag`. JSON is UTF-8, sorted keys, compact separators, no extra whitespace, and no duplicate/unknown fields. Base64url is canonical unpadded. Identifiers are 16 bytes, nonce 12 bytes, tag 16 bytes, ciphertext 1–65,536 bytes, and envelope at most 100,000 bytes. Retention is strictly positive and no more than 90 days. Versions and generation are bounded integers, never booleans.

`canonical_aad` deterministically binds the exact v1 record/vault/generation/key version with a **caller-supplied trusted** owner profile and lowercase SHA-256 signing-identity digest. It does not authenticate those inputs. `preflight_record` can reject identity swaps, expired/future-dated records using a trusted clock, stale generations and a nonce already present in a **trusted per-key** ledger. It deliberately does not mutate the ledger or verify the AES-GCM tag; doing either here would be a false security claim. A future Android-native service must obtain owner/profile/app identity from platform APIs and verify AEAD before committing a crash-safe ledger update.

## Negative evidence and residual threats

Offline unit fixtures exercise canonical roundtrip, duplicate keys, unknown fields, wrong types, boolean integers, invalid UTF-8, malformed/oversized Base64, timestamps/TTL, identity-bound AAD, wrong record/vault, stale generation and nonce reuse. Synthetic tag changes remain schema-valid by design: cryptographic tamper rejection is a **future SEC-023D gate**, not achieved here.

**Important limitations:** No nonce generation or collision proof; no AES-GCM encrypt/decrypt; no StrongBox/Keystore or per-use owner prompt; no atomic durable generation ledger; no protection against restoring both ciphertext and ledger; no secure deletion; no spoken TalkBack or physical Pixel 9 Pro validation. SEC-021/SEC-022 authorization and IPC trust remain independent review blockers. Any integration with real memory is prohibited until SEC-023B/D/E and independent review pass.

## Review checklist

- [x] Static canonical v1 encoding/decoding and bounded negative fixtures
- [x] No filesystem/network/Android side effects and no persistence enabled
- [ ] Independent reviewer approves schema freeze and AAD byte contract
- [ ] Android owner/UID/signing identity trust and authentication verified
- [ ] AEAD/tag, nonce uniqueness, replay ledger and crash/power-loss gates verified
- [ ] Pixel 9 Pro hardware validation, accessibility and release-signing gates verified

**Acceptance decision:** SEC-023A code submitted for review; independent approval **PENDING**. M1/M2/M6 IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7/M8 BLOCKED. No milestone is complete.
