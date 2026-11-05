# CI-004 — Gradle-merged release manifest security gate

**Status:** implementation submitted on feat/phase1-agentic-phone; exact-head CI is the acceptance gate.

## Why this gate exists

The existing Phase 1 source-manifest gate inspects the checked-in main manifest. The debug-probe regression checks inspect source manifests. Neither proves what the Android Gradle Plugin actually merged into the release variant. CI-003 already builds the unsigned release APK on two independent runners, so the merged release manifest can be checked at that point without adding a new workflow or changing application behavior.

## Implemented checks

scripts/release_manifest_gate.py searches the Gradle intermediates for the release merged manifest and fails closed if the expected output is missing or ambiguous. It prefers the single processReleaseMainManifest result when AGP exposes multiple release manifest intermediates.

The policy verifies:

- exactly one application;
- allowBackup=false and usesCleartextTraffic=false;
- no debuggable=true, testOnly=true, or requestLegacyExternalStorage=true;
- only the explicitly reviewed USE_BIOMETRIC permission, with no duplicate permission;
- no shared UID or instrumentation declaration;
- exactly one exported MainActivity with both MAIN/HOME/DEFAULT and MAIN/LAUNCHER intent filters;
- every non-Home component has explicit exported=false and no intent filter;
- the debug credential prompt Activity and cancellation receiver do not leak into release.

The gate writes deterministic JSON containing the selected manifest path, SHA-256, individual check results and any policy findings. CI-003 runs it on both independent build runners, uploads the report with the unsigned APK/SBOM/provenance bundle, and byte-compares the two reports.

## Tests

tests/test_release_manifest_gate.py covers the accepted baseline and negative controls for debug-probe leakage, unreviewed/duplicate permissions, exported or implicit-export components, non-Home intent filters, missing HOME/LAUNCHER filters, backup, cleartext, debug/test-only flags, shared UID, instrumentation, missing output and ambiguous output. A workflow regression asserts that CI-003 runs the gate after release assembly and compares the reports.

The test module is included automatically by scripts/phase1-preflight.sh unittest discovery.

## Limitations

This is a build-time merged-manifest policy check. It does not prove runtime absence of reflective/transitive capabilities, does not replace decoding the final binary manifest from the APK, and does not validate physical-device behavior. The release APK remains unsigned and release_ready=false. Independent security review remains pending.
