# SEC-021B — live capability binding at final dispatch admission

**Status:** No-side-effect prototype; independent human security review pending.  
**Branch:** `feat/phase1-agentic-phone`  
**Predecessor:** SEC-021A lock-coupled enrollment/dispatch claim.

## Gap closed

SEC-021A orders the durable `DISPATCH_STARTED` claim against signed owner/device rotation and revocation, but a reservation alone does not prove that the exact live TLS session and adapter-retained owner-consent capability are still valid at the final claim point. The previous reservation method consumed the in-memory capability at reservation time, leaving no retained capability evidence for a later final claim.

## Prototype

`OwnerConsentTlsAdapter.simulate_final_dispatch_admission` is a bounded, no-side-effect coordinator prototype:

1. Accepts only the exact adapter-issued opaque capability retained in the adapter's in-memory session map.
2. Requires the same concrete `SQLiteOwnerEnrollmentRegistry` object for transport-certificate and consent-key lookups, and a distinct `DurableActionReservationLedger`.
3. Revalidates the live server-side `SSLSocket`, exact TLS context, TLS version, ALPN, peer certificate, transport enrollment, adapter-issued session, monotonic session/capability deadlines, challenge identity, action, canonical arguments digest, active owner/device enrollment, credential generation and consent-key digest.
4. Creates or resumes only the exact idempotent reservation derived from that retained capability.
5. Passes a trusted, side-effect-free final guard into `claim_dispatch`. The guard is invoked after the enrollment `BEGIN IMMEDIATE` lock and action-ledger `BEGIN IMMEDIATE` transaction are held, immediately before the ledger's final clock check and `DISPATCH_STARTED` update.
6. On a successful storage claim, immediately records `FAILED_NO_EFFECT/NO_EXECUTOR_CONNECTED`. The result explicitly reports `device_actions_executed=false`.

A definitive revocation, socket/session mismatch, capability expiry or argument substitution cannot produce a successful simulated admission. A reservation that was created but fails final admission is cancelled where possible; uncertain persistence is surfaced as reconciliation-required rather than retried blindly.

## Ordering and limitations

- The enrollment writer lock is held from current enrollment validation through the action-ledger commit, preserving SEC-021A's single-host ordering against signed rotation/revocation.
- The adapter lock serializes use of the in-memory capability and prevents concurrent reuse through the same adapter instance.
- The capability's monotonic validity is checked inside the final guard; the ledger's signed epoch issue/expiry is checked again immediately afterward while both database locks remain held.
- This is a single-process/single-host prototype. It is not a distributed transaction, multi-host lock, remote attestation, or protection against malicious code already executing inside the trusted host process.
- The low-level ledger method remains a storage primitive. A successful claim without the adapter guard is not complete authorization and must never directly trigger a platform action.
- The prototype does not query Android runtime permissions, HOME role, AccessibilityService state, MediaProjection state, or device lock state.
- It does not invoke an executor, Android API, shell, listener, network endpoint or physical device.
- The authority private key and production mTLS client provisioning remain outside the repository.

## Regression cases

- Exact live capability creates a reservation, passes the final guard and ends in `FAILED_NO_EFFECT/NO_EXECUTOR_CONNECTED`.
- The same capability cannot be reused.
- Revocation after reservation but before final claim denies admission and cancels the reservation.
- Monotonic capability expiry after reservation denies admission and cancels the reservation.
- Action-argument substitution is rejected before reservation.
- A false or raising final guard fails closed and leaves the reservation RESERVED for the coordinator to reconcile/cancel.

## Acceptance gates

Exact-head Python policy, Android build/manifest checks, CI-003 independent unsigned reproducibility and QA-005 emulator workflows must pass. This does not establish Android permission control, actual device execution, spoken TalkBack, physical Pixel 9 Pro compatibility, signed release or production readiness. Independent human security review is required before any executor integration.
