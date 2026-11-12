# SEC-021C — crash recovery and commit-acknowledgement uncertainty

**Status:** synthetic fault-injection regression; no-side-effect prototype. Independent human security review remains pending.  
**Branch:** `feat/phase1-agentic-phone`  
**Predecessors:** SEC-021A lock-coupled admission and SEC-021B live-capability final admission.

## Failure model

A database client can lose the acknowledgement for a SQLite `COMMIT` after SQLite has durably committed the transaction. The caller then sees an exception but cannot infer that the write rolled back. Returning the pre-transaction snapshot as if it were authoritative would be unsafe.

AGENT-005R adds three exact failure-injection cases:

1. **Action-ledger claim commit acknowledgement lost.** The underlying `DISPATCH_STARTED` commit succeeds, then the test connection raises `sqlite3.OperationalError`. The public claim result is deliberately uncertain and carries the pre-claim snapshot state. Reopening the ledger reveals `DISPATCH_STARTED`; a duplicate claim is rejected as `ALREADY_CLAIMED`.
2. **Enrollment-lock commit acknowledgement lost.** The action-ledger `DISPATCH_STARTED` commit succeeds first. The enrollment context then commits its read/serialization transaction and the test connection loses that acknowledgement. The caller receives `ENROLLMENT_LOCK_COMMIT_UNCERTAIN`; the durable reservation remains `DISPATCH_STARTED` and cannot be reclaimed.
3. **Outcome commit acknowledgement lost.** The underlying `UNKNOWN_OUTCOME` update commits, then the test connection raises. Reopening the ledger reveals the terminal outcome; recording the same outcome is idempotent and a dispatch retry is rejected.

The proxy delegates to a real SQLite connection, executes the first `COMMIT`, and only then raises. This models acknowledgement loss after commit; it does not simulate a power cut, storage-controller failure or corrupt filesystem.

## Recovery contract

- Never infer rollback from a commit exception.
- Never automatically retry a `DISPATCH_STARTED` reservation.
- Reopen and inspect the durable ledger before any recovery decision.
- If the real-world action result cannot be established, retain/record `UNKNOWN_OUTCOME`; do not convert uncertainty to `FAILED_NO_EFFECT`.
- Preserve the idempotency binding and terminal tombstone so duplicate requests cannot create a new dispatch.
- Any future executor must keep its own durable side-effect journal and idempotency contract. SQLite admission state alone cannot prove whether an external side effect occurred.

## Scope and safety

This change adds tests and documentation only. It does not change production code, add a reconciliation daemon, retry a command, connect an executor, invoke Android, use shell/ADB, grant permissions, or contact a physical device. Existing `CommandRouter` remains fail-closed.

The guarantee remains local to the two SQLite stores and a single host/process architecture. The tests prove the modeled post-commit acknowledgement-loss paths, not distributed atomicity, power-loss durability on every filesystem, malicious same-process behavior, or physical-device execution semantics.

## Exact regression tests

- `test_ledger_commit_ack_loss_is_not_replayed_after_restart`
- `test_enrollment_commit_ack_loss_is_reported_after_ledger_claim`
- `test_outcome_commit_ack_loss_preserves_terminal_unknown_state`

All must pass in the exact-head Phase 1 Python policy workflow. Android emulator reruns are not required for this Python-only change; the most recent exact-head emulator baseline remains separately identified in the engineering run record.

## AGENT-005S — cross-process claim serialization (2026-11-08)

The new \`test_cross_process_dispatch_claim_has_one_winner_and_survives_restart\` regression starts two independent CPython interpreters. Each constructs its own \`SQLiteOwnerEnrollmentRegistry\` and \`DurableActionReservationLedger\` against the same two owner-only SQLite files. Per-process ready files and a shared release gate make both claim attempts concurrent rather than merely sequential.

Acceptance assertions:

- Exactly one process receives \`DISPATCH_CLAIMED\`.
- The other receives \`ALREADY_CLAIMED\`.
- Both observe the same durable \`DISPATCH_STARTED\` state.
- Both child interpreters terminate abruptly after reporting their result.
- The parent reopens the ledger after both processes exit and confirms the claim remains \`DISPATCH_STARTED\`.
- A further claim is rejected as \`ALREADY_CLAIMED\`; no retry or device action occurs.

This extends the existing thread/connection concurrency tests to separate OS processes on one host. It does **not** establish multi-host/distributed locking, power-loss durability, or external side-effect semantics. The final-admission callback in this storage-only test is a test guard, not a production authorization capability. No production source, Android permission, executor, shell bridge, or device behavior changes.



## AGENT-005T — process death between the two store commits (2026-11-08)

The new test_process_death_after_ledger_commit_before_enrollment_release_preserves_claim regression starts a separate Python interpreter and pauses it immediately after SQLite has successfully committed DISPATCH_STARTED, while the enrollment writer transaction is still open and before claim_dispatch can return. The parent observes the post-commit marker, terminates the child process, then reopens both stores.

Acceptance assertions:

- The reservation ledger recovers with DISPATCH_STARTED after the child is terminated.
- The enrollment database is readable and still reports the matching owner/device generation as active; process death released its writer lock.
- A duplicate claim is rejected as ALREADY_CLAIMED.
- No executor, Android API, shell, network or external side effect is invoked.

This tests one same-host process-death boundary between the two SQLite commits. It is not a power-cut, filesystem-corruption, distributed transaction or hardware durability test. The reservation remains non-replayable; no automatic retry is introduced.


## AGENT-005U — process death before the action-ledger COMMIT (2026-11-08)

The new test_process_death_before_ledger_commit_rolls_back_and_allows_one_claim regression complements AGENT-005T by testing the opposite side of the SQLite commit boundary. A separate Python interpreter acquires the enrollment writer lock, opens the action-ledger write transaction, applies the DISPATCH_STARTED update, and pauses in a test-only connection proxy immediately **before** the underlying SQLite COMMIT call. The parent observes a marker emitted before that call and terminates the child process.

Acceptance assertions:

- Reopening the action ledger recovers the original reservation as RESERVED; the uncommitted DISPATCH_STARTED update is not visible.
- The enrollment database is readable and reports the matching owner/device generation as active; process death released its writer lock.
- A subsequent valid claim can transition the reservation to DISPATCH_STARTED exactly once.
- A second claim is rejected as ALREADY_CLAIMED.
- No executor, Android API, shell, network or external side effect is invoked.

Together, AGENT-005T and AGENT-005U exercise process death immediately after and immediately before the action-ledger commit boundary. They are same-host SQLite process-crash tests, not power-cut, filesystem-corruption, distributed-transaction, storage-controller or external exactly-once guarantees. The test guard is not a production authorization capability. No production code or Android behavior changes.


## AGENT-005V — signed enrollment revocation process-death recovery (2026-11-08)

Two test-only subprocess regressions exercise the apply_signed_enrollment transaction itself, rather than only the separate action-ledger transaction.

1. **Death before enrollment COMMIT:** the child applies the signed revocation update and history insert inside the open SQLite transaction, then pauses before forwarding the real COMMIT. The parent terminates it. Reopening proves the owner/device row remains active at generation 1 and the history contains only the original enrollment. A previously reserved action can then be claimed once; the duplicate claim is rejected.
2. **Death after enrollment COMMIT:** the child forwards the real SQLite COMMIT, writes a durable test marker, then pauses before returning from apply_signed_enrollment. The parent terminates it. Reopening proves the owner/device row is inactive at generation 2 and the revocation history row is present exactly once. A previously reserved action is denied with DEVICE_NOT_ACTIVE and remains RESERVED.

The two cases verify the atomic relationship between the mutable owner/device row and append-only enrollment history across the process-death boundary. They also verify that dispatch admission observes the recovered enrollment state: rollback permits one later claim, while a committed revocation denies it.

**Limits:** these are same-host process-kill tests using synthetic keys and local SQLite. They do not establish power-cut/filesystem/controller durability, multi-host serialization, external exactly-once effects, or production authority provisioning. No production source, Android permission, executor, shell, network listener, or device action changed. Independent human security review remains required.
