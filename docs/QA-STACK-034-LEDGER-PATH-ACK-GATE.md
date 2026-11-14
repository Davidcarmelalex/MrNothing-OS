# QA-STACK-034 — Canonical replay-ledger pathname acknowledgement gate

**Scope:** `core/command_admission.py` and its host-only regression tests. Candidate is stacked on QA-STACK-033 / draft PR #62. No Android permission, network listener, executor, firmware, production service or signing change.

## Failure reproduced before correction

A same-UID actor with write access to the ledger directory can replace the canonical SQLite pathname with a prior valid snapshot after the connection has passed its initial identity checks. SQLite can continue committing through its already-open file descriptor. In two deterministic, test-only SQLite connection subclasses, substitution immediately after `INSERT INTO seen` and immediately after `COMMIT` both resulted in `ADMITTED_NO_EXECUTION` before this patch, even though the canonical pathname no longer referenced the committed ledger. Both negative tests failed on the parent commit.

## Bounded mitigation

Recheck the canonical ledger inode, owner-only file mode, link count and private directory ancestry immediately before `COMMIT` and after `COMMIT` before acknowledging admission. Only attempt `ROLLBACK` when the connection still has an open transaction. On observed substitution, propagate SQLite operational failure to the existing `LEDGER_UNAVAILABLE` admission result. A post-commit refusal may consume a nonce in a detached file; that is a conservative availability cost, not permission to execute an action.

## Acceptance evidence and limits

Two new POSIX regression tests use temporary private SQLite files and deliberately replace the canonical pathname before or after commit. Both failed before the change and passed afterward. The full host Python test suite passed **1,213/1,213** locally; focused command-admission suite passed **74/74**. Python compilation, checked-in Android manifest security gate, launcher source accessibility/recovery gate and Git whitespace validation passed. Exact-head GitHub CI, separate clean-checkout regression, and independent human review are separate gates to complete after publishing the candidate.

**Residual risk:** A same-UID attacker can replace the database after the final check, tamper with rows, or restore a valid historical snapshot. These checks reduce an acknowledgement race but **do not** establish tamper-proof persistence, distributed replay safety, process isolation or hardware anti-rollback. The production design must isolate the ledger under a distinct protected identity and/or use a trusted external integrity anchor, with independently reviewed recovery semantics. The result remains `ADMITTED_NO_EXECUTION` only; no device action is enabled. M6 and all other milestone acceptance gates remain incomplete.

**Provenance:** The project-specific `PROJECT-ADAPTER.md` exists; upstream `SKILL.md` was not found in the audited repository and its shared package remains unverified.
