# QA-STACK-021 — Replay-ledger ancestor path hardening

Scope: isolated host-side DurableReplayLedger prototype, on top of
QA-STACK-020 (d3ed0612ffe63d8f84641a98cab3f3f8fc8a3a8f).
No Android permissions, network endpoint, device actions or executor changes.

## Reproduced weakness

The existing path gate inspected only the immediate database parent with
os.stat, following directory symlinks. An alias to a private directory was
accepted. A directory renamed and reintroduced through a symlink could retain
the same database inode, bypassing the file-identity comparison. A writable,
nonsticky grandparent could also replace an otherwise private parent.

## Bounded change

On POSIX, verify each directory component from the ledger parent through the
filesystem root using os.lstat, rejecting symlinks, non-directories and
group/other-writable nonsticky ancestors and directories owned by
identities other than the process owner or root. Root/current-user-owned sticky
directories remain supported. Run the gate during initialization and both
sides of SQLite connection establishment, as before.

Seven additional regression cases cover symlinked parents/grandparents, unsafe
grandparents, untrusted directory owners, permission relaxation and
same-inode parent alias replacement.
The original sticky-directory compatibility test remains intact.

## Acceptance and limitations

- Local preflight: 1,177 Python tests passed; launcher accessibility/recovery
  source gate passed; no Android runtime or hardware test in this task.
- Focused command-admission tests: 46 passed.
- No independent human security or accessibility approval.
- Directory checks are pathname-based and cannot guarantee immunity to
  concurrent same-user or privileged TOCTOU attacks; secure directory-fd
  traversal and SQLite VFS anchoring remain a separate architectural review.
- This is not a distributed ledger, anti-rollback mechanism, production
  enrollment endpoint, signed release or device-flashing authorization.
- Upstream shared SKILL.md package remains unverified; only the local
  PROJECT-ADAPTER.md is known.
- M1–M8 acceptance is unchanged; no milestone is independently complete.

## Integration policy

Do not overwrite or merge the protected branch. Keep the QA-STACK-021
scoped branch separate while PR #51's exact-head CI is queued and
QA-STACK-020 remains unintegrated. Require an independent reviewer and
exact-head CI before consolidation.
