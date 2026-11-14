# CI-003Q — fail-closed staging parent ancestry

**Scope:** Experimental, unapproved offline Android builder candidate, stacked on CI-003P. This does not alter the Android app, production workflow, signing, OTA, or device behavior.

## Finding

CI-003P checked the immediate destination parent with `O_NOFOLLOW` and mode checks, but `os.open(stage_directory.parent, ...)` could still traverse a symlink or a group/other-writable directory in an earlier pathname component. A trusted final directory alone did not establish a trusted destination ancestry.

## Bounded correction

The staging destination parent is now opened component-by-component from `/` using `O_DIRECTORY|O_NOFOLLOW` and directory-relative descriptors. Each opened component must be owned by root or the effective UID. Group/other-writable ancestors are refused, except root-owned sticky **intermediate** directories such as `/tmp`; the final destination parent must never be group/other writable. Relative and `..` destination paths are refused. No ancestor permissions are changed. Existing archive hashes, ZIP checks, exclusive destination creation and cleanup gates remain intact.

New adversarial tests cover a symlinked intermediate ancestor, a group-writable intermediate ancestor and a relative destination. Existing tests exercise successful staging under root-owned sticky temporary-directory ancestors and immediate-parent refusal.

## Evidence and limits

Implementation checkout at CI-003P parent `9f33a741bd2153484ab0df36b3fa0507f75ba749`: focused `tests.test_ci003_builder_inputs` **49/49 PASS** and full Python discovery **1,218/1,218 PASS** (Python 3.14.4). Existing SQLite ResourceWarnings remain. Exact-head hosted CI and independent non-author security review are required after push; do not substitute a self-run checkout for approval.

The policy is Linux-specific and fail-closed. It does not protect against privileged or same-UID concurrent modifications, establish OCI provenance, pin missing Android SDK 35/build-tools 35.0.0 archives, make context publication atomic, or prove dual-builder reproducibility. Do not weaken the strict runner-image SBOM drift gate (issue #66). No Docker build, emulator, physical Pixel 9 Pro, signing, OTA, flashing or production deployment was performed.

The project-local `PROJECT-ADAPTER.md` exists; the upstream shared `SKILL.md` remains absent/unverified.
