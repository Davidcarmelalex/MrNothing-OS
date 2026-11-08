# AGENT-004H — durable consent-bound action reservation

**Status:** The Python/SQLite state machine is integrated behind an adapter-owned reservation method. It now supports an enrollment-locked pre-dispatch claim. It still does not query Android permissions or connect to an action executor.

## Why this is not a duplicate replay ledger

The existing DurableReplayLedger in core/command_admission.py stores a device/command replay marker for the legacy signed-command admission prototype. It does not bind the owner session, consent nonce, canonical action digest, transport certificate, credential generation, consent key, or side-effect lifecycle. AGENT-004H adds that separate final-action record; it does not replace or modify the legacy replay prototype.

## Binding and idempotency

The request record binds:

- owner, device and transport-session identifiers;
- one-use consent capability nonce and protocol version;
- exact allowlisted action ID and canonical argument SHA-256;
- signed issue/expiry timestamps;
- transport certificate SHA-256 and credential generation;
- consent public-key SHA-256.

The idempotency key is SHA-256 over a domain-separated canonical JSON encoding of every binding field. A database uniqueness constraint also prevents one owner/device capability nonce from being re-used with a changed binding. V1 is restricted to read_screen; V2 accepts only read_screen, navigate and scroll.

The public request dataclass is storage input, not proof of authentication. Only a future trusted adapter may construct it from its retained verifier-created capability record. Model output, request JSON and caller-supplied authentication Booleans must never populate it.

## Durable storage and concurrency

- Dedicated file-backed SQLite database; in-memory and URI paths are refused.
- New database files are created owner-only; existing symlinks, non-regular files and group/world-readable POSIX files are refused.
- WAL mode, synchronous FULL, bounded busy timeout and schema version 1.
- Reservation and state transitions use BEGIN IMMEDIATE transactions.
- One-host SQLite only; this is not a distributed lock.
- Capacity is bounded and fails closed. Records are not automatically evicted because that could re-enable a replay.
- Only identifiers, action metadata, digests and redacted outcome codes are stored. Raw arguments, screen contents, credentials and raw results are not stored.

## State machine

~~~text
RESERVED -> DISPATCH_STARTED -> COMPLETED
                            -> FAILED_NO_EFFECT
                            -> UNKNOWN_OUTCOME

RESERVED -> CANCELLED
RESERVED -> FAILED_NO_EFFECT
~~~

- Same nonce and same binding returns IDEMPOTENT_REPLAY; it never creates a second dispatch.
- Same nonce with a changed action, argument digest, session, certificate, credential generation or consent key returns IDEMPOTENCY_CONFLICT.
- Exactly one concurrent caller can move RESERVED to DISPATCH_STARTED.
- Reservation creation and dispatch claim check the signed issue/expiry window using a clock read taken after acquiring the SQLite write transaction. An expired RESERVED row is terminally changed to FAILED_NO_EFFECT with CAPABILITY_EXPIRED; a future-dated row is not claimable yet.
- These wall-clock checks are defense in depth. The live transport adapter must still enforce its monotonic session/challenge deadlines and current enrollment at the final admission boundary; the ledger alone is not proof of current owner authority.
- Cancellation and pre-dispatch denial are permitted only while RESERVED.
- A permission denial before dispatch can be recorded as FAILED_NO_EFFECT and permanently closes that capability.
- FAILED_NO_EFFECT after dispatch is valid only when the caller can prove no side effect occurred.
- UNKNOWN_OUTCOME is terminal. Never blindly replay an uncertain action.
- DISPATCH_STARTED survives process restart and is not automatically reclaimed. A recovery process must reconcile it and record UNKNOWN_OUTCOME when the side-effect result cannot be established.
- Duplicate terminal requests can read the stored state and redacted outcome through get(); they do not execute again.

A successful storage transition means only that a row/state transition was durably recorded. It is not action authorization and it does not execute anything.

## Android permission revalidation contract

No Android permission gate is implemented by this change. A future executor must treat OS permission/role state as a separate, revocable gate:

1. Reserve the verified capability before considering dispatch.
2. Query the current Android permission/role/service state after reservation.
3. Atomically claim dispatch only after the preflight succeeds.
4. Re-query the relevant OS state immediately before the platform API call; do not reuse a planning-time or cached Boolean.
5. If access is revoked before dispatch, call reject_before_dispatch with a redacted reason and do not claim.
6. If the platform rejects the call, record FAILED_NO_EFFECT only when absence of side effect is certain; otherwise record UNKNOWN_OUTCOME.

Action-specific future requirements:

- navigate: re-resolve the exact allowlisted package and visible launch target; no broad package enumeration permission is implied.
- scroll: require the explicitly user-enabled, currently enabled accessibility service and re-check immediately before each action.
- read_screen: require a fresh, user-approved MediaProjection/capture session; no persistent Boolean substitutes for the system grant.

Permission state is deliberately not persisted as authority in the reservation database. It can be revoked at any time. No permission is declared, requested or granted by AGENT-004H.

## Verification and limitations

The new test module covers 35 cases: exact binding, idempotent duplicate, nonce conflict, cross-context binding, concurrent reservation/claim, cancellation-versus-dispatch, permission-denial terminal state, outcome persistence, restart behavior, sticky uncertain outcome, capacity, malformed types/digests, v1 action restriction, file permissions, symlink refusal, WAL/FULL/schema configuration and corrupt-store failure.

Local scratch validation executed against the new module and tests only:

- python3 -m compileall -q core tests — passed.
- python3 -m unittest discover -s tests -p 'test_*.py' -v — 35 passed.

The full repository preflight, exact-head GitHub Actions, Android runtime permission checks and emulator workflow must still run against the committed tree. No local full-repository test result is claimed.

No mTLS adapter integration, Android PermissionGate, listener, shell bridge, Android executor, device action, runtime permission grant, physical Pixel 9 Pro test or production deployment was added. Independent human security review remains pending.


## AGENT-004I — adapter-owned reservation integration

OwnerConsentTlsAdapter.reserve_action_capability(...) is the only new integration point. It accepts the exact live server-side SSLSocket, the adapter-minted opaque capability, the action/argument object, and an exact DurableActionReservationLedger instance. It does not accept an ActionReservationRequest, owner/device/session IDs, certificate fingerprints, key digests, generations, or authentication Booleans from the caller.

The method shares a single private capability-validation routine with consume_action_capability. Before constructing the reservation request it revalidates:

- exact socket object, current file descriptor, negotiated TLS version, ALPN and server-context identity;
- currently active enrolled transport certificate and owner/device mapping;
- transport credential generation and adapter-retained session identity;
- retained challenge nonce, protocol version, action, signed argument digest and wall-clock validity;
- current owner enrollment state, transport binding, credential generation and consent public-key digest;
- monotonic session/capability/challenge expiry, with repeated clock and transport-registry reads immediately before reservation.

Only after those checks does the adapter construct ActionReservationRequest from its private _IssuedActionCapability and retained _IssuedChallenge. Caller-supplied identity snapshots cannot populate the durable row.

A successful result is RESERVATION_CREATED_NO_EXECUTION; the row remains RESERVED. The adapter consumes the in-memory capability after any definitive ledger decision. A registry outage or reservation-store exception fails closed and preserves the short-lived capability only for a bounded retry before expiry. An idempotent duplicate is reported as IDEMPOTENT_REPLAY, not as a new reservation.

**Dispatch remains deliberately unavailable through this adapter method.** It never calls claim_dispatch, never queries Android permissions, and never invokes a platform API. A future trusted Android coordinator must query the current action-specific OS permission/role/service state after reservation and again immediately before the platform call. It must revalidate the live transport/enrollment/capability context at the final dispatch boundary; the durable row is not a reusable authorization token. No listener, permission grant, shell bridge, device action, or production execution path was added.

The local mTLS tests cover successful v2 reservation, exact argument binding, transport revocation, consent-key rotation (including rotation between consecutive registry reads), enrollment-registry outage/retry, reservation-store failure/retry, duplicate nonce replay and monotonic expiry/expiry-during-commit. The exact-head Phase 1, CI-003 and QA-005 workflows are the acceptance gate for this change. Independent human security review remains pending.


## AGENT-005K — time-bounded reservation and dispatch claim

The storage state machine now refuses to create a reservation when its signed issue time is still in the future or its expiry has been reached. `claim_dispatch` re-reads the clock only after acquiring the SQLite `BEGIN IMMEDIATE` write transaction and refuses a claim outside the signed validity window. An expired RESERVED record is atomically made terminal as `FAILED_NO_EFFECT/CAPABILITY_EXPIRED`; a future-dated record remains RESERVED but cannot be claimed until its issue time.

The clock read occurs inside the write transaction so a caller queued behind another writer cannot rely on a stale pre-lock timestamp. These checks are defense in depth only: the adapter must still validate the exact live TLS peer, monotonic capability/session expiry, current enrollment generation and Android permission state immediately before any future platform call. This change does not connect `claim_dispatch` to the transport adapter or an executor and does not authorize device actions.


## AGENT-005L — enrollment-locked final dispatch claim

claim_dispatch now requires the exact SQLiteOwnerEnrollmentRegistry instance. It first reads the immutable reservation binding, then acquires the enrollment database's BEGIN IMMEDIATE writer lock, validates the active owner/device, transport-certificate fingerprint, credential generation and consent-key digest, and only then enters the reservation ledger's own BEGIN IMMEDIATE transaction. The ledger re-reads the complete immutable binding and commits DISPATCH_STARTED while the enrollment writer lock remains held.

All signed enrollment rotations/revocations use the same enrollment database writer lock. Therefore:
- If rotation/revocation commits first, the final claim observes the inactive/new generation and is denied.
- If the final claim acquires the enrollment writer lock first, rotation/revocation cannot commit until the reservation's DISPATCH_STARTED transaction commits; the claim is ordered before the later enrollment change.
- If either store is unavailable, the claim fails closed.
- If the ledger commit succeeds but the enrollment lock cannot cleanly close, the method returns ENROLLMENT_LOCK_COMMIT_UNCERTAIN; the row must be reconciled and must not be dispatched from that response.

This is single-host lock coupling, not a multi-database atomic commit, distributed lock or multi-host guarantee. Both SQLite files must be local to the same host and all enrollment changes must continue to use apply_signed_enrollment. The caller must still revalidate the exact live TLS session and monotonic deadline; this storage boundary does not perform Android permission checks. No executor or device action is connected.
