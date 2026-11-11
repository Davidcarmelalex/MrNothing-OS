# SEC-023B1B2D7 — Signed MemoryVault witness provenance preflight

**Status: DRAFT / PURE-JVM / NOT AUTHORIZING.** Stacked on SEC-023B1B2D6 PR #27; ultimately scoped to `feat/phase1-agentic-phone`. This is not a trusted witness service, enrollment flow, storage integration, or production security approval.

## Threat addressed

SEC-023B1B2D6 compares a record, marker, and witness, but all three are caller-supplied. A malicious writer can replace the entire bundle. This follow-on requires an Ed25519 signature over a domain-separated canonical witness payload (ASCII `mrnothing.memoryvault.witness.v1` plus NUL, big-endian signed 64-bit generation, 32-byte commitment). The public key is accepted only if its SHA-256 fingerprint matches a separately supplied pin. It also compares the signed witness generation against a separately supplied trusted high-watermark. Signatures are checked before recovery classifications.

**Trust caveat:** The pin and high-watermark are still caller-supplied. If an adversary can substitute both, this verifier does not prove anything. A replayed old valid signature is detected only when the high-watermark is genuinely protected from rollback. No Android Keystore marker alias by itself provides an undefeatable monotonic counter. The signed witness must be retained in a separate trust domain and pinned out-of-band under owner control before this code could be wired to any device operation.

## Fail-closed contract

- Missing/malformed record, marker, signature, key, pin, or watermark: `BLOCKED`.
- Wrong key, key-pin mismatch, invalid signature, changed commitment or malformed Ed25519 encoding: `BLOCKED`.
- Valid signed witness older than trusted high-watermark: `RECOVERY_REQUIRED_NOT_AUTHORIZED`; newer than high-watermark: `BLOCKED`.
- Valid signature and matched high-watermark with consistent structural snapshots: `VERIFIED_PROVENANCE_NOT_AUTHORIZED` — **not** permission to read/write memory.
- No automatic enrollment, reset, rollback, key rotation, service enablement, or agent execution.

## Transaction and recovery acceptance gates (NOT IMPLEMENTED)

1. Establish owner-confirmed initial public-key pin from an independently verified source. Provision and protect signer credentials outside app-controlled writable storage. Define signer rotation with two-key approval and audit.
2. Establish a durable independent high-watermark with explicit anti-rollback guarantees and post-power-loss recovery. Marker-first write ordering alone is not sufficient; define atomicity and crash matrices for each write phase.
3. Separate immutable generation enrollment anchor from per-use consent AES-GCM AAD. Require hardware-backed owner-authenticated CryptoObject proof and explicit revocation, cancellation and key invalidation.
4. Define uninstall, backup restore, factory reset, witness loss and offline verification behavior as fail-closed owner recovery, never silent re-enrollment.
5. Verify source and JUnit evidence, conduct independent Android/security review, and test actual Pixel 9 Pro StrongBox behavior with consent before any activation.

## Verification scope

12 synthetic JVM JUnit cases use ephemeral software Ed25519 keys. They verify signature and pin binding, stale/future witness refusal, changed commitment, wrong signer, forged-bundle refusal, and malformed inputs. No hardware-backed keys, signed release, TalkBack speech, emulator, installation, device flashing or OTA evidence is claimed. MemoryVault remains disabled/non-exported; PaperClip remains RAM-only; Android executor disconnected. `PROJECT-ADAPTER.md` remains project-specific and upstream `SKILL.md` is unverified.
