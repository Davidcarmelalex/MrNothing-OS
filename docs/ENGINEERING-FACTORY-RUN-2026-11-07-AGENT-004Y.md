# Engineering Factory run — AGENT-004Y: QA-005 parser integration and lockscreen gesture boundary

**Date:** 2026-11-07  
**Repository:** Davidcarmelalex/MrNothing-OS  
**Authorized branch:** feat/phase1-agentic-phone  
**Audit baseline:** ae1285119b63253cd04186fb23cfd84928ea8513

## Repository audit

- Recursive tree: 336 entries; not truncated.
- Latest 20 branch commits inspected; 280 commits ahead of main, 0 behind.
- Six open PRs (#1 and #3–#7). PR #1 remains open/draft against main and matched the authorized branch. It has no submitted reviews or inline review threads; other PR branches were not modified.
- PROJECT-ADAPTER.md and roadmap exist. Repository SKILL.md is absent. Upstream shared package remains unverified and is not claimed installed.
- Branch metadata reports protected=false; rulesets were empty. Protection enforcement remains unverified.

## Exact-head CI before AGENT-004Y

- Phase 1 push [42384024809](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384024809) and PR [42384029041](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384029041) passed. PR Python policy ran 717 tests; Android debug unit/build, repeat APK comparison, strict dependency verification, modified-dependency negative control and manifest security gate passed.
- CI-003 push [42384024664](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384024664) and PR [42384029055](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384029055) passed independent unsigned release builds and cross-runner verification.
- QA-005 PR [42384029065](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384029065) failed before instrumentation after the one bottom-edge swipe. Artifact [13579091222](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384029065/artifacts/13579091222) shows a settled awake display, Keyguard still showing, lockscreen hierarchy and no PIN keypad. Last-ANR reports no ANR; synthetic emulator PIN cleanup succeeded.

## Evidence and decision

The AGENT-004X wake-age correction worked: the Android 15 snapshot had mWakefulness=Awake, mWakefulnessChanging=false, mHalInteractiveModeEnabled=true and a 2,541 ms wake age. The remaining failure is the gesture-to-bouncer handoff, not the PowerManager parser.

The prior exact-node tap attempt also failed. The current artifact's lockscreen hierarchy exposes the exact locked-state device-entry icon, but not the PIN keypad. Logcat records showGestureNav shortly after the bottom-edge swipe. That is a clue, not a proven interception cause.

## Implementation

- Wire the already unit-tested scripts/qa005_power_state.py into the actual wake loop and final diagnostic; remove the duplicate sed parser.
- Capture secure navigation_mode read-only in the QA evidence artifact.
- Move the single workflow swipe start from 120 px to 180 px above the bottom edge; keep the same mid-screen destination and 450 ms duration. This is a bounded hypothesis to move away from the gestural-navigation edge region.
- Update static regression tests to require parser integration, navigation-mode evidence and the exact swipe offset.
- Keep all emulator actions limited to the disposable emulator and ordinary shell UID 2000. Synthetic PIN cleanup remains in the EXIT trap.

No production Android source, manifest, permissions, services, owner consent, CommandRouter, executor, physical device, signing, OTA or deployment behavior changes.

## Tests and acceptance

The 11 parser-specific unit tests passed locally on the implementation copy; Python compileall passed. Exact-head GitHub Phase 1, CI-003 and QA-005 for the AGENT-004Y commit are pending. No emulator acceptance is claimed. Independent human security/accessibility review remains pending.

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

Verify exact-head Phase 1 and CI-003, then inspect the navigation-mode artifact, post-swipe SystemUI hierarchy and JUnit output. Do not register AccessibilityService, connect MediaProjection or enable real agent dispatch until complete emulator acceptance and independent security/accessibility review pass. CommandRouter remains fail-closed.
