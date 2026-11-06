# SEC-020B6 — Android Keystore fail-closed negative-path verification

**Status:** implementation and emulator instrumentation added; exact-head CI acceptance pending.

## Scope

This slice tests AndroidKeyStore behavior that can be observed without claiming StrongBox hardware. It does not enroll an owner, create a production authority, grant permissions, change trust transitions or connect the agent executor.

AndroidAuthorityTrustCrypto now accepts an internal alias namespace with the original production aliases as defaults. The production AndroidOwnerAuthorityTrustStore continues to construct it with no arguments. Instrumentation supplies a unique UUID-scoped test namespace and removes only aliases created under that namespace in a finally block.

## Instrumentation cases

1. A StrongBox-required marker request fails without creating a TEE marker when the emulator does not advertise FEATURE_STRONGBOX_KEYSTORE. If a test device advertises StrongBox, the test instead requires a marker whose KeyInfo.securityLevel is exactly STRONGBOX and verifies its proof.
2. A missing marker alias cannot verify a marker proof.
3. A malformed marker suffix makes trust-store inspection unavailable.
4. A non-canonical decimal generation suffix (for example 01) makes inspection unavailable.
5. A zero generation marker makes inspection unavailable.
6. A TEE/software-only HMAC marker cannot become the generation watermark.
7. An AES encryption alias without any generation marker is an inconsistent state, not a fresh install.
8. A non-secret key under the marker prefix is rejected.

The tests use only disposable, unique AndroidKeyStore aliases and a missing-record persistence fixture. They clean their own aliases and never enumerate/delete production aliases.

## Security invariants

- Marker HMAC and AES-GCM production keys continue to request setIsStrongBoxBacked(true).
- KeyInfo.securityLevel must equal SECURITY_LEVEL_STRONGBOX; hardware-backed TEE is insufficient.
- Malformed, non-canonical, non-positive, wrong-type or non-StrongBox marker state must not become a valid generation watermark.
- An AES alias without a generation marker must not be classified as a fresh install.
- Missing marker proofs fail verification.
- Production aliases remain mrnothing_authority_marker_v1_ and mrnothing_authority_record_aes_v1.

## Evidence boundary and remaining gaps

An API 35 emulator without the StrongBox feature can verify refusal and absence of a TEE fallback; it cannot prove a real StrongBox implementation. If the emulator advertises StrongBox, the test verifies the returned key metadata, but a Pixel 9 Pro M7 hardware run remains separately required.

This slice does not inject a failing KeyInfo provider, simulate Keystore daemon death, verify loss of the AES key while a valid StrongBox marker remains, or test physical Keystore persistence across reboot/reset. Those remain separate failure-injection and hardware gates.

No production key is created or deleted by the instrumentation tests. No root, device flashing, credential bypass, permission grant, production signing or deployment is involved.

## Acceptance

- Phase 1 push/PR Python, Kotlin/JUnit, Android assembly, strict dependency verification and manifest checks pass.
- CI-003 push/PR independent unsigned build, manifest, SBOM and provenance checks pass.
- QA-005 API 35 emulator instrumentation passes all SEC-020B4D, SEC-020B5 and SEC-020B6 cases and confirms test-alias cleanup.
- Independent security review remains mandatory.
- Physical Pixel 9 Pro StrongBox and recovery validation remain M7 gates.

Release state remains release_ready=false; unsigned artifacts are not for release.
