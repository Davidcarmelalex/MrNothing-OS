# SEC-021A — lock-coupled final dispatch admission

**Status:** Implemented prototype; exact-head CI is the acceptance source. No executor is connected.  
**Scope:** Order a durable DISPATCH_STARTED claim against signed owner-enrollment rotation/revocation across the two existing local SQLite stores.

## Problem

SEC-019A already serializes consent-nonce consumption with enrollment changes in the owner-enrollment database. AGENT-005K separately hardened the action-reservation ledger's issue/expiry checks. Those protections do not by themselves order the later DISPATCH_STARTED claim against a revocation committed in the other database.

A read-only enrollment lookup followed by a separate ledger claim leaves a time-of-check/time-of-use window.

## Lock-coupled protocol

1. Read the immutable reservation snapshot from the action ledger. This read holds no database lock.
2. Require the exact SQLiteOwnerEnrollmentRegistry implementation and distinct database files.
3. Acquire BEGIN IMMEDIATE on the enrollment database.
4. While holding that writer lock, read the current owner/device row and require active state plus exact owner ID, device ID, transport-certificate SHA-256, credential generation and consent-public-key SHA-256.
5. While still holding the enrollment writer lock, acquire BEGIN IMMEDIATE on the action ledger.
6. Re-read the reservation row and compare every immutable binding field with the initial snapshot.
7. Require RESERVED and recheck the signed issue/expiry window using the ledger clock after both writer locks are held.
8. Commit DISPATCH_STARTED in the action ledger.
9. Only then leave/close the enrollment transaction and release its writer lock.

## Ordering argument

Signed enrollment rotation/revocation already uses BEGIN IMMEDIATE on the same owner-enrollment database.

- If rotation/revocation commits first, the claim waits for the lock and then observes inactive state or a different credential generation/fingerprint/key digest. It is denied and the reservation remains RESERVED.
- If the claim obtains the enrollment writer lock first, rotation/revocation cannot commit while the claim runs. The action ledger commits DISPATCH_STARTED before the enrollment lock is released, so the claim is durably ordered before the later rotation/revocation.
- Concurrent claims still serialize through the action ledger's own writer transaction; only one can transition RESERVED to DISPATCH_STARTED.

The ordering point is the action-ledger commit while the enrollment writer lock is held. A claim that has crossed this point is already in flight for lifecycle/revocation ordering, even though no platform action is executed by this prototype.

## Failure semantics

- Missing, corrupt, unavailable or mismatched enrollment state fails closed.
- Reservation-store failure rolls back/releases the enrollment lock and does not authorize dispatch.
- A reservation binding change, non-RESERVED state, future issue time or expired capability denies the claim.
- If the action-ledger commit succeeds but the enrollment context cannot cleanly close, the method returns ENROLLMENT_LOCK_COMMIT_UNCERTAIN. The reservation may remain DISPATCH_STARTED; the caller must not execute and recovery must reconcile it without automatic replay.
- DISPATCH_STARTED is never automatically reclaimed after process restart.

## Explicit limits

This is local, single-host SQLite lock coupling, not a distributed transaction, multi-host lock or cross-database atomic commit. It assumes all enrollment mutations continue to use the same SQLiteOwnerEnrollmentRegistry database and BEGIN IMMEDIATE transaction. It does not revalidate the exact live TLS socket, adapter-owned monotonic session/capability deadline, Android permission/role/service state, or platform result. Those checks belong in a future trusted coordinator immediately before platform invocation.

No listener, executor, Android permission, AccessibilityService, MediaProjection service, shell bridge, root access, physical device action or production release is enabled.

## Regression gates

- Revocation committed before claim rejects and leaves the reservation RESERVED.
- Credential rotation committed before claim rejects the old generation.
- A real two-thread test holds the enrollment writer lock during the ledger claim and proves revocation cannot commit until after DISPATCH_STARTED.
- Missing/corrupt enrollment storage fails closed and leaves the reservation RESERVED.
- Existing action-ledger tests continue to cover idempotency, one-use claims, expiry, cancellation, outcomes, restart and storage failure.

Independent human security review remains required before this boundary can authorize a real executor.
