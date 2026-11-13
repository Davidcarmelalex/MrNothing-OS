# SEC-023B1B2D8 — Offline witness enrollment crash-window model

**Status: NOT AUTHORIZING.** This is a pure-JVM, unwired diagnostic and negative-test specification, not a durable transaction implementation or trusted enrollment service. MemoryVault remains disabled, non-exported, and disconnected from PaperClip and agent execution.

## Threat and trust boundary

SEC-023B1B2D7 validates an Ed25519 witness against a **caller-supplied** pin and high-watermark. That proves neither the independent provenance of the pin nor the durability or rollback resistance of the watermark. An attacker who replaces the key, witness, pin, active record, and watermark together may create a coherent-looking old snapshot. This model explicitly demonstrates that counterexample. It must not be interpreted as a security approval.

The model accepts only an adjacent positive generation rotation (N -> N+1). Each snapshot field is a simulated observation, not evidence of a committed write. Its field named `trustedWatermarkGeneration` is **not** independently authenticated by this class.

## Proposed ordering and crash response

| Observed state | Proposed operation boundary | Diagnostic response |
| --- | --- | --- |
| All records at N; no candidate | No enrollment started | UNCHANGED_NOT_AUTHORIZED |
| Candidate N+1 staged; anchors at N | Candidate written and fsynced *if later proven* | STAGED_ABORT_REQUIRES_OWNER_REVIEW |
| Marker at N+1; witness, watermark, active at N | Marker committed | RECOVERY_REQUIRED_NOT_AUTHORIZED |
| Marker and witness at N+1; watermark and active at N | Signed witness published | RECOVERY_REQUIRED_NOT_AUTHORIZED |
| Marker, witness and watermark at N+1; active at N | Trusted watermark advanced *if later proven* | RECOVERY_REQUIRED_NOT_AUTHORIZED |
| All at N+1 | Active pointer switched | STRUCTURALLY_COMPLETE_NOT_AUTHORIZED |
| Skipped step, generation gap, stale or future field | Inconsistent / invalid observation | BLOCKED |

**No automatic resume, rollback, delete, key rotation, key creation or recovery is performed.** Any crash after marker advancement requires explicit owner-visible recovery and independently verified evidence. Even an apparently complete sequence never authorizes key use, memory persistence, or agent execution.

## Required future implementation gates

1. Define a signer-enrollment ceremony with independent, owner-verified public-key fingerprint provenance, protected signing key custody, revocation, and rotation.
2. Implement an independently authenticated, **rollback-resistant** monotonic generation high-watermark with a hardware-backed or separately trusted witness; ordinary app storage and Android Keystore aliases alone do not prove anti-rollback.
3. Specify candidate/marker/witness/watermark/active writes with fsync, atomic rename or equivalent durable primitives, concurrency locks, crash injection at every boundary, and recovery journaling. Prove that an attacker cannot replay all records together.
4. Bind cryptographic witness and reference to actual generation identities, signed enrollment transactions, owner consent and hardware key attestation. Confirm Pixel 9 Pro StrongBox behavior physically.
5. Perform independent security review, spoken TalkBack accessibility validation, and signed reproducible OTA/recovery drills before release acceptance.

## Evidence and exclusions

- 19 synthetic Kotlin JUnit methods cover valid crash windows, skipped writes, gaps, overflow, stale/future generations, null inputs, and the whole-snapshot rollback counterexample.
- CI's JUnit evidence gate requires the exact 19 methods and rejects missing/skipped/failed/duplicate methods.
- A separate Python source gate rejects application-runtime callers and forbidden storage/Keystore APIs.
- These tests do **not** demonstrate actual filesystem durability, a hardware monotonic counter, a genuine signature-provisioning ceremony, owner-authenticated CryptoObject interoperability, or physical Pixel validation.

**Milestone impact:** M6 remains in progress; M5 and M7 remain unaccepted/blocked, M8 blocked. No milestone can be marked complete without independent acceptance.
