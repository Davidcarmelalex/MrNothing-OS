# CI-004B — Packaged APK binary manifest verification

**Status:** implementation submitted on feat/phase1-agentic-phone; exact-head Phase 1 and CI-003 runs are the acceptance gates.

## Objective

CI-004 verifies the Gradle-merged release manifest before packaging. CI-004B independently decodes the final unsigned APK's binary AndroidManifest.xml with the Android SDK apkanalyzer manifest print command and compares security-relevant semantics against the Gradle-merged XML.

The decoder is supplied by the installed Android SDK Command-Line Tools package. CI records its Pkg.Revision; the Android SDK Build Tools and Gradle versions remain pinned by CI-003.

## Implemented checks

- Decode the manifest from app-release-unsigned.apk, not from a source or intermediate XML path.
- Require the packaged manifest to be valid XML and to declare the expected tech.mrnothing.os application ID.
- Re-run the existing fail-closed release-manifest policy against both merged and packaged manifests.
- Compare a deterministic security projection covering package identity, root security attributes, SDK bounds, permission declarations, custom permission declarations, instrumentation, package-visibility queries, application security attributes, component export/permission/process attributes, intent filters and provider access rules.
- Normalize relative component class names against the expected application ID so .MainActivity and its fully qualified equivalent compare consistently.
- Ignore presentation-only labels, icons and themes; they do not grant capabilities or alter component exposure.
- Emit raw XML SHA-256 and canonical policy-projection SHA-256 for both manifests, plus explicit policy/match booleans and mismatched section names.
- Upload the packaged-manifest report in each independent CI-003 artifact bundle, include it in SHA256SUMS.txt, and byte-compare the two reports in the independent-runner verifier.

The raw decoded manifest is not uploaded; the report contains hashes and policy outcomes only.

## Fail-closed behavior

Missing/symlinked/oversized/invalid manifest files, a missing packaged package identifier, an application ID mismatch, a policy violation or any security-projection mismatch fails the build. The decoder is invoked with a fixed path and fixed APK input; no arbitrary command is accepted by the Python gate.

The existing CI-004 gate is also tightened to reject unsupported future uses-permission-* declaration forms rather than silently skipping them.

## Tests

The new Python suite covers identical manifests, relative class-name normalization, presentation-only differences, unreviewed permissions, exported component injection, intent-filter changes, cleartext policy changes, package mismatch/missing package, malformed XML, deterministic reports and workflow ordering. The existing CI-004 tests add an unknown permission-tag negative control.

## Limitations

This proves consistency between the Gradle-merged XML and the manifest decoded from the unsigned APK by the recorded SDK decoder. It does not inspect DEX/native code for runtime capability use, validate Android runtime permission behavior, prove hardware-backed key properties, test a Pixel 9 Pro, sign the APK or establish OTA/recovery/production readiness. Independent security review remains required.
