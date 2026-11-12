# AGENT-005K — time-bounded durable action admission

**Date:** 2026-11-08  
**Repository:** Davidcarmelalex/MrNothing-OS  
**Authorized branch:** feat/phase1-agentic-phone  
**Audited starting head:** 63a4d23e4d97117a342ae831600736fcd0797ae7  
**Scope:** storage-only hardening of AGENT-004H; no dispatch wiring or device side effects.

## Repository audit

- Recursive Git tree: 350 entries, not truncated.
- Recent branch commits: 20 inspected; starting head 63a4d23e4d97117a342ae831600736fcd0797ae7.
- Branch comparison: 302 commits ahead of main, 0 behind.
- Open PRs: #1, #3, #4, #5, #6 and #7. PR #1 is the only open PR whose head is the authorized branch; it targets main and remains draft. Other PRs were left untouched.
- Branch protection is disabled and no repository rulesets were returned.
- `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` exist. No repository `SKILL.md` was found. The upstream shared package remains unverified and is not claimed as installed.
- Existing Android HOME launcher, typed action arguments, action-specific `ActionPermissionGate`, process-local platform-session registry, owner-consent mTLS adapter and durable reservation ledger were reviewed.
- Exact starting-head GitHub Actions: Phase 1 push/PR, CI-003 push/PR and QA-005 PR all completed successfully (runs 42421601322, 42421605014, 42421601317, 42421604989 and 42421604994). The QA run is disposable Android 15 emulator evidence; no physical Pixel 9 Pro test is implied.

## Selected bounded task

AGENT-004H's durable ledger previously checked request shape and maximum TTL but did not enforce the stored issue/expiry window at reservation or dispatch claim. A RESERVED row could therefore be claimed after its signed expiry if a caller reached the storage API without the live adapter's separate monotonic revalidation.

The selected correction is defense in depth at the durable state machine:
- Reject reservation creation when the trusted ledger clock is before issue time or at/after expiry.
- Re-read the clock after acquiring the SQLite write transaction for both reserve and claim, avoiding stale pre-lock time.
- On an expired RESERVED row, atomically record terminal `FAILED_NO_EFFECT/CAPABILITY_EXPIRED`.
- Keep future-dated rows RESERVED but not claimable until issue time.
- Preserve one-use claim, idempotency and all existing storage semantics.

## Changes

- `core/action_reservation.py`: enforce time window during reserve and claim.
- `tests/test_action_reservation.py`: add four regression cases for expired/future reservation and claim behavior.
- `docs/AGENT-004H-DURABLE-ACTION-RESERVATION.md`: document AGENT-005K behavior and the remaining live-adapter requirement.
- `docs/ENGINEERING-FACTORY-ROADMAP.md`: record this checkpoint and retain the cross-store final-admission race as the next security task.
- `PROJECT-ADAPTER.md`: record this audit and upstream package provenance.
- This run record.

## Verification and limits

The implementation was reviewed against the existing transaction/state-machine code. No local Python interpreter or Android SDK build was available in this run; therefore no local tests are claimed. Exact-head GitHub Actions must run the full Python suite, Android Gradle/unit checks, CI-003 independent builders and QA-005 emulator workflow after the commit. The new regression tests are the acceptance evidence for the time-window behavior.

This does **not** solve the cross-store race between owner-enrollment revocation and action-reservation dispatch claim. The transport adapter still reserves only; it does not call `claim_dispatch`. The Android `CommandRouter` remains fail-closed and rejects all requests. No listener, executor, permission grant, shell bridge, accessibility service, projection service or device action was enabled.

## Specialist responsibilities

- Android: lifecycle, launcher and Android permission adapters.
- AI/agents: deterministic plans and bounded sandbox; no executor.
- Security: owner identity, consent, revocation and reservation invariants.
- UX/accessibility: TalkBack, focus, large text and owner recovery.
- CI/QA: Python/Gradle, reproducibility and emulator evidence.
- Hardware/release: Pixel 9 Pro compatibility, signing, OTA and rollback.
- Independent supervisor/verifier: separate diff, test and security review. No independent human review was available; status remains pending.

## Milestones

M1 foundation — in progress; M2 OS interface — in progress; M3 agentic intelligence — partial; M4 permission-controlled integrations — not started; M5 Pixel 9 Pro compatibility — not accepted; M6 security/privacy — in progress; M7 physical hardware validation — blocked; M8 production readiness — blocked. No milestone is complete.

## Next task

Implement and test a serializable final-admission ordering between current owner-enrollment generation/revocation and the durable reservation's DISPATCH_STARTED claim. It must establish one linearization point, fail closed on either store outage, and remain no-execution until the Android permission gate and actual platform adapter are independently reviewed.
