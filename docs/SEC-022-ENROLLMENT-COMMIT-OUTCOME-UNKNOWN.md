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

The exception exposes only bounded reconciliation metadata: `operation`, `device_id`, `enrollment_id`, `credential_generation` and `envelope_sha256`. It does not expose the signed envelope, private key material or credential bytes. `reconciliation_required` is true.

If COMMIT raises while the transaction is still open and ROLLBACK succeeds, the registry reports a definite `EnrollmentRegistryError` (or `EnrollmentConflict` for an integrity constraint). That is a confirmed rollback path, not an unknown outcome.

## Caller recovery contract

1. Stop automatic retries when `EnrollmentOutcomeUnknown` is raised.
2. Reopen the enrollment registry and validate its durable state.
3. Inspect `history(device_id)` for the exact `envelope_sha256`, enrollment ID, operation and generation.
4. Compare the active device row and generation with the matching history entry.
5. If the exact history entry is present once, treat the signed statement as applied; do not replay it.
6. If the durable state cannot be reconciled unambiguously, remain fail-closed and require supervised recovery. Absence of an acknowledgement is never permission to retry.

The registry does not automatically retry, infer success from an exception message, or execute an external side effect.

## Regression evidence

The test suite covers acknowledgement loss for initial enrollment, rotation and revocation after COMMIT; a pre-COMMIT failure followed by successful rollback; and a failed rollback. It checks the typed outcome metadata, durable row/history state and replay rejection. Tests use synthetic Ed25519 authority and P-256 consent keys with temporary local SQLite databases.

## Limits

This is a same-host SQLite application-level outcome contract. It does not establish power-cut or storage-controller durability, filesystem corruption recovery, multi-host transactions, production authority provisioning, Android Keystore/StrongBox behavior, or exactly-once external effects. Independent security review remains mandatory. The real device executor remains disconnected.
