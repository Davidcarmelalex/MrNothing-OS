# Engineering Factory run — AGENT-004X: QA-005 wake-age parser correction

**Date:** 2026-11-07  
**Repository:** Davidcarmelalex/MrNothing-OS  
**Authorized branch:** feat/phase1-agentic-phone  
**Audit head:** 0ffb78dfacf09b2856c836e4ee631e70b389425f  
**Scope:** QA-only Android 15 disposable-emulator wake preflight.

## Repository audit

- Complete recursive tree: 333 entries; not truncated.
- Latest 20 authorized-branch commits inspected.
- Branch comparison: 279 commits ahead of main, 0 behind.
- Six open PRs: #1 and #3–#7. PR #1 is open/draft, targets main, and matched the authorized branch head. PRs #3–#7 were left untouched.
- PR #1 had no submitted reviews or inline review threads.
- Branch metadata reports protected=false; rulesets were empty. Branch-protection enforcement remains unverified.
- PROJECT-ADAPTER.md and docs/ENGINEERING-FACTORY-ROADMAP.md exist. Repository SKILL.md is absent. The upstream shared package remains unverified and is not claimed installed.

## Exact-head CI before this correction

- Phase 1 push [42383275068](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383275068): passed.
- Phase 1 PR [42383280140](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280140): passed; Python policy ran 703 tests; Android debug unit/build, repeat APK comparison, strict dependency verification, modified-dependency negative control and manifest security gate passed.
- CI-003 push [42383275207](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383275207): passed.
- CI-003 PR [42383280178](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280178): passed; independent unsigned release build/reproducibility verifier passed. Artifacts remain unsigned and are not release-ready.

## QA-005 failure evidence

QA-005 PR [42383280219](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280219) booted the disposable API 35 emulator, built the debug APK and passed the Gradle negative control, then failed before instrumentation in the wake-age preflight.

Artifact [13578492527](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280219/artifacts/13578492527) shows:

- mWakefulness=Awake
- mWakefulnessChanging=false
- mHalInteractiveModeEnabled=true
- mLastWakeTime=32654 (22892 ms ago)
- Screenshot: illuminated Android lockscreen.
- Last-ANR report: no ANR since boot.
- Synthetic emulator PIN: successfully cleared by EXIT cleanup.

The shell source double-escaped the GNU sed ERE grouping and back-reference, so it could not extract the valid wake age. The snapshot writer also used a double-escaped newline format.

## Implementation

- Corrected the sed expression to single-escaped literal parentheses and capture back-reference.
- Corrected the after-wake snapshot writer to printf with a real newline.
- Added exact-expression regression coverage for a valid Android 15 dump, a below-threshold age, missing/malformed age and snapshot newline escaping.
- No production Android source, manifest, permissions, services, owner consent, CommandRouter, executor, physical-device or release behavior changed.

## Acceptance

Post-change exact-head Phase 1, CI-003 and QA-005 runs are required. Emulator acceptance is not claimed. Independent human security/accessibility review remains pending.

## Milestones

| Milestone | Status |
|---|---|
| M1 Foundation | In progress |
| M2 OS interface | In progress |
| M3 Agentic intelligence | Partial |
| M4 Permission-controlled integrations | Not started |
| M5 Pixel 9 Pro compatibility | Not accepted |
| M6 Security/privacy | In progress |
| M7 Physical hardware validation | Blocked |
| M8 Production readiness | Blocked |

No milestone is complete.

## Next task

Verify the parser regression tests and exact-head Phase 1/CI-003, then inspect full QA-005 emulator and JUnit evidence. Do not add an AccessibilityService declaration, connect MediaProjection or enable real agent dispatch until emulator acceptance and independent security/accessibility review pass. CommandRouter remains fail-closed.
