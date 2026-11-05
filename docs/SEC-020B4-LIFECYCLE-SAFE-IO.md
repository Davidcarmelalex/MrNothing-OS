# SEC-020B4 — lifecycle-safe trust-store I/O

**Scope:** move Android Keystore and AtomicFile inspection/commit work off the Activity main thread while preserving the existing owner-consent and credential boundary.

## Implementation

- OwnerAuthorityIoCoordinator provides one process-wide single-thread executor. All AndroidOwnerAuthorityTrustStore inspect() and commit() calls from the owner trust Activity are submitted through it, so Keystore/AtomicFile work is serialized and the UI thread does not wait for disk or hardware-backed cryptographic operations.
- OwnerAuthorityOperationGate issues one active operation token, rejects concurrent operations, and invalidates queued work on explicit cancellation or Activity destruction.
- Store inspection and final commit revalidation use immutable parsed input captured on the main thread. UI state is updated only through a main-thread Handler.
- The 30-second one-shot confirmation is still consumed on the credential callback. The background task reinspects the store, recomputes the mode/snapshot binding, rebuilds the Ready proposal, and rechecks device safety before claiming the commit boundary.
- Cancellation or Activity destruction before claimCommit() suppresses the queued commit. After the boundary is claimed, the already-authorized atomic transaction is allowed to finish; the UI callback is suppressed if the Activity is destroyed. A started AtomicFile/Keystore transaction is not falsely described as cancelable or rolled back.
- Explicit cancel/clear refuses to claim success if the transaction has already crossed the commit boundary. The executor remains disconnected.

## Tests and acceptance

- OwnerAuthorityOperationGateTest covers single-operation admission, cancellation-before-commit, destruction-before-commit, non-cancelability after commit claim, callback suppression after destruction, and concurrent begin attempts.
- Python source gates require a single-thread executor, off-main store calls, cancellation invalidation, commit-claim ordering, and the application-context device-safety recheck.
- Exact-head Phase 1 push/PR, CI-003 push/PR, and QA-005 emulator PR workflows must pass before accepting this change.
- The tests do not exercise Android Keystore, StrongBox, physical crash recovery, or Pixel 9 Pro behavior. Independent security review remains required.

## Transaction boundary clarification

The commit claim is the point after fresh credential success, one-shot confirmation consumption, trust-store snapshot revalidation, proposal reconstruction and a final device-safety check. Before that point, cancellation/destruction invalidates the operation and the worker must not commit. Once claimed, the storage transaction has started and is allowed to complete atomically; an Activity destruction after that point suppresses UI delivery but cannot safely promise rollback of an already-started AtomicFile/Keystore operation.
