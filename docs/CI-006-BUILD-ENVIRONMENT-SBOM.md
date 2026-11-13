# CI-006 — scoped build-environment SBOM and toolchain inventory

**Status:** Implemented on `feat/phase1-agentic-phone`; exact-head GitHub validation is required before acceptance.

## Purpose

CI-003 already emits an SPDX-2.3 SBOM for the Android `releaseRuntimeClasspath` and records a small set of top-level toolchain fields in provenance. That runtime SBOM is intentionally not a build-environment inventory. CI-006 adds a separate, deterministic inventory and SPDX-2.3 document for the build environment actually observed by each independent CI-003 builder.

## Captured scope

The inventory includes:

- Installed Debian/Ubuntu packages and versions from `dpkg-query`.
- Installed Python packages and versions from `pip list --format=json`.
- Installed Android SDK packages and revisions from `sdkmanager --list_installed`, with SHA-256 fingerprints of available package `source.properties` files.
- The downloaded Gradle distribution version and SHA-256, checked against the workflow's `--gradle-sha256` provenance pin. A static regression gate requires that value to match the shared downloader's allowlisted version/hash.
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
- The Gradle distribution digest matches the checked-in provenance pin, and the static gate proves it matches the shared checksum-verifying downloader.
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


### CI-006A fixture correction

The first submitted CI-006A commit over-escaped the Python date-regex and JSON fixture newline literals while generating the patch. The follow-up corrects the date regex to match the canonical UTC timestamp and writes real newline terminators in all five adversarial fixtures. No generator, inventory schema, workflow or Android runtime behavior changed. The corrected exact-head Phase 1/CI-003 runs are the acceptance evidence.


### CI-006A assertion correction

The first exact-head CI-006A run executed 495 tests and exposed one stale assertion message in the existing tampered-inventory test. The canonical SPDX validator rejected the modified inventory before the old namespace/hash-specific assertion text, so the implementation failed closed but the test expected only the previous wording. The assertion now accepts the new canonical-document rejection message as well. No production code or policy was weakened.


### CI-006B — shared Gradle downloader checksum binding

CI-004 replaced the inline Gradle ZIP `curl`/checksum command with the shared `scripts/download_gradle_distribution.sh` helper. CI-006 now reads the Gradle digest from the CI-003 provenance argument `--gradle-sha256`, rather than requiring the removed inline `echo ... | sha256sum` command. The CI-003 static gate requires the provenance digest to equal the helper's hard-coded pinned digest. The build-environment inventory still independently hashes the downloaded ZIP and rejects any mismatch.

This keeps the downloader as the acquisition/checksum enforcement path while preserving an explicit provenance value that binds the resulting SBOM to the same expected archive digest. No dependency verification metadata or checksum was weakened.


### CI-006C — inventory the verified cached Gradle archive

The shared downloader writes the checksum-verified Gradle ZIP to `$HOME/.gradle/distributions/gradle-8.9-bin.zip` and extracts it into `$RUNNER_TEMP`. CI-003 now passes that same cached ZIP path to the build-environment inventory generator. The previous `$RUNNER_TEMP/gradle-8.9-bin.zip` inventory path did not exist because extraction does not copy the source archive. A static workflow gate now requires the inventory to hash the exact verified cache file and rejects the nonexistent temporary path.

The inventory still computes the ZIP's SHA-256 and compares it with the workflow provenance pin before recording the Gradle component. This fixes artifact-path wiring only; it does not relax the digest check.


## CI-006D — fail-closed hosted-runner drift diagnostics (2026-11-13)

CI-003 issue #66 records two exact-head failures on GitHub-hosted Ubuntu
runners with different image versions. The unsigned APK SHA-256 and runtime
SBOM matched in both attempts, but the complete scoped host-environment
inventory did not. The strict full-environment equivalence gate remains
**mandatory and failing** when any recorded inventory, runner identity,
toolchain or SPDX document differs.

The independent verifier now writes a bounded `differences` section to
`build-environment-verification.json` even when verification fails. It
reports changed runner identity field names, both image versions, changed
toolchain field names, complete counts of package-URL differences, and
up to 12 name/version/architecture examples from each runner. Arbitrary
component metadata, paths, environment variables and secrets are excluded.
The verifier's exception also identifies which comparison categories differ.

Negative controls exercise image-version drift, 17 additional host packages
(truncated sample but exact total count), and a changed Gradle version with
validly rebound SPDX/provenance. All three **must fail**. The identical
environment positive control must still pass. This change is diagnostic only:
it does **not** suppress the failure, exempt host packages, alter APK digest
verification, establish a pinned host image, or claim reproducibility success.

**Next acceptance work:** separately design a digest-pinned isolated build
environment or submit a reviewed policy distinguishing controlled build inputs
from host-image drift, with full host SBOM retention and a separately failing
host-drift status. That decision requires independent security/release review;
this diagnostic change does not authorize it. Signed release, OTA and Pixel
hardware gates remain blocked.
