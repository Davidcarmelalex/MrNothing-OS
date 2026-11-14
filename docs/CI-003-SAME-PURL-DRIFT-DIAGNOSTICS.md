# CI-003 — same-package-URL drift diagnostics

## Scope and motivation

The strict CI-003 independent-runner verifier already refuses non-identical
build-environment inventories. Before this change, its bounded drift report
only counted package URLs exclusive to each runner. A package present under
the same URL on both runners but with different checksum or metadata therefore
failed the strict gate without an actionable component-level explanation.

## Bounded correction

The verifier now also compares canonical component records at shared package
URLs and emits changed_common_component_count and a bounded
changed_common_component_sample. Samples include package kind/name/version
and changed field names only; checksum bytes, arbitrary metadata values,
paths and environment variables are never emitted. The existing sample limit
also applies to this new category. OS-package versus non-OS drift classification
now includes shared-URL record changes.

No inventory equality, provenance, SBOM, APK, or runner-image gate is relaxed.
The new diagnostic does not pin GitHub-hosted runner images or resolve their
observed OS-package drift. It does not authorize release signing or deployment.

## Verification

Tests exercise independently valid synthetic runner bundles with the same
package URL but different opaque metadata or Gradle checksum; both must still
raise and write a bounded diagnostic. Additional tests cover OS/non-OS
classification, sample truncation and omission of arbitrary values.
Hosted Android/CI and independent non-author review remain separate gates.
