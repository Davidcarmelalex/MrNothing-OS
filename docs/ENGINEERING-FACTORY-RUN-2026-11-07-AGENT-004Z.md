# Engineering Factory run — AGENT-004Z: QA-005 source-gate alignment and swipe origin

**Date:** 2026-11-07  
**Repository:** Davidcarmelalex/MrNothing-OS  
**Authorized branch:** feat/phase1-agentic-phone  
**Audit baseline:** 531407b415e0f3b92b71fe832754950cb46023a2

## Repository audit

- Recursive tree: 337 entries; not truncated.
- Latest 20 branch commits inspected; six open PRs (#1 and #3–#7).
- PR #1 remained open/draft against main and matched the branch; no submitted reviews or inline threads. Other PR branches were not modified.
- PROJECT-ADAPTER.md and roadmap exist; repository SKILL.md is absent; upstream shared package remains unverified/not installed.
- Branch metadata reports protected=false; rulesets empty; protection enforcement unverified.

## Exact-head CI before AGENT-004Z

- Phase 1 push [42384614275](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384614275) and PR [42384618251](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384618251): 717 tests each, 712 passed and 5 failed. All five were stale source assertions expecting the old inline grep/sed implementation after the wake parser moved to a dedicated Python helper. Android debug unit/build job passed.
- CI-003 push [42384614277](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384614277) and PR [42384618227](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384618227): independent unsigned release builders and cross-runner verifier passed.
- QA-005 PR [42384618137](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384618137): emulator boot and wake parser passed; the 180 px bottom-offset swipe did not expose the PIN bouncer. Artifact [13578824258](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384618137/artifacts/13578824258) shows navigation_mode=2, Keyguard still visible, exact clock and device-entry bounds, no PIN keypad, no ANR, and successful synthetic PIN cleanup.

## Implementation

- Updated five stale source-gate tests to assert the dedicated parser's actual contract rather than removed shell grep/sed fragments.
- Kept the helper-backed wake predicate: Awake, no transition, HAL interactive and at least 1,500 ms since last wake.
- Moved the one emulator swipe start to display_height minus 440 px. At 1080x1920 this is y=1480, inside the observed gap between clock bottom y=1444 and device-entry icon top y=1538, away from the gestural navigation edge.
- Kept the same mid-screen destination and 450 ms duration. Navigation mode remains captured read-only.

## Tests and acceptance

The 11 parser-specific unit tests passed locally; Python compileall passed; the helper accepted the exact captured 2,541 ms wake snapshot. The previous exact-head GitHub Python policy had five stale source-gate failures; post-fix exact-head CI is pending. The next QA-005 run must prove the PIN keypad appears and the full instrumentation/QA sequence completes. No emulator acceptance is claimed.

No production Android source, manifest, permissions, services, owner-consent, router, executor, physical hardware, signing, OTA or deployment changes. Independent human security/accessibility review remains pending.

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

Verify exact-head Phase 1 and CI-003, then inspect the new navigation-mode, post-swipe SystemUI and JUnit evidence. Do not register AccessibilityService, connect MediaProjection or enable real agent dispatch before full emulator acceptance and independent security/accessibility review pass. CommandRouter remains fail-closed.
