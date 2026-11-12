# Engineering Factory run — AGENT-004U: Android 15 PowerManager predicate correction

**Date:** 2026-11-07  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Audit head:** `81cbd72f3fdb240267cc19ee2aaabd985ad6f6e6`  
**Target:** Pixel 9 Pro (`caiman`); this task changes only the disposable-emulator QA harness.

## Audit

- Complete recursive tree: 330 entries; not truncated.
- Latest 20 commits on the authorized branch inspected.
- Branch comparison: 276 commits ahead of `main`, 0 behind.
- Open PRs: #1 and #3–#7. PR #1 is open/draft, targets `main`, and its head matched the authorized branch at audit time. PRs #3–#7 remain on separate scoped branches and were not modified.
- `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` exist.
- Repository `SKILL.md` is absent. The authorized Library title search found no supplied shared factory package. The upstream package remains unverified and is not claimed installed.
- GitHub repository rulesets endpoint returned an empty list; branch-protection enforcement remains unverified.

## Exact-head evidence

At `81cbd72f3fdb240267cc19ee2aaabd985ad6f6e6`, Phase 1 push [42377979055](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377979055) and PR [42377982649](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377982649) passed both Android debug and Python policy jobs. CI-003 push [42377979046](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377979046) and PR [42377982589](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377982589) passed independent unsigned APK builds and verification.

QA-005 PR run [42377982743](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377982743) failed in its credential preflight before instrumentation. Artifact [13576597256](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377982743/artifacts/13576597256) was downloaded and inspected:

- The disposable API 35 emulator booted; the debug APK build and modified-dependency negative control passed.
- Before wake, `dumpsys power` reported `mWakefulness=Asleep` and `mHalInteractiveModeEnabled=false`.
- After `KEYCODE_WAKEUP`, it reported `mWakefulness=Awake` and `mHalInteractiveModeEnabled=true`.
- The Android 15 dump did **not** expose `mInteractive=true`. The workflow's `screen_is_awake` predicate therefore remained false for all 20 polls, despite the power service reporting awake/interactive mode. The pre-cleanup screenshot shows the illuminated lockscreen.
- The synthetic PIN cleanup ran successfully. `dumpsys activity lastanr` reports no ANR since boot; no MrNothing application crash was established. No instrumentation test started.

## Bounded correction

AGENT-004U changes only `.github/workflows/qa005-emulator.yml` and `tests/test_qa005_workflow_gate.py`:

- The asleep predicate now requires both `mWakefulness=Asleep` and `mHalInteractiveModeEnabled=false`.
- The awake predicate now requires both `mWakefulness=Awake` and `mHalInteractiveModeEnabled=true`.
- The source regression gate asserts these exact Android 15 dump fields and rejects the unsupported `mInteractive` field.
- Existing bounded waits, Keyguard checks, synthetic PIN handling and EXIT cleanup remain unchanged.

No Android production source, manifest, permission, service declaration, owner-consent flow, CommandRouter, executor, physical-device behavior or release configuration is changed.

## Verification and acceptance

The workflow-source regression is designed to catch recurrence. Exact-head Phase 1, CI-003 and full QA-005 reruns are required after this commit. A green source gate is not emulator acceptance. No emulator result for the new head, physical Pixel test, production signing, OTA or production readiness is claimed by this run.

## Responsibilities and gates

- Android: validate platform lifecycle and system permission handoffs.
- AI/agents: preserve supervised planning and disconnected execution.
- Security: review consent, revocation, attestation and fail-closed routing.
- UX/accessibility: validate disclosure, TalkBack and large text.
- CI/QA: exact-head tests, emulator artifacts and reproducibility.
- Hardware/release: Pixel 9 Pro, StrongBox, signing, OTA and recovery.
- Independent supervisor: review source diff and runtime artifacts; human security/accessibility approval remains pending.

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

## Next task

Run exact-head Phase 1 and CI-003, then inspect the new QA-005 power snapshot and full emulator artifact. Only after the synthetic unlock and all downstream smoke steps pass should the QA-005 emulator gate be accepted. Keep AccessibilityService registration, MediaProjection and real agent dispatch disconnected pending independent security/accessibility review.
