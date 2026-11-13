# SEC-023B1B2D9 — Owner-recovery intent binding (offline preflight)

**Status: NOT AUTHORIZING.** This is a pure-JVM, unwired policy test for a future owner-assisted recovery ceremony. It neither provisions signer keys nor creates a rollback-resistant counter, writes a journal, invokes Android credentials, rotates keys, resumes enrollment, enables MemoryVault or executes an agent.

## Threat model and design

The prior SEC-023B1B2D8 policy identifies crash windows in a candidate → marker → witness → watermark → active-pointer sequence. The new preflight accepts **only** the staged-candidate and incomplete-enrollment outcomes. It binds the exact crash snapshot, caller-supplied observed/external signer pins, caller-supplied watermark, owner user ID and 256-bit nonce into a domain-separated SHA-256 intent digest. It reuses the existing 30-second one-shot `OwnerAuthorityConfirmationState` instead of creating another token or timeout engine.

The future owner-facing UI must derive all context from trusted Android and independently authenticated sources. The present `foregroundOwnerUi`, `secureCredentialConfigured`, credential result, externally pinned signer and external watermark are **caller-supplied assertions**, not proofs. Matching two pins cannot establish independent provenance. Matching two counters cannot establish anti-rollback. The intent outcome `OWNER_REVIEW_RECORDED_NOT_AUTHORIZED` is deliberately not a grant, even if a caller reports credential success. Cancellation, replay, process recreation, changed inputs and timeout fail closed.

## Required release/security work

1. Independently authenticated signer-pin enrollment, protected key custody, explicit owner-approved rotation/revocation and recovery; never trust an agent-provided fingerprint.
2. Independently retained, **rollback-resistant** high-watermark or authenticated external witness. Same-host app storage and caller-supplied counters cannot detect full-state replay.
3. Atomic durable journal/write ordering, fsync/rename verification and crash injection on actual Android storage; external independent security review.
4. Genuine owner-facing system credential and CryptoObject proof, physical Pixel 9 Pro StrongBox interoperability, TalkBack spoken validation, and signed OTA/recovery drills.

No source from the Android runtime calls this preflight. No memory persistence or executor wiring changes. The synthetic JVM tests and source checks establish only local policy behavior, not physical Pixel hardware, owner presence or production readiness. M1–M8 acceptance is unchanged.
