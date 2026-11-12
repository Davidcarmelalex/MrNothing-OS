# Engineering Factory run — AGENT-004W: minimum post-wake settle interval

**Date:** 2026-11-07  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Audit head:** `29c078a03ba7b509689ed90635f1c5e18fc4bc72`  
**Scope:** QA-only disposable Android API 35 emulator preflight.

## Audit and prior CI

- Recursive tree: 330 entries, not truncated; latest 20 branch commits inspected.
- Branch was 276 commits ahead of `main`, 0 behind at audit.
- Six open PRs (#1, #3–#7); #1 open/draft on main and matched the branch; other PRs untouched.
- Project adapter and roadmap present; repository SKILL.md absent. Authorized Library title search found no supplied upstream factory package. Upstream package remains unverified.
- Rulesets endpoint empty; branch protection unverified.

At `29c078a03ba7b509689ed90635f1c5e18fc4bc72`, Phase 1 push [42382756758](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382756758) and PR [42382761141](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761141) passed: 702 Python tests on each run, Android debug unit/build and dependency checks passed. CI-003 push [42382756740](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382756740) and PR [42382761169](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761169) passed independent unsigned release reproducibility.

## QA-005 evidence

QA-005 PR run [42382761144](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761144) passed emulator boot, debug build, negative dependency control, and the AGENT-004U/004V PowerManager predicates. It then failed because the bounded bottom-edge swipe did not reveal the PIN bouncer. Artifact [13578476716](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761144/artifacts/13578476716) was downloaded and inspected:

- `mWakefulness=Awake`, `mWakefulnessChanging=false`, and `mHalInteractiveModeEnabled=true`.
- `mLastWakeTime` age was only **67 ms** when the snapshot was taken.
- Both KeyguardServiceDelegate and KeyguardStateMonitor reported showing=true.
- Screenshot and UIAutomator hierarchy showed the illuminated lockscreen and `device_entry_icon_view`, not the PIN bouncer.
- Synthetic PIN cleanup succeeded; `last-anr` reported no ANR. No application crash was established. Instrumentation did not start.

The stable-state flag can clear almost immediately after the wake request. The gesture was still issued within the first 100 ms, before the lockscreen had a practical settle interval.

## Bounded correction

AGENT-004W changes only `.github/workflows/qa005-emulator.yml` and `tests/test_qa005_workflow_gate.py`:
- Keep the existing wakefulness, transition-complete and HAL-interactive checks.
- Parse the age reported alongside `mLastWakeTime`.
- Require at least **1,500 ms** since the last wake before the existing Keyguard checks and single swipe.
- Add a source regression gate asserting the bounded settle threshold and ordering.

The existing 20-second bounded polling loop remains the outer timeout. Synthetic PIN setup/cleanup and the exact SystemUI hierarchy parser are unchanged. No Android production source, manifest, permission, service, owner-consent, CommandRouter, executor, physical-device behavior or release configuration changes.

## Acceptance

Exact-head Phase 1, CI-003 and QA-005 reruns are required. A green source gate is not emulator acceptance. The next artifact must show a wake age >=1,500 ms before the swipe and the actual PIN bouncer before synthetic digit entry. Independent human security/accessibility review remains pending.

## Milestones

M1 Foundation — IN PROGRESS.  
M2 OS interface — IN PROGRESS.  
M3 Agentic intelligence — PARTIAL.  
M4 Permission-controlled integrations — NOT STARTED.  
M5 Pixel 9 Pro compatibility — NOT ACCEPTED.  
M6 Security/privacy — IN PROGRESS.  
M7 Physical hardware validation — BLOCKED.  
M8 Production readiness — BLOCKED.

No milestone is complete.
