# SEC-022 — enrollment COMMIT outcome classification

**Status:** Implemented on `feat/phase1-agentic-phone`; exact-head CI is the acceptance gate.  
**Scope:** `SQLiteOwnerEnrollmentRegistry.apply_signed_enrollment` only.  
**Safety boundary:** No Android permission, network listener, executor, shell bridge or device action is added.

## Problem

A SQLite COMMIT call can raise after the underlying transaction has committed but before the caller receives an acknowledgement. Treating every such error as a definite rollback invites unsafe replay. Conversely, treating a pre-COMMIT failure as committed would strand valid work.

The registry previously wrapped both cases as the same `EnrollmentRegistryError`, leaving callers unable to distinguish a confirmed rollback from an ambiguous commit outcome.

## Typed contract

`EnrollmentOutcomeUnknown` is a subclass of `EnrollmentRegistryError`, preserving existing catch compatibility. It is raised when:

- the COMMIT call raises and SQLite reports that the connection is no longer in a transaction; or
- COMMIT raises while a transaction remains open, but an explicit ROLLBACK also fails.

The exception exposes only bounded reconciliation metadata: `operation`, `owner_id`, `device_id`, `enrollment_id`, `credential_generation` and `envelope_sha256`. It does not expose the signed envelope, private key material or credential bytes. `reconciliation_required` is true.

If COMMIT raises while the transaction is still open and ROLLBACK succeeds, the registry reports a definite `EnrollmentRegistryError` (or `EnrollmentConflict` for an integrity constraint). That is a confirmed rollback path, not an unknown outcome.

## Caller recovery contract

1. Stop automatic retries when `EnrollmentOutcomeUnknown` is raised.
2. Reopen the registry through a fresh `SQLiteOwnerEnrollmentRegistry` instance.
3. Call `reconcile_outcome_unknown(outcome)`. This is a read-only snapshot check that validates schema/integrity, exact history metadata and the current row against the latest history entry.
4. Interpret the result conservatively:
   - `APPLIED`: the exact enrollment ID, owner/device, operation, generation and envelope hash are in durable history, and the current owner/device row agrees with the latest history entry. Do not replay.
   - `NOT_OBSERVED`: the exact history entry is absent and the prior state is coherent. This is an observation, **not** a retry authorization; any further action requires supervised review.
   - `UNRESOLVED`: metadata, history/current state or database integrity does not reconcile. Remain fail-closed and require supervised recovery.
5. Every result has `automatic_retry_permitted=false`. The API never returns permission to resubmit a signed statement.

The API never infers success from an exception message, writes to the registry, retries, or executes an external side effect. It does not protect against a privileged attacker who can replace both the database and its filesystem state; production deployments still require an independently protected monotonic trust anchor and storage review.

## Regression evidence

The test suite covers acknowledgement loss for initial enrollment, rotation and revocation after COMMIT; a pre-COMMIT failure followed by successful rollback; and a failed rollback. Reconciliation tests classify exact committed history as APPLIED, a coherent pre-commit state as NOT_OBSERVED, and mismatched/corrupt state as UNRESOLVED. Every result denies automatic retry. Tests use synthetic Ed25519 authority and P-256 consent keys with temporary local SQLite databases. Tests use synthetic Ed25519 authority and P-256 consent keys with temporary local SQLite databases.

## Limits

This is a same-host SQLite application-level outcome contract. It does not establish power-cut or storage-controller durability, filesystem corruption recovery, multi-host transactions, production authority provisioning, Android Keystore/StrongBox behavior, or exactly-once external effects. Independent security review remains mandatory. The real device executor remains disconnected.
