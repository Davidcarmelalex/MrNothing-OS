# CI-003 — independent-runner unsigned Android reproducibility

**Status:** Implemented in the feature branch; acceptance is pending exact-head GitHub Actions evidence.

## Purpose

The SEC-019B debug APK hashes differed between independent GitHub runners. The prior workflow only compared repeat builds within one runner and used a per-run debug signing identity. CI-003 creates an explicitly unsigned release variant and compares two independently provisioned GitHub-hosted runner jobs.

## Build contract

- Runner image label: ubuntu-24.04.
- JDK: Eclipse Temurin 17.0.13+11.
- Gradle: 8.9 binary distribution, SHA-256 d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab.
- Android Gradle Plugin: 8.7.3.
- Kotlin Gradle plugin: 2.0.21.
- Android platform: android-35.
- Android build tools: 35.0.0.
- The release build type has no signing configuration and CI rejects v1 signing entries and the APK Signature Scheme v2/v3 signing block.
- Release unit tests, unsigned release assembly and a resolved releaseRuntimeClasspath inventory run on both builders.
- The two APKs must be byte-identical. A normalized ZIP-entry comparison is also retained to distinguish payload differences from container metadata variance.
- Build provenance is deterministic from the source commit timestamp and records the actual JDK/SDK manager versions plus pinned top-level toolchain inputs.

## SBOM scope

The generated SPDX-2.3 SBOM inventories resolved Android releaseRuntimeClasspath artifacts, including each artifact SHA-256 and Maven package URL. Build plugins, Gradle internals, SDK packages and operating-system packages are not application runtime dependencies; they are recorded in build provenance and are explicitly outside this runtime SBOM. This is not a complete build-environment SBOM or a signed attestation.

## Acceptance

1. Both independent builders compile and pass :app:testReleaseUnitTest.
2. Both produce an unsigned app-release-unsigned.apk.
3. APK ZIP structure is valid, has no duplicate/unsafe/encrypted/symlink entries, and has no APK signing block or v1 signature files.
4. Whole-file SHA-256 and normalized entry-content digests match across runners.
5. Runtime inventory, SPDX SBOM and recorded toolchain inputs match byte-for-byte.
6. Provenance confirms the same source commit and marks release_ready=false and provenance_signed=false.
7. Independent supervisor review remains a separate gate.

## Safety and limitations

- No production signing key is generated, stored or used.
- The unsigned APK is a CI engineering artifact, not an installable release and not for distribution.
- GitHub Actions major-version tags remain mutable; dependency verification metadata and immutable action pinning remain future hardening.
- A matching pair of GitHub-hosted runners is evidence for this exact source/toolchain/run, not proof that every future host or environment is reproducible.
- No emulator, physical Pixel 9 Pro, OTA, firmware or production deployment is performed by CI-003.
- A successful CI-003 result does not complete M1 or M8 without independent approval and the remaining milestone gates.
