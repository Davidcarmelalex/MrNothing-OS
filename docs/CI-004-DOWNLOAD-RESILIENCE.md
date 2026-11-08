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

- Both Phase 1 and CI-003 now pin Eclipse Temurin **17.0.21+9**, the exact Temurin build already observed in the Phase 1 Ubuntu 24.04 hosted-runner toolcache.
- Both workflows call one shared `scripts/download_gradle_distribution.sh` helper for Gradle **8.9**.
- The helper accepts only the pinned version and hard-coded SHA-256 `d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab`.
- It tries only Gradle-operated HTTPS distribution endpoints: `services.gradle.org`, `downloads.gradle.org`, and `downloads.gradle-dn.com`. Gradle documents these endpoints at [Decommissioning HTTP for Gradle Services](https://blog.gradle.org/decommissioning-http).
- Each endpoint uses bounded connect/transfer timeouts and retry handling for transient network errors.
- Redirects are restricted to HTTPS and TLS 1.2 or later.
- A checksum mismatch is a hard failure. The helper does not extract or publish an unverified archive and does not fall through after a checksum mismatch.
- The verified archive is moved atomically into the requested destination. Community mirrors, caller-supplied URLs, disabled TLS verification and dynamic Gradle versions are not accepted.

## Static regression gates

The CI-003 workflow gate now checks:
1. Both workflows use the same pinned downloader.
2. Both Android jobs pin the same exact Temurin build.
3. The downloader contains only the allowlisted official HTTPS endpoints.
4. The expected SHA-256 is checked before the archive is moved into place.
5. Unsupported Gradle versions are rejected before any network request.
6. A simulated transport failure attempts each official endpoint and no untrusted host.

## Acceptance still required

At the new exact head, require:
- Phase 1 push and PR: Python suite, Android unit tests, debug assembly, repeat-build byte identity, strict dependency verification and negative control all pass.
- CI-003 push and PR: both independent builders and the cross-runner verifier pass; APK, normalized contents, runtime SBOM, toolchain and scoped build-environment inventory match.
- QA-005 exact-head disposable-emulator workflow passes.
- Any HTTP 504 or checksum mismatch remains a failed gate; no previous-head result substitutes for exact-head evidence.

## Limits

This change improves dependency acquisition reliability; it does not establish build success until the new exact-head workflows complete. It does not alter Android application code, permissions, enrollment, consent, device execution, OTA or release signing. CI-003 artifacts remain unsigned engineering artifacts with `release_ready=false`. Independent security review remains pending.
