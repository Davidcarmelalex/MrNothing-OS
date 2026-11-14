# CI-003R — bind newly created offline builder staging directory to its inode

**Scope:** Unapproved offline CI-003 candidate, stacked on CI-003Q (PR #82).
This change does not enable an OCI build, alter Android permissions, or relax
the strict independent-builder provenance gate.

## Reproduced defect

At parent `5a9a290080e0067f0bf64fc0a2523ee662585489`:

1. If `os.open(stage_directory.name, O_NOFOLLOW|O_DIRECTORY, dir_fd=parent_fd)`
   failed after `os.mkdir` succeeded, the empty `builder/inputs` directory
   was stranded and blocked a safe idempotent retry.
2. If the new directory entry was replaced after `mkdir` but before `open`,
   the old implementation accepted the replacement inode as its own staging
   directory and populated it.

## Correction and acceptance

Capture the directory identity immediately after exclusive creation. Require
the subsequently opened directory descriptor to match that identity *before*
copying any verified archive. On an open failure, remove the empty context
only when the original inode is still present; preserve substituted or
nonempty entries for investigation. The existing post-copy publication
identity check, archive SHA-256 verification and ZIP preflight remain intact.

Two deterministic negative tests reproduced both defects before the fix and
passed afterward. A separate non-author security review is still required.

## Boundaries

This is a best-effort, no-follow, inode-checked local staging helper, **not**
a defense against privileged or same-UID concurrent filesystem mutation.
It does not establish base-image provenance, checksum-verified real SDK 35
inputs, container reproducibility, physical Pixel compatibility, signing,
OTA, or release readiness. No upstream shared SKILL.md was installed.
