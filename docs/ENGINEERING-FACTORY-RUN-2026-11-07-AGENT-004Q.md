# Engineering Factory Run — AGENT-004Q: repair exact-head QA-005 preflight wiring

Date: 2026-11-07  
Repository: Davidcarmelalex/MrNothing-OS  
Authorized branch: feat/phase1-agentic-phone  
Audit baseline: 11cd5ae4ca0d84aabd146c04dcd40d990c613fd9

## Audit and current evidence

- Complete recursive tree: 326 entries; not truncated.
- Latest 20 commits on the authorized branch inspected. Branch comparison with main: 269 ahead, 0 behind; merge base f3c9a701d2a337de8ef393ac14df044a79843d60.
- Six open PRs (#1 and #3–#7) inspected. PR #1 is the existing open draft umbrella targeting main; its head matched the authorized branch at audit time. No submitted PR reviews or inline review threads. Other PRs were left untouched.
- PROJECT-ADAPTER.md and docs/ENGINEERING-FACTORY-ROADMAP.md are present. Repository SKILL.md is absent. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed.
- Branch API reports protected=false; repository rulesets are empty. Branch-protection enforcement remains unverified.
- Current-head Phase 1 push 42370252796 and PR 42370256677 failed in Python policy after 690 tests because test_keyguard_unlock_uses_exact_systemui_resource_ids_without_text_injection expected the package-qualified key ID to be built through SYSTEM_UI, while the helper duplicated the package literal. Android debug build/unit tests passed in both jobs.
- Current-head CI-003 push 42370252811 and PR 42370256658 passed both independent unsigned release builders and the reproducibility verifier.
- Current-head QA-005 42370256924 reached the disposable API 35 emulator, configured and observed the synthetic PIN keypad, then failed before instrumentation because the step runs with working directory android/ but invoked scripts/qa005_unlock_keyguard.py as if it were at the repository root. The shell variable TEST_PIN=2468 was not exported to the helper process, which would have caused a second fail-closed refusal after the path was corrected.

## Selected task and implementation

The highest-priority bounded task was to repair these two exact-head QA regressions without touching production Android behavior.

1. Build KEY_IDS with f"{SYSTEM_UI}:id/key{digit}", matching the source guard and avoiding a duplicated package literal.
2. Invoke the helper from the step's actual android/ working directory using ../scripts/qa005_unlock_keyguard.py.
3. Pass the synthetic disposable-emulator PIN only through the helper process environment using TEST_PIN="$TEST_PIN"; it is not placed in command arguments or printed.
4. Extend the QA workflow source guard to assert the working-directory assumption, synthetic PIN setup, corrected relative helper path and environment handoff.

The helper remains restricted to an emulator-* serial and ordinary ADB shell UID 2000. It requires the exact visible SystemUI PIN view/container and unique enabled/clickable, display-bounded key controls before tapping. No root or physical-device target is permitted.

## Safety and architecture review

Only QA helper wiring, static QA tests and engineering documentation change. No production Android source, manifest, permission, AccessibilityService, MediaProjection service, owner-consent protocol, CommandRouter, executor, physical-device operation, firmware, OTA or deployment is changed. The synthetic test PIN is confined to the disposable emulator and is cleared by the existing EXIT cleanup trap. CommandRouter remains fail-closed.

## Validation status

The pre-fix evidence is explicit: 690 Python tests ran with one source-guard failure; Android debug build/unit/dependency gates passed; CI-003 reproducibility passed; QA-005 failed at helper process launch before instrumentation. After this correction, exact-head Phase 1, CI-003 and QA-005 runs are required. No post-fix test pass or emulator acceptance is claimed in this record.

## Specialist ownership and independent gates

- Android: platform and lifecycle boundaries; no production Android change in this run.
- AI/agents: supervised plans and closed action schemas; real dispatch remains disabled.
- Security: owner consent, key/device binding, replay and revocation.
- UX/accessibility: disclosure, Settings handoff, TalkBack and keyboard acceptance.
- CI/QA: source guards, Android builds, disposable emulator and reproducibility.
- Hardware/release: Pixel 9 Pro, StrongBox, signing and OTA.
- Independent supervisor/verifier: exact-head diff, CI artifacts, test outcomes and security boundary review. Independent human security/accessibility approval remains pending.

## Milestones

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete.

## Next task

Obtain exact-head green Phase 1 and CI-003, then inspect the new QA-005 emulator artifact and require complete JUnit/instrumentation plus launcher/recovery smoke acceptance. Only after independent security/accessibility review may the team consider a narrowly scoped AccessibilityService declaration. MediaProjection remains a separate workstream.
