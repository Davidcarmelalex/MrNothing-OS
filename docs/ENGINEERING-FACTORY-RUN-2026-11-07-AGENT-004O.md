# Engineering Factory Run — AGENT-004O: QA-005 keyguard transition race

Date: 2026-11-07  
Repository: Davidcarmelalex/MrNothing-OS  
Authorized branch: feat/phase1-agentic-phone  
Audit head: 57d70638a78e4c8864f1528fd6bebed2df420cf6

## Repository and governance audit

- Recursive Git tree: 322 entries; truncated=false.
- Latest 20 branch commits inspected.
- Compare against main: 267 commits ahead, zero behind; merge base f3c9a701d2a337de8ef393ac14df044a79843d60.
- Six open PRs: #1, #3, #4, #5, #6 and #7. Only PR #1 targets main; it is open/draft and its head matches the authorized branch. PRs #3–#7 were inspected and left untouched.
- PR #1 has zero submitted reviews and zero inline review threads. Branch-protection enforcement is not established: repository rulesets were empty and the connected integration could not verify the protection endpoint.
- PROJECT-ADAPTER.md and docs/ENGINEERING-FACTORY-ROADMAP.md exist. Repository SKILL.md is absent. The authorized upstream shared factory package remains unverified and is not claimed as installed.

## Exact-head CI audit at the baseline

- Phase 1 push 42360496305 and PR 42360499894 passed. Each Python policy run passed 680 tests. Android debug unit tests/build, repeat debug APK comparison, strict dependency verification and modified-dependency negative control passed.
- CI-003 push 42360496250 and PR 42360499926 passed both independent builders and the verifier. The unsigned APKs were byte-identical; provenance correctly reported release_ready=false.
- QA-005 PR 42360499918, attempt 2, failed in the disposable-emulator credential precondition before instrumentation. Artifact 13571292518 was downloaded and inspected.

## Root cause established from runtime evidence

The pre-instrumentation Keyguard snapshot recorded KeyguardServiceDelegate showing=false and KeyguardStateMonitor mIsShowing=false. The post-wait snapshot recorded both as true. The old script sampled too early, treated the transient unlocked state as final, skipped synthetic PIN entry, and then waited for the state to become unlocked while Keyguard was now showing. The failure was in the emulator harness state transition; no app test had started and no product crash/assertion was recorded.

## Bounded implementation

The QA-005 workflow now forces a deterministic disposable-emulator sleep/wake transition after setting the synthetic test PIN:

1. Send KEYCODE_SLEEP using ordinary ADB shell.
2. Poll dumpsys power with a deadline and require a non-interactive/asleep state.
3. Send KEYCODE_WAKEUP.
4. Poll dumpsys window policy with a deadline and require a positive Keyguard-showing state.
5. Only then swipe and enter the synthetic PIN; require both Keyguard state fields to report hidden before instrumentation.
6. Preserve the existing EXIT trap that captures failure evidence and clears the synthetic PIN.

Power and post-wake Keyguard snapshots are retained in the QA artifact. The static Python gate now asserts this ordering and rejects the previous transient-unlocked shortcut.

## Safety and scope

- Only QA workflow, static workflow tests, QA evidence documentation, adapter/roadmap records and this run report are changed.
- No production Android source or manifest change.
- No AccessibilityService or MediaProjection declaration.
- No permission prompt/grant, screen capture, gesture, device action, shell bridge or CommandRouter connection.
- No adb root; emulator shell remains UID 2000.
- No physical Pixel 9 Pro, firmware flash, OTA, signing-key use, deployment or merge.

## Specialist responsibilities and independent gate

Android owns platform lifecycle; AI/agents owns action schemas and supervised planning; Security owns consent/revocation/fail-closed review; UX/accessibility owns disclosure and TalkBack acceptance; CI/QA owns instrumentation and reproducibility; Hardware/release owns Pixel 9 Pro, StrongBox, signing and OTA. The independent supervisor must inspect exact-head diffs and runtime evidence. No independent human security/accessibility approval has been submitted.

## Milestones

M1 Foundation — IN PROGRESS.  
M2 OS interface — IN PROGRESS.  
M3 Agentic intelligence — PARTIAL.  
M4 Permission-controlled integrations — NOT STARTED.  
M5 Pixel 9 Pro compatibility — NOT ACCEPTED.  
M6 Security/privacy — IN PROGRESS.  
M7 Physical hardware validation — BLOCKED.  
M8 Production readiness — BLOCKED.

No milestone is complete. Current-head CI after this change is required; emulator acceptance remains open until the new QA-005 exact-head run passes and its evidence is inspected.

Next task: accept the keyguard harness correction only on exact-head QA-005 evidence; then complete owner-visible AccessibilityService lifecycle review before any service declaration. Keep MediaProjection separate and CommandRouter fail-closed.
