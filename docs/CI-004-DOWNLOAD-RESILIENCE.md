# CI-004 — pinned build-tool download resilience

**Status:** Implemented on `feat/phase1-agentic-phone`; exact-head CI re-acceptance pending.

## Triggering evidence

At branch head `1de4c02404ca3adce9052afbb5d282d6cfa9edb8`, the Python policy suite and QA-005 emulator workflow passed, but Android build and CI-003 jobs were blocked before completing build verification:

- Phase 1 PR run [42468185605](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42468185605), latest rerun attempt 7: Gradle 8.9 download returned repeated HTTP 504 responses.
- Phase 1 push run [42468182494](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42468182494), rerun attempt 2: Kotlin compiler artifact resolution returned HTTP 504.
- CI-003 PR run [42468185426](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42468185426), rerun attempt 7: Temurin 17.0.13+11 setup and Gradle distribution downloads returned HTTP 504.
- CI-003 push run [42468182534](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42468182534), rerun attempt 2: both independent builders failed while downloading Gradle 8.9 with HTTP 504.

The failed steps were dependency/tool downloads, not test assertion failures. Rerunning failed jobs did not clear the dependency-host failures.

## Pinned acquisition policy

- Phase 1, CI-003 and QA-005 now pin Eclipse Temurin **17.0.21+9**, the exact Temurin build already observed in the Phase 1 Ubuntu 24.04 hosted-runner toolcache.
- All three Android workflows call one shared `scripts/download_gradle_distribution.sh` helper for Gradle **8.9**.
- The helper accepts only the pinned version and hard-coded SHA-256 `d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab`.
- It tries only Gradle-operated HTTPS distribution endpoints: `services.gradle.org` and `downloads.gradle.org`. Gradle documents these endpoints at [Decommissioning HTTP for Gradle Services](https://blog.gradle.org/decommissioning-http).
- Each endpoint uses bounded connect/transfer timeouts and retry handling for transient network errors.
- Redirects are restricted to HTTPS and TLS 1.2 or later.
- A checksum mismatch is a hard failure. The helper does not extract or publish an unverified archive and does not fall through after a checksum mismatch.
- The verified archive is stored under `~/.gradle/distributions` and included in the Gradle cache. Existing cache entries are checksum-verified before reuse; symlinks, non-regular files and mismatched cached archives fail closed.
- `actions/setup-java` caches Gradle dependency and distribution paths in all three Android workflows. Pull-request runs are read-only cache consumers; push and manual-dispatch runs may populate the cache.
- The verified archive is moved atomically into the requested destination. Community mirrors, caller-supplied URLs, disabled TLS verification and dynamic Gradle versions are not accepted.

## Static regression gates

The CI-003 workflow gate now checks:
1. Both workflows use the same pinned downloader.
2. Both Android jobs pin the same exact Temurin build.
3. The downloader contains only the allowlisted official HTTPS endpoints.
4. The expected SHA-256 is checked before the archive is moved into place.
5. Unsupported Gradle versions are rejected before any network request.
6. A simulated transport failure attempts each official endpoint and no untrusted host.
7. QA-005 uses the same pinned JDK, verified Gradle downloader and cache paths; it contains no independent single-host Gradle download.

## Acceptance still required

At the new exact head, require:
- Phase 1 push and PR: Python suite, Android unit tests, debug assembly, repeat-build byte identity, strict dependency verification and negative control all pass.
- CI-003 push and PR: both independent builders and the cross-runner verifier pass; APK, normalized contents, runtime SBOM, toolchain and scoped build-environment inventory match.
- QA-005 exact-head disposable-emulator workflow passes.
- Any HTTP 504 or checksum mismatch remains a failed gate; no previous-head result substitutes for exact-head evidence.

## Limits

This change improves dependency acquisition reliability; it does not establish build success until the new exact-head workflows complete. It does not alter Android application code, permissions, enrollment, consent, device execution, OTA or release signing. CI-003 artifacts remain unsigned engineering artifacts with `release_ready=false`. Independent security review remains pending.


## Kotlin plugin dependency fallback

The exact-head build logs showed a second independent 504 boundary: `kotlin-compiler-embeddable:2.0.21` was requested from Maven Central and redirected to the JetBrains GitHub release asset, which returned HTTP 504. The Android settings preserve the original Maven Central-before-Gradle-Plugin-Portal precedence (required by the existing dependency-verification metadata) and add Sonatype's canonical Maven Central endpoint `https://repo1.maven.org/maven2/` after `mavenCentral()` in both plugin and application dependency resolution. Sonatype documents repo1 as a canonical HTTPS Central endpoint: [Consume Central](https://central.sonatype.org/consume/). Existing Gradle dependency verification remains enabled, so artifact checksums are still enforced.

This is a repository-order fallback, not a guarantee that the upstream network will be available. Exact-head Gradle builds must prove it.


### Repository-order correction

The first exact-head attempt with Gradle Plugin Portal ahead of Maven Central failed the strict dependency-verification gate for the Kotlin plugin marker POM. The original repository precedence has been restored; the Sonatype repo1 endpoint is now an additional fallback after Maven Central. Dependency verification remains enabled and no checksum was weakened or regenerated from the failing run.


## QA-005 emulator build-tool parity

The emulator workflow previously used an unpinned Java 17 selector and a separate direct download from only `services.gradle.org`. It now uses the same exact Temurin 17.0.21+9 build, Gradle cache paths and checksum-verifying downloader as Phase 1 and CI-003. Pull-request runs remain read-only cache consumers. The emulator creation, instrumentation, synthetic test-credential cleanup and diagnostics steps are unchanged.

This closes a CI configuration drift; it does not guarantee a cache hit or eliminate upstream HTTP 504 responses on cache misses. Exact-head Phase 1, CI-003 and QA-005 workflows remain the acceptance evidence. No dependency checksum was changed or bypassed.
