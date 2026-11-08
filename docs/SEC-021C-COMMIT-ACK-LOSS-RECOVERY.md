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

