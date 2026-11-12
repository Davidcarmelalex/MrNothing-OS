# QA-STACK-030 — Private SQLite replay-ledger directory

## Scope and reason

The host-side DurableReplayLedger stores a SQLite database with 0600
permissions. SQLite may also create -journal, -wal and -shm sidecars
in the same directory. The previous ancestor check allowed a directly
world-readable 0755 directory and a sticky 01777 directory. Sticky
semantics protect existing file names from unlinking, but do not prevent
another directory writer from pre-creating an unclaimed sidecar name.
World-readable directories also expose the namespace of SQLite sidecars.

The POSIX gate now requires the immediate database parent to be owned
by the process effective UID and inaccessible to group/others (mode & 077
== 0). Trusted ancestors retain the previous symlink, owner and sticky
directory checks, allowing a private child directory under /tmp.

This is a fail-closed compatibility tightening: existing deployments
using a direct /tmp/ledger.sqlite path or a shared 0755 directory
must provision a dedicated private subdirectory before enabling admission.
No migration, permission change or privileged operation is performed by
the ledger itself.

## Acceptance

- Reproduce previous acceptance of 0755, 01777 immediate parents
  and admission after relaxing the parent to 0755.
- Reject immediate group/world-readable, executable or writable parents
  during initialization; reject post-initialization relaxation.
- Accept a private 0700 immediate parent under a trusted sticky ancestor.
- Run full Python regression and source/static gates at exact commit head.
- Obtain independent security review before integration acceptance.

## Limitations

Pathname and metadata checks are not a complete defense against
same-UID attackers, races involving directory replacement, malicious
SQLite schema changes, or distributed replay. This is a host-side,
no-execution prototype, not a physical Pixel or production security claim.
The upstream shared SKILL.md remains unverified; the project-specific
PROJECT-ADAPTER.md remains the governing local adapter.
