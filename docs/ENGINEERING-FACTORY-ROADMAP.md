# MrNothing OS — verified engineering milestones

**Audit baseline:** 2026-11-05, branch feat/phase1-agentic-phone at 4ef47ea5292efc7901cfb809a94ea873d49eb036. GitHub push/PR checks and QA-005 emulator workflow passed at this baseline. No physical Pixel 9 Pro, live command channel, custom firmware, OTA or release signing has been demonstrated.

| Gate | Owner(s) | Objective acceptance evidence | Baseline |
| --- | --- | --- | --- |
| **M1 Foundation** | CI/QA + Android | reproducible pinned build, test inventory, threat model, CI green, reviewed adapter, supervisor signoff | IN PROGRESS |
| **M2 OS interface** | Android + UX | default HOME role, app library, accessibility checks with TalkBack/large text, user-controlled stock-launcher recovery, emulator E2E | IN PROGRESS (QA-005 emulator workflow passed; TalkBack speech acceptance and hardware remain unverified) |
| **M3 Agentic intelligence** | AI/agents | authenticated deterministic plan->tool->result state machine, cancellation, injection and timeout tests, 20 sandbox scenarios | IN PROGRESS (isolated plan/consent primitives; no integrated executor) |
| **M4 Device integrations** | Android + security | opt-in permission UX, 5 supported app workflows, revocation tests, no restricted-screen bypass | NOT STARTED |
| **M5 Pixel 9 Pro compatibility** | Hardware/release | caiman build/ABI checks, vendor/boot chain analysis, modem limitations documented, recovery plan | NOT STARTED |
| **M6 Security/privacy** | Security + verifier | threat model, device-bound keys, persistent replay prevention, no high-risk findings, encryption/retention/kill-switch tests | IN PROGRESS (StrongBox/consent prototypes; independent review pending) |
| **M7 Physical hardware** | Hardware + QA | actual Pixel 9 Pro evidence: install, reboot, SIM/VoLTE, Wi-Fi/Bluetooth, battery, thermal, accessibility, rollback; separately prove two-way SIM AI audio | BLOCKED: device access |
| **M8 Production readiness** | Release + supervisor | signed reproducible artifacts, SBOM, 100 scripted scenarios, measured reliability, OTA rollback drill, privacy/legal review, independent signoff | BLOCKED by M1–M7 |

**No milestone is COMPLETE.** Estimates are not acceptance evidence. Overall completion percentages are informal planning estimates and must never replace gates.

## Highest-priority engineering backlog
1. **SEC-001**: make signed command admission fail closed with durable replay state, explicit device-key boundary, strict payload validation and restart tests. *No network exposure.*
2. **CI-002**: pin Android build tooling and add reproducibility/manifest security checks; retain debug artifact labels. **IMPLEMENTED AND CI-PASSING** at ecfbf9f (two successful runs), but independent signoff and release-grade provenance remain pending. Do not duplicate this task.
3. **UX-003**: accessible launcher and owner-controlled stock-launcher recovery. **SOURCE IMPLEMENTED** at 6cb27de with contrast, 56dp touch-target and recovery source gates; TalkBack/large-font emulator tests and independent review remain open. Do not mark M2 complete.
4. **AGENT-004**: authenticated device enrollment and revocation design, Keystore-bound keys, idempotent task executor with cancellation. AGENT-004A/B/C now provide isolated verifier, Android signer and host-side challenge-issuer primitives; persistent enrollment registry, authenticated transport integration, rate limiting and supervised executor remain open.
5. **QA-005**: Android emulator E2E launch/role tests and screenshot/accessibility evidence.
6. **HW-006**: Pixel hardware matrix, SIM audio feasibility and firmware rollback validation after hardware is available.

## Independent supervisor gate
For every PR: compare actual diff against task scope; verify tests independently; check secrets, permissions, command authorization, rollback and user consent; reject unsupported completion claims. The code author cannot self-approve. If a second reviewer is unavailable, record PENDING_INDEPENDENT_REVIEW.

## Release blocks
No root/firmware flash or production deployment from CI. No public command endpoint until identity enrollment, encryption, durable replay, revocation, rate limits, threat review and audit logging are tested. No physical-device or SIM audio claims without hardware logs.

## AGENT-013 offline plan simulator (2026-11-02)

Implemented a bounded M3 prototype at core/agent_sandbox.py with a strict 20-step limit, full preflight, explicit no-side-effect results, cancellation/deadline checks and 34 regression tests. See AGENT-013 evidence (AGENT-013-OFFLINE-PLAN-SIMULATOR.md). Local tests passed; GitHub CI and independent review are separate gates. This does not replace AGENT-004 authenticated enrollment, nor imply a production agent. The upstream shared SKILL.md remains unverified.

## AGENT-004A cross-platform consent protocol primitive (2026-11-05)

Implemented a bounded P-256 ECDSA verification primitive and matching Kotlin/Python canonical payload encoders. Both platforms consume the same Java-Properties fixture at android/app/src/test/resources/owner-consent-v1.properties. The Python verifier requires an authenticated transport, a host-issued challenge, an enrolled P-256 public key supplied by a trusted registry, exact challenge-field matching, a 30-second maximum lifetime and atomic nonce consumption through the existing SQLite replay ledger.

This is not yet Android signing, challenge issuance, key registry integration, permission granting or command execution. The existing HMAC consent verifier remains a separate offline prototype. See AGENT-004A-CONSENT-PROTOCOL.md. Keep M3 partial and M6 in progress until Android per-use signing, host challenge provenance, supervised integration and independent security review pass. The upstream shared SKILL.md remains unverified.

## AGENT-004B AndroidKeyStore per-use signing primitive (2026-11-05)

Added an isolated Android signer that loads only the existing StrongBox-backed owner-key alias, prepares SHA256withECDSA, binds the operation to the framework BiometricPrompt.CryptoObject, requires strong biometric or device-credential authentication, rechecks device safety, locally verifies the resulting signature and emits the AGENT-004A envelope. Cancellation and all failures refuse; no software-key or key-generation fallback exists.

The source manifest now declares only android.permission.USE_BIOMETRIC; the manifest gate explicitly allowlists that one permission and rejects duplicates or all unreviewed permissions. JVM tests cover canonical envelope formatting and synthetic DER bounds; Python source tests guard the StrongBox/CryptoObject/no-executor boundary.

This is not a production consent flow: no host challenge issuer, trusted registry, authenticated transport, caller integration, permission grant or command execution exists. The signed-64-bit parity correction remains in open draft PR #7 and is not part of this branch baseline. Physical StrongBox/Pixel validation and independent review remain pending. Keep M3 partial and M6 in progress.


## AGENT-004C host-side owner-consent challenge issuer prototype (2026-11-05)

Added core/owner_consent_issuer.py as a bounded library primitive. It creates a 128-bit secrets-based nonce, validates a live host-authenticated session assertion against a read-only enrolled-device registry, validates canonical P-256 SPKI DER, binds owner/device/session/action/time, limits challenge lifetime to 30 seconds and caps expiry at the session expiry. It returns the trusted registry public key for the host verifier and does not execute actions.

Eleven focused tests cover successful issuance, nonce format, session expiry capping, signed-64-bit boundary behavior, invalid/future/expired sessions, invalid clock and action, nonce-source failure, unknown/inactive/mismatched device records, registry failure and RSA/P-384/malformed public keys.

The session object is not cryptographically unforgeable; its provenance depends on a trusted transport adapter. The registry is an interface, not a persistent enrollment implementation. No authenticated network endpoint, attestation-chain validation, rate limiter, audit log, Android caller integration, permission grant or command execution was added. The issuer is stateless; the existing SQLite replay ledger remains responsible for atomic one-use consumption. Keep M3 partial and M6 in progress pending integration and independent security review. The upstream shared SKILL.md remains unverified.
