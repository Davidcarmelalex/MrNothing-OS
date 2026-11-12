# Engineering Factory run — AGENT-004V: wait for wake transition completion

**Date:** 2026-11-07  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Audit head:** `8758ba1a9187acbec6a98fa0c7829dd1cf651f3b`  
**Target:** Pixel 9 Pro (`caiman`); this task changes only disposable-emulator QA.

## Audit

- Recursive tree: 330 entries, not truncated.
- Latest 20 authorized-branch commits inspected.
- Branch comparison at audit: 276 ahead of `main`, 0 behind.
- Six open PRs (#1 and #3–#7); PR #1 open/draft on `main` and head-matched at audit. Other PR branches untouched.
- `PROJECT-ADAPTER.md` and engineering roadmap present; repository `SKILL.md` absent.
- Authorized Library title search found no supplied upstream factory package. Upstream package remains unverified and is not claimed installed.
- Repository rulesets endpoint empty; branch-protection enforcement unverified.

## Exact-head verification at 8758ba1a9187acbec6a98fa0c7829dd1cf651f3b

Phase 1 push [42382193350](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382193350) and PR [42382197027](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197027) passed. Each Python policy job ran **701 tests**, all passed; Android debug unit/build, dependency verification and negative control passed.

CI-003 push [42382193270](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382193270) and PR [42382197099](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197099) passed independent-runner reproducibility. Verification artifact [13578087506](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197099/artifacts/13578087506) records:
- Byte-identical unsigned release APKs: 7,862,996 bytes, 21 ZIP entries.
- APK SHA-256: `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`.
- Normalized contents SHA-256: `fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140`.
- Runtime inventory SHA-256: `9b06a5f81611e6fcbf8264ab0793543a02e29a8a7b9ef3c8aa8994b3a32afe8b`; SPDX runtime SBOM SHA-256: `0fbaabc0cf1dacb1d07d55e9c60c7a2821c8f0f464d8df1d2ed8c6f1a3087212`.
- Scoped build-environment inventory has 1,260 components and matching runner reports. It is not a complete hosted-runner image SBOM. Artifacts are unsigned; provenance says `release_ready=false`.

QA-005 PR [42382197044](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197044) booted the disposable API 35 emulator, built the debug APK, passed the modified-dependency negative control, and passed the corrected Android 15 awake predicate. It then failed because the bounded bottom-edge swipe did not reveal the SystemUI PIN bouncer. Artifact [13578420997](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197044/artifacts/13578420997) was downloaded and inspected:
- `mWakefulness=Awake` and `mHalInteractiveModeEnabled=true` were present.
- Critically, `mWakefulnessChanging=true` was still present; `mLastWakeTime` was only 97 ms old at the captured snapshot.
- KeyguardServiceDelegate and KeyguardStateMonitor both reported showing=true.
- Screenshot and UIAutomator hierarchy showed the illuminated lockscreen and the exact `device_entry_icon_view`, not the PIN keypad.
- The synthetic PIN cleanup succeeded. `last-anr` reported no ANR; no application crash was established. Instrumentation and downstream smoke tests did not start.

## Bounded correction

AGENT-004V changes only `.github/workflows/qa005-emulator.yml` and `tests/test_qa005_workflow_gate.py`:
- The wake predicate now requires `mWakefulness=Awake`, `mWakefulnessChanging=false`, and `mHalInteractiveModeEnabled=true`.
- A regression test requires the stable-transition field and asserts the swipe occurs after the gate.
- Existing bounded polling, Keyguard consistency checks, bottom-edge swipe, exact SystemUI hierarchy parser and EXIT PIN cleanup remain unchanged.

This is QA-only. No production Android source, manifest, permissions, service declarations, owner-consent flow, CommandRouter, executor, physical-device behavior or release configuration changed.

## Next acceptance gate

Run exact-head Phase 1, CI-003 and QA-005 again. The next emulator artifact must show the wake transition complete before the swipe and the actual PIN bouncer before any synthetic digit tap. A green static source gate is not emulator acceptance. Independent human security/accessibility review remains pending.

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
