# MrNothing OS — verified engineering milestones

**Audit baseline:** 2026-11-02, branch `feat/phase1-agentic-phone` at `f159e1461d829517f57c0b05825962c4458219ad`. The existing PR #1 was draft; GitHub CI at this baseline passed Android debug compilation/unit tests and Python preflight. No emulator, physical Pixel, live command channel, custom firmware, OTA or release signing has been demonstrated.

| Gate | Owner(s) | Objective acceptance evidence | Baseline |
| --- | --- | --- | --- |
| **M1 Foundation** | CI/QA + Android | reproducible pinned build, test inventory, threat model, CI green, reviewed adapter, supervisor signoff | IN PROGRESS |
| **M2 OS interface** | Android + UX | default HOME role, app library, accessibility checks with TalkBack/large text, user-controlled stock-launcher recovery, emulator E2E | IN PROGRESS (source only) |
| **M3 Agentic intelligence** | AI/agents | authenticated deterministic plan->tool->result state machine, cancellation, injection and timeout tests, 20 sandbox scenarios | NOT STARTED (policy prototypes only) |
| **M4 Device integrations** | Android + security | opt-in permission UX, 5 supported app workflows, revocation tests, no restricted-screen bypass | NOT STARTED |
| **M5 Pixel 9 Pro compatibility** | Hardware/release | `caiman` build/ABI checks, vendor/boot chain analysis, modem limitations documented, recovery plan | NOT STARTED |
| **M6 Security/privacy** | Security + verifier | threat model, device-bound keys, persistent replay prevention, no high-risk findings, encryption/retention/kill-switch tests | IN PROGRESS (prototype only) |
| **M7 Physical hardware** | Hardware + QA | actual Pixel 9 Pro evidence: install, reboot, SIM/VoLTE, Wi-Fi/Bluetooth, battery, thermal, accessibility, rollback; separately prove two-way SIM AI audio | BLOCKED: device access |
| **M8 Production readiness** | Release + supervisor | signed reproducible artifacts, SBOM, 100 scripted scenarios, measured reliability, OTA rollback drill, privacy/legal review, independent signoff | BLOCKED by M1–M7 |

**No milestone is COMPLETE.** Estimates are not acceptance evidence. Overall completion percentages are informal planning estimates and must never replace gates.

## Highest-priority engineering backlog
1. **SEC-001**: make signed command admission fail closed with durable replay state, explicit device-key boundary, strict payload validation and restart tests. *No network exposure.*
2. **CI-002**: pin Android build tooling and add reproducibility/manifest security checks; retain debug artifact labels. **IMPLEMENTED AND CI-PASSING** at `ecfbf9f` (two successful runs), but independent signoff and release-grade provenance remain pending. Do not duplicate this task.
3. **UX-003**: accessible launcher and owner-controlled stock-launcher recovery. **SOURCE IMPLEMENTED** at `6cb27de` with contrast, 56dp touch-target and recovery source gates; TalkBack/large-font emulator tests and independent review remain open. Do not mark M2 complete.
4. **AGENT-004**: authenticated device enrollment and revocation design, Keystore-bound keys, idempotent task executor with cancellation.
5. **QA-005**: Android emulator E2E launch/role tests and screenshot/accessibility evidence.
6. **HW-006**: Pixel hardware matrix, SIM audio feasibility and firmware rollback validation after hardware is available.

## Independent supervisor gate
For every PR: compare actual diff against task scope; verify tests independently; check secrets, permissions, command authorization, rollback and user consent; reject unsupported completion claims. The code author cannot self-approve. If a second reviewer is unavailable, record `PENDING_INDEPENDENT_REVIEW`.

## Release blocks
No root/firmware flash or production deployment from CI. No public command endpoint until identity enrollment, encryption, durable replay, revocation, rate limits, threat review and audit logging are tested. No physical-device or SIM audio claims without hardware logs.

## AGENT-013 offline plan simulator (2026-11-02)

Implemented a bounded M3 prototype at `core/agent_sandbox.py` with a strict 20-step limit, full preflight, explicit no-side-effect results, cancellation/deadline checks and 34 regression tests. See [AGENT-013 evidence](AGENT-013-OFFLINE-PLAN-SIMULATOR.md). Local tests passed; GitHub CI and independent review are separate gates. This does not replace AGENT-004 authenticated enrollment, nor imply a production agent. The upstream shared `SKILL.md` remains unverified.

## AGENT-004A cross-platform consent protocol primitive (2026-11-05)

Implemented a bounded P-256 ECDSA verification primitive and matching Kotlin/Python canonical payload encoders. Both platforms consume the same Java-Properties fixture at `android/app/src/test/resources/owner-consent-v1.properties`. The Python verifier requires an authenticated transport, a host-issued challenge, an enrolled P-256 public key supplied by a trusted registry, exact challenge-field matching, a 30-second maximum lifetime and atomic nonce consumption through the existing SQLite replay ledger.

This is not yet Android signing, challenge issuance, key registry integration, permission granting or command execution. The existing HMAC consent verifier remains a separate offline prototype. See [AGENT-004A protocol contract](AGENT-004A-CONSENT-PROTOCOL.md). Keep M3 partial and M6 in progress until Android per-use signing, host challenge provenance, supervised integration and independent security review pass. The upstream shared `SKILL.md` remains unverified.
