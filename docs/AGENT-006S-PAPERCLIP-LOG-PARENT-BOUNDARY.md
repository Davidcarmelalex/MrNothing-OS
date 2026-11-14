# AGENT-006S — PaperClip log parent-directory boundary

## Finding
AGENT-006Q validated `mrnothing/` and `logs/` after opening them with
O_NOFOLLOW, but the containing directory (`HOME.parent`) was not checked.
If that parent is group/other-writable, another local account can replace
the `mrnothing` directory entry, defeating pathname stability and log
availability. A sticky shared directory does not provide the required
stable ownership boundary for this privacy-sensitive logger.

## Scoped correction
After opening the containing directory with O_DIRECTORY|O_NOFOLLOW,
validate its inode via fstat before creating/opening `mrnothing`:
- must be a directory owned by root or the effective UID;
- must not be writable by group or others;
- never chmod or otherwise modify the containing directory;
- fail closed without creating a log if validation fails.

The existing descriptor-relative operations and private 0700/0600
permissions remain unchanged. No Android API, device permission, executor,
network access, memory persistence or production service is changed.

## Verification and limitations
Two regression cases reject group-writable and sticky world-writable parent
directories and confirm no home/log entry was created. Full regression and
source checks must be recorded against the exact published commit.

This does not protect against a malicious privileged user, same-UID
processes, filesystem/kernel compromise, or symlinked ancestors of the
containing directory. Independent non-author security review remains
required. The upstream shared SKILL.md package remains unverified.

## Local isolated-checkout verification — 2026-11-14
- Base commit: `f42af837bcb8eed478cadbc472b7571441449a7a`.
- Focused PaperClip logging: 13/13 tests passed.
- Full Python unittest discovery: 940/940 tests passed.
- Python source compilation and `git diff --check`: passed.
- Hosted exact-head CI and non-author review: pending at this writing.
- A separate historical `feat/agent006r-paperclip-bounded-logs-20261109`
  branch exists; this AGENT-006S change does not modify that branch.
