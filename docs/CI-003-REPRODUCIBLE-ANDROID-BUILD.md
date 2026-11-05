# CI-003 — independent-runner unsigned Android reproducibility

**Status:** CI-003 exact-head acceptance passed on 2026-11-05.

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


## Exact-head CI-003 acceptance — 2026-11-05

Verified source commit: 43e0e0f5f86718fd1c3265364c71bed8547b8a7c.

Both independent-runner workflows passed, including their third-job verifier:
- Push CI-003 run 42014136696 — success.
- PR CI-003 run 42014145465 — success.

Each workflow completed both isolated builders and the independent verifier. Both builders passed Gradle 8.9 checksum verification, release unit tests, unsigned release assembly, resolved runtime inventory, SPDX-2.3 SBOM generation and unsigned build provenance.

Cross-runner evidence:
- Unsigned APK SHA-256 on both builders: 4a79cd0be8e6001bae9246eb2b4e6b45ebdaaece79a068bde95ab64d0ba7a4b9.
- APK size: 2,118,361 bytes; 13 ZIP entries.
- Normalized ZIP-entry content SHA-256: ad274b70c474a120a7524b4c093e1b57af4cd353ba2ad00e57916f4baf04e8e8.
- SPDX-2.3 runtime SBOM SHA-256: af5311a96e363ac57fe939777c1b42b7ad25414cacf4c84eedfc688f8859644f; three packages (application plus two resolved runtime artifacts).
- Resolved runtime inventory SHA-256: a8a1b16dd1cefb90d14426c477e924a3710c7a160def52a2ece3a6d55c266e44.
- Matching toolchain: ubuntu-24.04, Temurin/OpenJDK 17.0.13, sdkmanager package revision 12.0, Gradle 8.9 with the pinned distribution SHA-256, AGP 8.7.3, Kotlin 2.0.21, Android platform 35 and build-tools 35.0.0.
- Verifier reported byte-identical APKs, identical normalized contents, runtime inventory, SBOM, toolchain and source commit.

The verifier report explicitly retains release_ready=false and provenance_signed=false. This establishes reproducibility for this unsigned artifact and recorded runner/toolchain pair only. It does not establish a signed release, complete build-environment SBOM, immutable GitHub Action pinning, physical-device compatibility or production readiness.


## Exact-head revalidation — 2026-11-05

The later documentation-only source commit `d5eaf80e39571e0aeaef6013c0af049151e1f77b` was independently revalidated:
- Phase 1 push run 42014876703 and PR run 42014883122 — success.
- CI-003 push run 42014876770 and PR run 42014883313 — success; runner-a, runner-b and independent verifier jobs all succeeded.
- QA-005 disposable x86_64 emulator PR run 42014883226 — success.

For the PR CI-003 run, both independent builders produced the same unsigned APK SHA-256 `4a79cd0be8e6001bae9246eb2b4e6b45ebdaaece79a068bde95ab64d0ba7a4b9` (2,118,361 bytes, 13 ZIP entries), normalized entry digest `ad274b70c474a120a7524b4c093e1b57af4cd353ba2ad00e57916f4baf04e8e8`, SPDX-2.3 runtime SBOM SHA-256 `bae5331ef29e8e6df321e85763b70c76d2d57f47be705b6da258b896b98913e2`, and runtime inventory SHA-256 `a8a1b16dd1cefb90d14426c477e924a3710c7a160def52a2ece3a6d55c266e44`. The verifier confirmed matching toolchain and source commit `d5eaf80...`.

The Phase 1 Python job ran 370 tests successfully. QA-011 remained a read-only preflight and reported the TalkBack service disabled; QA-012 was structural semantics only and did not test spoken TalkBack. The emulator workflow success is not physical Pixel evidence.

CI-003 acceptance is verified for this exact unsigned artifact and recorded GitHub-hosted runner/toolchain pair. It does not make the artifact installable, signed, release-ready or production-ready.
