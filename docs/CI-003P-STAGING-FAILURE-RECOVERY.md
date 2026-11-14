# CI-003P — fail-closed cleanup of incomplete offline builder contexts

**Scope:** Candidate-only CI-003 builder archive staging, stacked on CI-003O. No Android app, production workflow, signer, OTA, container runtime, or release change.

## Failure mode

CI-003O exclusively created `builder/inputs` before validating both archives. If validation of the second archive failed, a partial directory could remain. Subsequent attempts correctly refused to overwrite it, but the leftover required manual cleanup and could be mistaken for a completed context by an operator. The Dockerfile's own locked SHA-256 check remained mandatory and would reject missing/mismatched archives.

## Bounded correction

On unsuccessful staging, cleanup now checks that the directory entry still refers to the exact inode created by this invocation and contains only the two allowlisted archive filenames. It then unlinks those entries using the retained directory descriptor, removes the empty directory relative to the checked parent descriptor, and fsyncs the parent. Unexpected files or directory substitution prevent cleanup rather than permitting arbitrary deletion. A cleanup failure does not suppress the original verification error. Successful contexts remain unchanged.

Regression tests cover a tampered second archive with safe retry, a missing second archive after partial copying, and refusal to delete an unexpected foreign entry. This is a cleanup and idempotence improvement, **not atomic context publication** and not a guarantee against a same-user or privileged adversary modifying the directory after staging. CI-003 remains blocked on independent OCI provenance, SDK 35/build-tools 35.0.0 inputs, dual-builder reproducibility and independent security review.

## Acceptance boundaries

Only source-level and Python tests are runnable in this isolated cycle; Android/JVM hosted checks must be evaluated on the exact pushed SHA. No Docker image build, device/emulator test, signer, firmware, OTA or production deployment is authorized by this change. The shared upstream `SKILL.md` remains unverified; the project-specific `PROJECT-ADAPTER.md` is present.
