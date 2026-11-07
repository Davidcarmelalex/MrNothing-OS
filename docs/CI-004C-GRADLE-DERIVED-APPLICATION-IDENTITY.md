# CI-004C — Gradle-derived release application identity

**Status:** implementation submitted on `feat/phase1-agentic-phone`; exact-head Phase 1 and CI-003 workflows are the acceptance gates.

## Objective

Remove the duplicated hard-coded application ID from CI-003. The expected release identity must come from the actual Android Gradle Plugin release variant, then be used consistently for the merged manifest, packaged APK manifest and release provenance.

## Implementation

- AGP 8.7.3 Android Components API selects the release build variant and reads its resolved `variant.applicationId` provider.
- `:app:writeReleaseVariantMetadata` emits deterministic `release-variant-metadata.json` under `app/build/reports/ci003`.
- The Gradle task requires exactly one unflavored `release` variant. Adding flavors or multiple release variants requires an explicit policy update rather than silently choosing one.
- A shared strict metadata reader rejects symlinks, missing/non-regular files, files over 16 KiB, invalid JSON, duplicate keys, unknown/missing fields, invalid package identifiers and non-release variant metadata.
- CI-004B consumes `--variant-metadata`; it validates both the Gradle-merged and packaged APK manifest package IDs against the Gradle-derived application ID. No literal application ID remains in the workflow invocation.
- CI-003 provenance advances to schema v2 and records application ID, variant name, build type and metadata SHA-256.
- Both independent builders package the metadata and include it in SHA256SUMS. The verifier checks the metadata against its own provenance and requires exact metadata/provenance equality across runners.

## Negative controls

- Gradle metadata with a different application ID is rejected against both manifest forms.
- A debug/non-release variant is rejected.
- An invalid application ID is rejected.
- Duplicate JSON keys are rejected.
- Metadata changed after provenance generation is rejected.
- Workflow tests require the Gradle task, metadata-driven gate invocation, provenance input, artifact inclusion and cross-runner comparison.

## Limitations

This verifies build-variant identity consistency; it does not prove runtime package behavior, inspect DEX/native capabilities, sign the APK, validate Android Keystore/StrongBox, exercise a Pixel 9 Pro or establish OTA/recovery/production readiness. Independent security review remains required.
