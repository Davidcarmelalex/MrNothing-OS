# Engineering Factory Run — AGENT-004R: fresh SystemUI hierarchy acquisition

Date: 2026-11-07  
Repository: Davidcarmelalex/MrNothing-OS  
Authorized branch: feat/phase1-agentic-phone  
Audit baseline: 7180daeb44908bcea1c83ef4a4753b6ec059c8bb

## Audit and evidence

- Complete recursive tree at the baseline: 326 entries, not truncated.
- Latest 20 branch commits inspected; 270 commits ahead of main, zero behind; merge base f3c9a701d2a337de8ef393ac14df044a79843d60.
- Six open PRs (#1 and #3–#7) inspected. PR #1 remains the open draft umbrella targeting main and matched the authorized branch. No submitted reviews or inline review threads; other PRs untouched.
- PROJECT-ADAPTER.md and roadmap are present. Repository SKILL.md is absent. The authorized Library title search found no supplied shared SKILL.md or PROJECT-ADAPTER.md package; the upstream shared package remains unverified and is not claimed installed.
- Branch metadata reports protected=false; repository rulesets are empty. Branch-protection enforcement remains unverified.
- On exact head 7180daeb, Phase 1 push [42370939857](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42370939857) and PR [42370944187](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42370944187) passed: each Python policy run reported 690 tests passed; Android debug unit/build/dependency gates passed.
- CI-003 push [42370939860](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42370939860) and PR [42370944158](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42370944158) passed both independent unsigned release builders and verifier.
- QA-005 [42370944161](https://github.com/Davidcarmelalex/MrNothing-OS/MrNothing-OS/actions/runs/42370944161) booted the disposable API 35 emulator, passed debug build and dependency negative control, and reached the SEC-020B4D synthetic credential preflight. The helper path and TEST_PIN environment handoff were correct. The step then failed at UIAutomator hierarchy acquisition with the captured diagnostic ERROR: null root node returned by UiTestAutomationBridge.; the subsequent adb pull found no remote XML. Artifact 13573334800 was downloaded and inspected. The screenshot showed the lockscreen, not the PIN keypad. No instrumentation test started; last-anr reported no ANR; no application crash was established.

## Selected task and implementation

The highest-priority bounded task is to make the QA-only SystemUI hierarchy acquisition fresh, observable and bounded, without guessed coordinates or changes to production Android behavior.

1. Move hierarchy capture into the QA-only Python helper.
2. Remove a unique remote destination before every attempt and use a distinct filename per attempt, preventing stale XML reuse.
3. Require the exact UIAutomator success marker for that exact destination before pulling it.
4. Retry only the observed null-root diagnostic, with a maximum of five attempts and a one-second delay. Other errors fail closed immediately.
5. Pull the fresh XML, require a non-empty local file and run the existing exact SystemUI package/resource-id/clickability/bounds parser before tapping.
6. Add unit tests for null-root retry, unique paths, fail-closed non-null-root errors and the hard retry limit.
7. Update workflow source guards and allow a bounded 120-second helper invocation.

## Safety and architecture review

The helper still refuses non-emulator serials and any identity other than ordinary ADB shell UID 2000. It uses only exact, visible SystemUI resource IDs and validated on-screen bounds; it does not use guessed keypad coordinates, text injection, adb root or real-device access. The synthetic PIN remains in the helper process environment, is never printed or passed in argv, and the existing EXIT cleanup trap clears it.

Only QA helper/workflow/tests/documentation change. No production Android source, manifest, permissions, AccessibilityService, MediaProjection service, CommandRouter, executor, owner-consent protocol, physical device, firmware, OTA or deployment changes. CommandRouter remains fail-closed.

## Validation status

At the baseline, Phase 1 passed 690 Python tests on push and PR, Android debug tests/build passed, and CI-003 passed independent unsigned release reproducibility. QA-005 did not reach instrumentation. Post-fix exact-head Phase 1, CI-003 and QA-005 results are required; no post-fix pass is claimed here.

## Specialist ownership

Android: platform and lifecycle boundaries. AI/agents: supervised planning and action schemas. Security: consent, identity, replay and revocation. UX/accessibility: disclosure, Settings handoff and TalkBack. CI/QA: bounded instrumentation and artifact verification. Hardware/release: Pixel 9 Pro, StrongBox, signing and OTA. Independent supervisor: exact-head diff, artifact inspection and separate acceptance decision. Independent human security/accessibility review remains pending.

## Milestones

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete.

## Next task

Verify exact-head Phase 1 and CI-003, then inspect the new QA-005 artifact. Require complete instrumentation/JUnit, launcher/recovery, accessibility and credential-prompt steps. Only after independent security/accessibility review may a narrowly scoped AccessibilityService declaration be considered. MediaProjection remains separate.
