# CI-006 — scoped build-environment SBOM and toolchain inventory

**Status:** Implemented on `feat/phase1-agentic-phone`; exact-head GitHub validation is required before acceptance.

## Purpose

CI-003 already emits an SPDX-2.3 SBOM for the Android `releaseRuntimeClasspath` and records a small set of top-level toolchain fields in provenance. That runtime SBOM is intentionally not a build-environment inventory. CI-006 adds a separate, deterministic inventory and SPDX-2.3 document for the build environment actually observed by each independent CI-003 builder.

## Captured scope

The inventory includes:

- Installed Debian/Ubuntu packages and versions from `dpkg-query`.
- Installed Python packages and versions from `pip list --format=json`.
- Installed Android SDK packages and revisions from `sdkmanager --list_installed`, with SHA-256 fingerprints of available package `source.properties` files.
- The downloaded Gradle distribution version and SHA-256, checked against the workflow's pinned digest.
- Actual JDK vendor/runtime properties and Python runtime version.
- Android Gradle Plugin and Kotlin Gradle plugin versions read from the checked-in Gradle declarations.
- Compile SDK and workflow-pinned Android platform/build-tools packages.
- GitHub Actions repository references, each required to use a full 40-character commit SHA.
- GitHub-hosted runner image identity (`ImageOS`, `ImageVersion`) and `/etc/os-release`.

The SPDX package list is generated deterministically from the canonical JSON inventory. The inventory digest is included in the SPDX document namespace. Provenance v2 receives a `build_environment_sbom` object containing the inventory and SPDX filenames, SHA-256 digests and scope statement.

## Independent-runner acceptance

Both CI-003 builders generate and attach their own inventory and SBOM. The independent verifier:

1. Validates each inventory schema and source commit.
2. Validates the SPDX-2.3 document namespace against the exact inventory digest.
3. Checks SPDX package URLs and any declared SHA-256 values against the inventory.
4. Checks the inventory/SBOM hashes against provenance.
5. Requires byte-identical inventory and SBOM files across runner A and runner B.
6. Requires identical runner-image identity and direct toolchain metadata.
7. Emits `build-environment-verification.json` in the independent-verifier artifact.

A negative-control command rewrites a temporary copy of the workflow with a mutable action tag and proves that the action-pin parser rejects it. The real workflow is never modified by the negative control.

## Explicit limitations

This is a **scoped build-environment SBOM**, not a claim of a complete hosted-runner image SBOM. It does not enumerate every GitHub toolcache file, every transitive Gradle plugin-resolution dependency, all downloaded network resources, or every file in each Android SDK package. The runtime SBOM remains a separate document. A matching pair of inventories proves equivalence for the recorded CI runner/toolchain inputs, not universal reproducibility or artifact authenticity.

The release remains unsigned and `release_ready=false`. No signing key, production deployment, device flashing or physical-device operation is involved.

## Acceptance gates

- The Phase 1 Python-policy and Android jobs pass on push and PR.
- Both CI-003 builders produce valid inventory and SPDX documents.
- The Gradle distribution digest matches the checked-in workflow pin.
- Required SDK packages and actual JDK/Python/Gradle/plugin versions are captured.
- Every CI-003 GitHub Action is pinned to a full commit SHA.
- The mutable-action negative control is rejected.
- Provenance links match both inventory/SBOM digests.
- The independent-runner verifier passes exact-byte comparisons.
- A separate independent security review remains required; CI success is not self-approval.


## CI-006A — canonical SPDX integrity validation

The verifier now validates inventory component identity fields, lowercase SHA-256 values, unique package URLs, canonical component ordering and exact per-kind counts. It then regenerates the expected SPDX-2.3 document from the digest-bound inventory and requires full object equality.

This closes ambiguity that a package-URL set comparison alone would permit: duplicate SPDX package records, changed package names or versions, ungrounded checksums, altered SPDX identifiers, missing or extra relationships, and modified document metadata now fail validation. The CI-006 schema remains intentionally strict; an intentional SPDX shape change must update the generator, validator and tests together.

Five adversarial regression tests cover duplicate SPDX package records, package metadata tampering, relationship-graph tampering, duplicate inventory package URLs and inconsistent component counts. Exact-head Phase 1 and CI-003 push/PR validation remains required; this is not independent security approval or a complete hosted-runner SBOM.
