# Engineering Factory Run — AGENT-004T: QA-005 wake-state readiness gate

Date: 2026-11-07  
Repository: Davidcarmelalex/MrNothing-OS  
Authorized branch: feat/phase1-agentic-phone  
Audit baseline: 38596a6b138cf039e26f244e780c63d5bd6032f7  
Current implementation scope: QA-005 workflow and static regression gate only.

## Audit

- Complete recursive tree: 329 entries; not truncated.
- Latest 20 authorized-branch commits inspected; branch is 275 commits ahead of main and zero behind.
- Six open PRs (#1 and #3–#7) inspected. PR #1 is the open/draft umbrella targeting main and matched the authorized branch head. PRs #3–#7 target separate scoped branches and were not modified.
- PROJECT-ADAPTER.md and roadmap are present. Repository SKILL.md is absent. Upstream shared package remains unverified and is not claimed installed.
- Existing architecture reviewed: native Kotlin HOME launcher; non-exported owner trust/consent/disclosure Activities; process-local accessibility/projection session registry; action-specific permission gate; Python HERMES/admission/sandbox prototypes. CommandRouter rejects requests absent a verifier-created transport session. No AccessibilityService or MediaProjection service is declared.
- PR #1 has no submitted reviews or inline review threads. Repository rulesets list is empty; branch-protection enforcement remains unverified.

## Evidence and diagnosis

Exact-head Phase 1 push/PR runs 42375117580 and 42375122847 passed. CI-003 push/PR runs 42375117743 and 42375122831 passed. QA-005 run 42375122823 failed in the disposable emulator credential preflight, before instrumentation. Artifact 13575706693 was downloaded and inspected. The screenshot and hierarchy show the Android 15 lockscreen, not the PIN bouncer. The policy snapshot reports both Keyguard visibility flags true while the display is still TURNING_ON/WAKING. The old workflow proceeded to the swipe as soon as either Keyguard flag was true. No app assertion, application crash or ANR was established; the synthetic PIN cleanup succeeded.

## Implementation

AGENT-004T:
- waits at most 20 seconds after KEYCODE_WAKEUP for dumpsys power to report both mWakefulness=Awake and mInteractive=true;
- records power-state-after-wake.txt for future diagnosis;
- requires both KeyguardServiceDelegate showing=true and KeyguardStateMonitor mIsShowing=true before the existing single bounded swipe;
- adds source-level regression assertions for the wait and operation ordering.

Only .github/workflows/qa005-emulator.yml, tests/test_qa005_workflow_gate.py, project adapter, roadmap and QA-005 evidence documentation are changed. No Android production source, manifest, permission, service, executor, CommandRouter, physical device or firmware behavior is changed.

## Validation

The pre-change exact-head evidence is listed above. Post-change Phase 1, CI-003 and QA-005 results are pending; no post-change pass is claimed. The GitHub workflow will run the Python policy suite, Android Gradle unit/debug build and independent unsigned release reproducibility. QA-005 must then complete the disposable API 35 emulator, instrumentation, launcher/recovery and downstream smoke steps. No local emulator or physical Pixel test was run in this automation environment.

## Specialist responsibilities and independent gate

- Android: lifecycle, Android permission boundaries and service integration.
- AI/agents: deterministic plans, bounded tools and supervised execution.
- Security: identity, consent, revocation, replay prevention and fail-closed policy.
- UX/accessibility: disclosure, Settings handoff, keyboard navigation and TalkBack.
- CI/QA: workflow integrity, emulator evidence, JUnit and reproducibility.
- Hardware/release: Pixel 9 Pro, StrongBox, signed release and OTA rollback.
- Independent supervisor/verifier: inspect diff and exact-head evidence; independent human security/accessibility approval remains PENDING.

## Milestones

M1 FOUNDATION — IN PROGRESS.  
M2 OS INTERFACE — IN PROGRESS.  
M3 AGENTIC INTELLIGENCE — PARTIAL.  
M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED.  
M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED.  
M6 SECURITY/PRIVACY — IN PROGRESS.  
M7 PHYSICAL HARDWARE VALIDATION — BLOCKED.  
M8 PRODUCTION READINESS — BLOCKED.

No milestone is complete.

## Next task

Accept AGENT-004T only after exact-head Phase 1 and CI-003 pass and QA-005 completes with inspected JUnit/screenshots/hierarchy. If the display fails to reach awake state, stop before any gesture and retain diagnostics. If it reaches awake but the bouncer still does not appear, diagnose the gesture using the next exact screenshot/hierarchy rather than adding speculative input. Obtain independent security/accessibility review before any AccessibilityService declaration. Keep MediaProjection separate and CommandRouter fail-closed.
