# AGENT-005L — lock-coupled final dispatch admission

**Date:** 2026-11-08  
**Repository:** Davidcarmelalex/MrNothing-OS  
**Authorized branch:** feat/phase1-agentic-phone  
**Audited starting head:** 7bf32e5f45e5d8ee0cfd013706ead4c88fe92849  
**Scope:** single-host ordering between enrollment revocation/rotation and the durable DISPATCH_STARTED claim; no device execution.

## Repository audit

- Complete recursive tree: 351 entries, not truncated.
- Recent branch commits: 20 inspected; starting head 7bf32e5f45e5d8ee0cfd013706ead4c88fe92849.
- Branch comparison: 303 commits ahead of main, zero behind.
- Open PRs: #1, #3, #4, #5, #6 and #7. PR #1 matches the authorized branch, targets main and remains draft; it has no submitted reviews or inline review threads. Other PRs were not modified.
- Branch protection is disabled and repository rulesets are empty.
- PROJECT-ADAPTER.md and the engineering roadmap exist. No repository SKILL.md exists. The upstream shared package remains unverified and is not claimed as installed.
- Existing SEC-019A already serializes consent-nonce consumption with enrollment rotation/revocation in the owner registry. The separate action reservation ledger's final dispatch claim was not covered by that transaction.
- Exact starting-head Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR workflows all completed successfully. QA-005 passed 30/30 instrumentation tests on a disposable Android API 35 x86_64 emulator. Spoken TalkBack and physical Pixel 9 Pro validation remain unverified.

## Selected bounded task

AGENT-005K explicitly left a cross-store race: owner enrollment/revocation lives in one SQLite database while action reservations and DISPATCH_STARTED live in another. A read-only enrollment lookup followed by a separate ledger claim permits revocation to commit between the two operations.

## Implementation

- Added SQLiteOwnerEnrollmentRegistry.hold_active_enrollment_for_dispatch(...). It acquires BEGIN IMMEDIATE on the enrollment database, checks the exact active owner/device, transport-certificate fingerprint, credential generation and consent-key digest, and holds the writer lock through the caller's ledger transaction.
- Changed DurableActionReservationLedger.claim_dispatch(...) to require the exact SQLiteOwnerEnrollmentRegistry instance. It reads the reservation binding, acquires the enrollment lock, re-reads the immutable binding under the ledger's own BEGIN IMMEDIATE transaction, checks the signed time window, and commits DISPATCH_STARTED before releasing the enrollment lock.
- Signed enrollment rotation/revocation already uses BEGIN IMMEDIATE on the same enrollment database. Thus a revocation/rotation committed first is observed and denied; a claim that holds the enrollment lock first commits DISPATCH_STARTED before a later revocation can commit.
- Direct claim without an enrollment registry is no longer accepted. Both stores fail closed. If the ledger claim commits but the enrollment context cannot cleanly close, the method returns ENROLLMENT_LOCK_COMMIT_UNCERTAIN and never authorizes dispatch.

This is single-host lock coupling, not a distributed transaction or multi-host guarantee. It does not validate the exact live TLS socket/monotonic session, query Android permissions, or execute any device action. The executor remains disconnected.

## Regression coverage

Four integration tests were added:
1. Revocation committed before claim denies and leaves the reservation RESERVED.
2. Credential rotation committed before claim denies the old generation.
3. A real two-thread race proves revocation blocks while the claim holds the enrollment writer lock, then commits after DISPATCH_STARTED.
4. Missing/corrupt enrollment storage fails closed and leaves the reservation RESERVED.

The reservation state-machine tests now use a real signed test enrollment fixture so every successful claim exercises the registry gate.

## Verification and limits

At submission, exact-head Phase 1 push/PR, CI-003 independent-runner push/PR and QA-005 emulator workflows are pending. No local Python interpreter/Gradle/Android SDK test execution is claimed in this run. The GitHub Actions exact-head runs are the acceptance source.

Independent source review was performed against the lock order, transaction boundaries, exception paths and regression tests. Independent human security review remains PENDING. No production executor, listener, permission grant, shell bridge, AccessibilityService, MediaProjection service, physical device, signing key or OTA path was enabled.

## Specialist responsibilities

- Android: launcher, lifecycle, platform permissions and future typed adapters.
- AI/agents: bounded planning, supervised policy and cancellation.
- Security: enrollment, consent, revocation, replay and final admission.
- UX/accessibility: TalkBack, focus, large text and owner recovery.
- CI/QA: Python, Gradle, static security, emulator and reproducibility evidence.
- Hardware/release: Pixel 9 Pro, StrongBox, signing, OTA and rollback.
- Independent supervisor/verifier: separate review and acceptance; human approval remains pending.

## Milestones

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete.

## Next task

Implement the final trusted coordinator that combines the live TLS socket/session and monotonic capability validation with this lock-coupled claim, then performs fresh action-specific Android permission checks before any platform invocation. Keep the executor disconnected until independent security review approves the complete ordering and all failure/recovery cases.
