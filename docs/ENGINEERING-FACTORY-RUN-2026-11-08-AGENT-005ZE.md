# Engineering Factory Run AGENT-005ZE — CI-006 archive-path correction

**Date:** 2026-11-08  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Branch:** `feat/phase1-agentic-phone`  
**Audit head:** `71d2cdd59b528c60454df3aa7c8bb9a1d3e4fd2a`

## Finding

After AGENT-005ZD corrected the CI-006 parser to read the workflow's `--gradle-sha256` provenance pin, both CI-003 builders progressed through release Gradle tests/build, merged and packaged release-manifest security gates, and the dependency-verification negative control. They then failed because the inventory command still pointed to `$RUNNER_TEMP/gradle-8.9-bin.zip`, which the shared downloader does not create.

The verified ZIP is retained at `$HOME/.gradle/distributions/gradle-8.9-bin.zip`; the workflow extracts it to RUNNER_TEMP but does not copy the ZIP.

## Implementation

- Change CI-003 `--gradle-zip` to the verified cached archive path.
- Add a static gate that requires this path and rejects the nonexistent RUNNER_TEMP ZIP path.
- Document the path and checksum contract in CI-006.
- Record this bounded correction in the roadmap.

The generator continues to hash the actual archive and compare it to the explicit provenance digest. No checksum or security gate is weakened.

## Prior-head evidence

At head `71d2cdd`, Phase 1 push passed with 789 Python tests and Android debug build/unit/repeat-build/dependency-negative-control checks. CI-003 failed only during build-environment inventory generation after its release build and manifest/dependency gates had passed. Exact-head reruns after this commit are required; no new-head pass is claimed here.

## Safety

No Android app source, permission, consent, enrollment, executor, shell bridge, OTA, signing key or physical device was changed. No merge to main or force-push occurred. Independent security review remains pending and the real executor remains disconnected.
