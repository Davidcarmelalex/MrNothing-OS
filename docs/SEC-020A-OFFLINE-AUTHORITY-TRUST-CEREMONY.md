# SEC-020A — offline authority trust ceremony policy

**Status:** implemented as a pure JVM policy slice; not a provisioned trust store or production ceremony.

## Scope

SEC-017's host registry verifies enrollment statements against an authority public key supplied by its trusted constructor. The Android app does not yet have a persistent, owner-confirmed way to provision that authority key. SEC-020A adds the deterministic policy boundary for first install, signed rotation and recovery without connecting it to a live enrollment path.

## Candidate and fingerprint

A candidate consists of a bounded canonical Ed25519 SubjectPublicKeyInfo DER public key, a 1–64 character ASCII authority key identifier, and a positive signed-64-bit generation.

The owner-facing fingerprint is SHA256: followed by 64 uppercase hexadecimal characters, calculated over the exact canonical SPKI DER bytes. The fingerprint entered by the owner must come from an independently authenticated out-of-band channel, not from the same file, QR payload or screen that delivered the candidate.

## First-install policy

First install is eligible only when the trusted generation watermark is exactly zero, the candidate generation is exactly one, the key is valid, the out-of-band fingerprint matches in constant time, and the foreground owner confirmation is present. An existing watermark is never treated as an empty store.

## Rotation policy

Rotation requires a valid current record whose stored fingerprint matches its exact SPKI; the hardware-backed generation watermark to equal the current record generation; a different key identifier and different Ed25519 public key; candidate generation exactly current plus one; a 64-byte Ed25519 signature by the current authority over the deterministic, domain-separated, length-prefixed rotation payload; matching out-of-band fingerprint; and explicit owner confirmation.

The payload is binary and deterministic: domain string MRNOTHING-OWNER-AUTHORITY-ROTATION-V1, big-endian 64-bit generation, then length-prefixed ASCII key ID, SPKI DER and canonical fingerprint. It does not depend on JSON field ordering or whitespace.

## Recovery policy

Recovery is not a reset. It is eligible only when the active record is absent or unreadable while a non-zero trusted generation watermark still exists. The candidate must be exactly one generation newer than that watermark, and requires the same out-of-band fingerprint and owner confirmation. Recovery is blocked if a valid active record exists, the watermark is absent, the generation would roll back or skip, or the generation counter is exhausted.

If Android Keystore and the app's encrypted state are both lost (for example after a device reset), the previous watermark cannot be proven. Re-provisioning then requires a fresh owner-controlled first-install ceremony and independent fingerprint confirmation. A future backend must detect the inconsistent case where app data exists but its Keystore marker does not, and fail closed rather than silently treating it as first install.

## Anti-rollback contract for the future store

highestObservedGeneration is an input to this policy, not a value read from app preferences. SEC-020B must provide it from Android Keystore-backed, non-exportable per-generation marker keys and must bind the encrypted active record to the matching generation. The marker must be created before the active record is committed. If a crash leaves a marker ahead of the record, normal load/rotation must fail closed and enter the explicit recovery path. Old markers must not be deleted during ordinary rotation.

This policy code does not implement that backend. It also does not implement a user interface, system-credential prompt, import/export transport, certificate revocation, remote attestation or authority signing key custody.

## Security boundaries

- Pure local policy and JCA cryptographic verification only.
- No network APIs, listeners, external process, shell, accessibility service or screen capture.
- No Android permission grant, owner-consent signing, command admission or executor connection.
- No Android Keystore mutation or persistent write.
- A Ready result is only a validated proposal. It is not proof that the future caller actually committed it atomically or obtained a genuine system credential result.
- The ownerConfirmation argument is a policy signal; a production UI must derive it only from a foreground, owner-visible ceremony and fresh Android system-credential result. It must not be supplied by an agent, model, intent extra or remote peer.

## Tests and acceptance

OwnerAuthorityTrustCeremonyTest uses generated ephemeral JDK Ed25519 keys. It covers fingerprint formatting and mismatch, explicit confirmation, first-install generation, invalid SPKI and key IDs, signed rotation, wrong/tampered signatures, rollback/skipped generations, watermark mismatch, key reuse, invalid current records, recovery eligibility, recovery fingerprint/confirmation, generation exhaustion and deterministic rotation payloads.

These are JVM policy tests, not Android Keystore, StrongBox, physical-device, UI or recovery-drill tests. SEC-020 remains incomplete until SEC-020B supplies the persistent rollback-resistant backend and owner-visible first-install/rotation/recovery UI, and independent security review approves the complete flow.


## Exact-head CI acceptance — 2026-11-05

Source commit: b4b6dad184d48055753bda2087e28292a1a2a008. Phase 1 push/PR, CI-003 push/PR and QA-005 PR workflows all passed: runs 42024219462, 42024226415, 42024219429, 42024226462 and 42024226407. The Phase 1 jobs each ran 380 Python tests and passed Gradle debug unit tests/assembly with strict dependency verification. The CI-003 independent verifier confirmed byte-identical unsigned APKs (SHA-256 972cc506d948a34321351785f51129022be0eb0d7b54ed4ae18b9d53bd8f7993; 2,133,809 bytes; 13 entries), matching normalized APK contents, runtime inventory and SPDX runtime SBOM. QA-005 disposable emulator workflow passed; TalkBack remained disabled and spoken navigation remains unverified.

This acceptance is limited to the SEC-020A pure-JVM policy code. No persistent trust store, UI, Android Keystore marker, StrongBox runtime, physical Pixel, production enrollment or executor was tested. SEC-020 remains incomplete; SEC-020B is the next implementation task.


## Android Ed25519 provider compatibility

API-35 emulator instrumentation exposed that the platform-default Ed25519 KeyFactory selected an AndroidKeyStore-backed implementation that could not import the synthetic external owner SPKI. The ceremony now uses a pinned Bouncy Castle 1.86 provider instance for both Ed25519 KeyFactory import and Signature verification. The provider is passed directly to each JCA lookup and is not registered in the process-wide Security provider list. A known RFC 8032 public-key vector and a provider-registry invariance assertion cover this behavior. The application dependency is checksum-pinned in Gradle verification metadata and its Bouncy Castle license is recorded in `docs/THIRD-PARTY-NOTICES.md`.

This is software-provider compatibility evidence only. It does not make owner keys hardware-backed and does not claim StrongBox protection for the imported public key.
