# SEC-023B1B2D3 — Cancellation fence for dormant MemoryVault Cipher probe

**Status:** DRAFT; independent security approval PENDING. Stacked on PR #22 / #21, targeting `feat/phase1-agentic-phone`. Upstream shared `SKILL.md` remains unverified; the repository's `PROJECT-ADAPTER.md` is project-specific.

## Security property and implementation

Previously `MemoryVaultAuthenticatedCipherProbe.complete()` held its object monitor while running potentially blocking `Cipher.doFinal()`. A concurrent `revoke()` could not acquire the monitor until after the method returned, allowing an in-flight probe to report success before a waiting cancellation was processed.

The revised method atomically consumes its pending Cipher/digest under the object monitor, then releases that monitor before callback inspection and cryptographic work. A separate pure-JVM one-shot `MemoryVaultCompletionCancellationFence` linearizes `begin`, `revoke` and `finish`. A revocation that **linearizes before finish** forces the probe result to `BLOCKED`, even if `doFinal()` later succeeds. It is not possible to retroactively cancel a result whose finish already linearized; the result remains diagnostic only and never grants storage authorization. The fence is in-memory only and cannot be reconstructed across process death. Repeated calls are blocked.

## Evidence and limitations

`MemoryVaultCompletionCancellationFenceTest` adds eight pure-JVM tests: finish-without-begin, single-use, pre-begin revocation, in-flight revocation, repeated revocation, process recreation, deterministic cross-thread cancellation while a worker is suspended, and finish-before-revoke ordering. These are **not** actual AndroidKeyStore, hardware, IPC, owner credential or physical Pixel 9 Pro tests. Hosted Gradle/JUnit execution and exact-head CI must be recorded separately. Local Kotlin compilation with Android stubs and a 14-assertion standalone smoke run do not establish an Android build.

**Open critical gates:** same-key-generation continuity across alias replacement (metadata alone cannot prove it), real owner-consent Activity and cancellation lifecycle, genuine per-use device-credential CryptoObject interoperability, key invalidation, StrongBox provenance on consented Pixel 9 Pro hardware, spoken TalkBack, independent security review, and signed OTA/recovery. Keep MemoryVaultService disabled and non-exported, PaperClip memory RAM-only, Android executor disconnected. No permissions, keys, storage or production integrations are enabled by this patch.

**Milestones:** M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7/M8 BLOCKED. None independently accepted.
