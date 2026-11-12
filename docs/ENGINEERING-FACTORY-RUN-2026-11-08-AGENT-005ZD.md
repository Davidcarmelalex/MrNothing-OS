# Engineering Factory Run AGENT-005ZD — CI-006 checksum binding

**Date:** 2026-11-08  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Audit head:** `4feef32563d5a9877350120cfeb4b8a50ad41ce1`  
**Task:** Correct the CI-006 build-environment inventory parser after CI-004 moved Gradle acquisition into the shared checksum-verifying downloader.

## Finding

At the AGENT-005ZC head, Phase 1 push passed with 787 Python tests and the Android debug build/unit/repeat-build/dependency-negative-control gates. CI-003 builders also completed the release Gradle build, release merged/packaged manifest gates and the CI-005 dependency-verification negative control. Both then failed during build-environment SBOM generation because `scripts/build_environment_sbom.py` still searched the workflow for the old inline ZIP checksum command.

CI-004 had intentionally replaced that inline command with `scripts/download_gradle_distribution.sh`. The workflow still carries the pinned digest in its `--gradle-sha256` provenance argument, but CI-006 had not been updated to read it.

## Implementation

1. `scripts/build_environment_sbom.py`: parse the explicit `--gradle-sha256` provenance pin instead of the removed inline `echo | sha256sum` command.
2. `tests/test_build_environment_sbom.py`: update the fixture to use the provenance argument and add a missing-digest rejection regression.
3. `tests/test_ci003_workflow_gate.py`: require the provenance digest to match the shared downloader's pinned SHA-256.
4. `docs/CI-006-BUILD-ENVIRONMENT-SBOM.md`: document the shared-downloader/provenance binding.
5. `docs/ENGINEERING-FACTORY-ROADMAP.md`: record audit evidence and next gate.

The inventory still computes SHA-256 over the actual Gradle ZIP and rejects mismatches. No checksum, dependency-verification metadata, mirror policy or security gate was weakened.

## Verification

The new Python regression tests and exact-head Phase 1/CI-003/QA-005 workflows are the acceptance gate. No new-head pass is claimed at commit creation.

## Safety

No Android application source, permissions, consent, enrollment, executor, shell bridge, network listener, OTA, signing key or device behavior changed. No physical Pixel 9 Pro was tested. No merge to main, force-push or production operation occurred. Independent security approval remains pending; the real executor stays disconnected.
