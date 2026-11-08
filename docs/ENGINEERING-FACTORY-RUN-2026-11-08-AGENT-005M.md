# AGENT-005M — live-capability final-admission simulation

**Date:** 2026-11-08  
**Repository:** Davidcarmelalex/MrNothing-OS  
**Authorized branch:** feat/phase1-agentic-phone  
**Audited starting head:** fd819d852148232f8974eed3997bccd78a9a7dd0  
**Scope:** bind adapter-retained live TLS/owner-consent capability evidence to the SEC-021A lock-coupled final claim, without executing a device action.

## Repository audit

- Complete recursive feature-branch tree: 353 entries; not truncated.
- Recent commits: 20 inspected. Latest starting commit: `fd819d852148232f8974eed3997bccd78a9a7dd0`.
- Branch comparison: 304 commits ahead of main, zero behind.
- Open PRs: #1, #3, #4, #5, #6 and #7. PR #1 matches the authorized branch, targets main and remains draft; it has zero submitted reviews and zero inline review threads. Other PRs were not modified.
- Branch protection is disabled; no repository rulesets were found.
- `PROJECT-ADAPTER.md` and the roadmap exist. No repository `SKILL.md` exists. The upstream shared factory package remains unverified and is not claimed as installed.
- Architecture includes the Kotlin HOME launcher, isolated Android trust/consent UI, Python mTLS consent adapter, signed SQLite owner/device registry, durable action reservation ledger, and no-op executor. The production command router remains fail-closed; no real executor is connected.
- Starting-head Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR all passed. Both Python policy jobs reported 745 tests passed. QA-005 completed on a disposable Android 15 API 35 x86_64 emulator; QA-011 reported `blocked_service_disabled`, and QA-012 remained structural only. CI-003 reported byte-identical unsigned APKs (7,862,996 bytes; SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`) and `release_ready=false`.

## Selected task

AGENT-005L closed the cross-store enrollment-revocation/dispatch-claim race, but the action ledger could still be claimed without revalidating the adapter-retained exact live TLS session and capability. The previous reservation method consumed the capability at reservation time, so no live evidence remained for a later final claim.

## Implementation

- Added an optional trusted final-admission guard to `DurableActionReservationLedger.claim_dispatch`. When supplied, it runs after both SQLite writer locks and the reservation binding re-read, immediately before the final signed-time check and DISPATCH_STARTED update. False, non-boolean and raising guards fail closed.
- Added `OwnerConsentTlsAdapter.simulate_final_dispatch_admission`. It requires the exact adapter-retained capability, the same concrete SQLite registry object for transport and consent lookup, and a distinct reservation ledger.
- The method binds owner/device/session, nonce, protocol version, action, canonical argument digest, transport certificate fingerprint, credential generation and consent-key digest to the durable reservation.
- The final guard rechecks the exact live TLS socket, TLS context/version/ALPN, enrolled peer certificate, adapter session, monotonic session/capability deadlines, challenge, action/arguments and current paired enrollment while the enrollment writer lock and reservation-ledger transaction are held.
- A successful claim is immediately terminalized as `FAILED_NO_EFFECT/NO_EXECUTOR_CONNECTED`. This is an admission simulation only; no Android permission check, executor, shell, listener, network endpoint or device action is invoked.
- Definitive failure after reservation cancels the reservation when possible. Transient storage/registry/clock errors remain fail-closed and are surfaced for retry/reconciliation without assuming success.

## Regression coverage added

- Two storage tests: false guard rejection and exception fail-closed.
- Four mTLS integration tests: successful live-capability simulation with no effect; revocation after reservation but before final claim; monotonic capability expiry after reservation; argument substitution before reservation.
- The test fixture uses ephemeral software keys and synthetic local mTLS certificates only.

## Verification and limits

- The container could not clone GitHub because outbound DNS/network access was unavailable. No local Python, Gradle or emulator execution is claimed for this run.
- The exact-head GitHub Actions runs after this commit are the acceptance source.
- The final guard is a trusted in-process callback, not a boundary against malicious code already executing in the host process.
- This remains single-host SQLite lock coupling. It is not distributed/multi-host atomicity.
- Android runtime permissions, HOME role, AccessibilityService, MediaProjection and device-lock state are not queried.
- No physical Pixel 9 Pro, spoken TalkBack acceptance, signed production artifact or OTA rollback was tested.

## Specialist responsibilities

- Android: launcher, lifecycle and typed platform permission probes.
- AI/agents: deterministic plans, bounded tools and cancellation.
- Security: owner identity, consent, replay, revocation and final admission.
- UX/accessibility: TalkBack, focus, large text and recovery.
- CI/QA: exact-head Python, Gradle, manifest, emulator and reproducibility evidence.
- Hardware/release: Pixel 9 Pro, StrongBox, signing and OTA.
- Independent supervisor/verifier: separate review of diff and evidence; human security approval remains PENDING.

## Milestones

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete.

## Next task

Implement the action-specific Android permission/role preflight as a separate, typed, fail-closed coordinator stage. It must run after final live-capability validation but before any platform invocation, bind the exact action to the exact permission state, re-read permission state at the final invocation boundary, and require user-visible revocation. Keep the executor disconnected until independent human security review approves the complete flow.
