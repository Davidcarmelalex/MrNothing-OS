# SEC-023B1B2D6 — MemoryVault generation-anchor preflight

**Status: DRAFT / OFFLINE DIAGNOSTIC ONLY.** This branch stacks on PR #26 and ultimately targets `feat/phase1-agentic-phone`. The upstream shared SKILL.md is absent/unverified; PROJECT-ADAPTER.md is project-specific.

## Threat and non-goals

PR #26's AES-GCM canary detects replacement of the key alone. If an adversary can replace both the key and canary reference, it can generate a matching new pair. The new pure-JVM `MemoryVaultGenerationAnchorPolicy` compares three *caller-supplied* snapshots: a generation-bound active record, a monotonic marker snapshot, and a separately pinned witness commitment. The commitment is SHA-256 over a fixed domain, big-endian signed 64-bit generation, 32-byte generation ID, and 32-byte reference hash.

This is **not** a trusted anchor implementation. It cannot authenticate a witness, prove hardware rollback resistance, or detect replacement of *all three* inputs. It never authorizes persistence, authentication, recovery, key use or an agent action. Both positive and recovery outcomes explicitly end in `NOT_AUTHORIZED`. It is not wired into MemoryVaultService, Android Keystore, OwnerAuthorityTrustStore, or the executor.

## Structural refusal contract

- Missing witness, missing marker, malformed sizes, invalid generation, marker/record generation mismatch or commitment mismatch: BLOCKED (except a strictly older record).
- Record older than a marker or witness: RECOVERY_REQUIRED_NOT_AUTHORIZED. No automatic replay, reset, enrollment or retry.
- Record ahead of either marker or witness: BLOCKED.
- Missing record with valid positive marker and witness: RECOVERY_REQUIRED_NOT_AUTHORIZED; never treat as a new first install.
- All three snapshots consistent: CONSISTENT_INPUTS_NOT_AUTHORIZED, which is only a synthetic comparison result.

## Required independent trusted-anchor design before integration

1. Define a separate trust domain for a durable, authenticated witness. A caller-provided hash or Boolean is **not** evidence. Android Keystore marker aliases can detect app-private record rollback only while marker keys survive. They are not an undefeatable hardware monotonic counter. Reuse the SEC-020B1 marker-first *ordering pattern* only after threat review; do not share its authority trust aliases or keys with MemoryVault.
2. Specify generation-ID and reference enrollment under explicit owner credential consent, marker-before-record commit, atomic durable write, post-write readback, recovery-only transitions and uninstall/factory-reset semantics. Never auto-re-enroll after lost witness or alias.
3. Define per-use consent separately from the generation witness. The SEC-023B1B2D5 canary currently includes a consent digest in AAD; a reusable enrollment anchor requires a distinct immutable generation-bound reference and a separate per-use authenticated operation. Do not silently reuse a per-consent ciphertext as a permanent witness.
4. Require a trusted, pinned external or independently protected high-watermark for stronger rollback claims, with offline/unavailable state fail-closed. A privileged attacker controlling OS/Keystore and witness storage remains outside demonstrated protection.
5. Add hardware-backed owner-authenticated CryptoObject integration, simultaneous key+reference+record replacement tests, process death, power loss, key invalidation, revocation, caller isolation, TalkBack and consented Pixel 9 Pro StrongBox evidence.
6. Obtain independent Android/security review before any MemoryVault activation or release.

## Evidence scope

17 synthetic pure-JVM JUnit cases and source/CI regressions. No Android emulator, real credential, physical device, hardware StrongBox, memory persistence, installation, OTA or signed release. MemoryVault remains disabled and non-exported; PaperClip RAM-only; executor disconnected. No M1–M8 milestone independently complete.
