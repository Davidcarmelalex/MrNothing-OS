# QA-STACK-017 — Replay-ledger path-boundary hardening

Scope: core/command_admission.py on the draft UX x MemoryVault integration PR, not production Android execution.

## Threat model and change

The previous file-level 0600/owner/inode checks did not reject a database
with multiple hard links, or a ledger path inside a group/other-writable,
non-sticky directory. Another user with write access to such a directory
could replace the pathname, causing denial of service or replay-state confusion.
The update rejects multi-linked database files both at initialization and
before every SQLite connection. It also rejects unsafe parent-directory
permissions at creation and connection, while allowing sticky writable
directories only if their owner is the process user or root.

Six new regression cases cover initialization, runtime permission changes,
hardlink changes, safe sticky directories and simulated untrusted ownership.
Rejection fails closed.

## Limitations and acceptance

This is a POSIX host-side prototype boundary. It is not a complete defense
against path-component symlink races, malicious same-user processes, hostile
filesystems, rollback, or distributed replay. A real device integration needs
private app storage, identity-bound authenticated transport and independent
security review. This change does not grant device permissions or execute commands.

Acceptance requires full Python preflight, targeted regressions, manifest and
accessibility source checks, syntax checks, exact-head hosted CI, and independent
human review. No M1-M8 milestone becomes complete from this patch.
