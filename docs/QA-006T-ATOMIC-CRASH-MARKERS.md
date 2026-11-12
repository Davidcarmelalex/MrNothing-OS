# QA-006T — atomic SQLite crash-test synchronization markers

## Finding
A fresh-clone AGENT-006S run intermittently failed the existing
`test_process_death_after_signed_revocation_commit_preserves_revocation_atomically`
because the parent observed the subprocess marker path before its content was
written. The test asserted an empty string instead of `ready`, even though
the targeted rerun and full rerun passed. This was a synchronization race in
the test harness, not evidence of an SQLite durability defect.

## Bounded correction
The enrollment registry and action-reservation crash subprocesses now write
markers to unique, same-directory `.partial` paths, close the files, then
atomically publish the final marker using `os.replace`. The parent only
polls the final path. No production source, database schema, authorization
policy, Android behavior, permissions, or execution integration changes.

This protocol prevents readers from seeing newly created partial marker
content. It does not claim crash-proof marker durability, which is not
needed for these tests: the marker is only a synchronization signal and
SQLite durability is asserted separately after process termination.

## Acceptance
- Existing before/after SQLite COMMIT process-death tests pass repeatedly.
- Full Python policy suite, compilation and whitespace checks pass.
- Exact-head hosted CI must pass and a separate reviewer must verify that
  the subprocess pause remains on the intended side of COMMIT.
- No emulator, Pixel hardware, device installation or release claim follows
  from this test-only change.

Upstream shared `SKILL.md` remains absent/unverified; the local
`PROJECT-ADAPTER.md` is not a verified upstream installation.
