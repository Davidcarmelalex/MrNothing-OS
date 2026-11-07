# Engineering Factory Run AGENT-005D — bounded SystemUI lockscreen diagnostics

**Date:** 2026-11-07  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Audited parent:** `dd5980ee9fb6636a65f77b048dafc9332a6f5878`  
**Selected workstream:** Android instrumentation reliability + CI/QA

## Audit and exact-head baseline

The authorized branch was at `dd5980ee9fb6636a65f77b048dafc9332a6f5878`, 290 commits ahead of `main`, zero behind. The recursive tree was 340 entries, not truncated; 20 recent commits, PRs #1 and #3–#7, CI, tests, architecture and factory docs were inspected. PR #1 remained open/draft and matched the branch; other PRs were not modified. It had no submitted reviews or inline review threads. `PROJECT-ADAPTER.md` and roadmap exist; repository `SKILL.md` is absent. The upstream shared factory package was not found in authorized Library searches and remains unverified.

At parent head `dd5980ee9fb6636a65f77b048dafc9332a6f5878`:
- Phase 1 push [42401626640](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42401626640) and PR [42401631060](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42401631060) passed. Both Python policy jobs ran 721 tests. Android `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat debug APK comparison, strict dependency verification and modified-dependency negative control passed.
- CI-003 push [42401626656](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42401626656) and PR [42401631077](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42401631077) passed. Independent unsigned APKs were byte-identical: 7,862,996 bytes, 21 entries, SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`; normalized contents SHA-256 `fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140`. Runtime SBOM and scoped build-environment inventory matched. Provenance says `release_ready=false`.

## QA-005 evidence

QA-005 [42401631073](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42401631073) booted the disposable API 35 x86_64 emulator, built the app and instrumentation APKs, and executed 30 tests: 28 passed, 2 failed, 0 errors, 0 skipped. Artifact [13586350038](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42401631073/artifacts/13586350038) and JUnit XML show that both AccessibilityDisclosureActivity tests passed after AGENT-005C. The two failures were the SEC-020B4D commit-lifecycle tests, both failing in `longPressSystemDeviceEntryIconToRevealCredentialEntry` because the exact visible, enabled, clickable and long-clickable SystemUI device-entry node was not found.

The pre-cleanup screenshot shows the Android lockscreen clock and bottom lock affordance. PowerManager reported awake, not transitioning, and HAL interactive; KeyguardServiceDelegate reported showing=true and secure=true. No ANR was reported. The workflow cleanup path executed `locksettings clear --old` and reset its PIN-configured flag. The helper's failure message did not include the bounded accessibility hierarchy, so the precise resource/class/long-clickable state is not yet known.

## Implementation

- Keep the exact SystemUI resource/package/class/visibility/enabled/clickable/long-clickable checks, screen-bound checks, ordinary shell UID 2000 requirement and `ACTION_LONG_CLICK`.
- Add a bounded five-second retry (100 ms interval) for the exact accessibility-node lookup after wake; no coordinate fallback or gesture guessing.
- On failure, include a bounded `credentialUiSnapshot()` plus summaries of matching resource nodes. The snapshot is capped at 96 nodes/14 KB and omits node text/content descriptions.
- Add `longClickable` to structural node diagnostics and Python source gates for the retry, failure evidence and text-free snapshot.
- No production Android source, manifest, permission, AccessibilityService, MediaProjection, trust store, CommandRouter, executor, hardware, signing or deployment code changed.

## Acceptance and limitations

The current-head Phase 1 and CI-003 workflows passed. QA-005 did not pass; its two lifecycle failures are the current blocker. This follow-up improves bounded SystemUI observability and retries only the exact node lookup. It is not an assertion that the node is now available or that the emulator tests pass. No local Gradle/emulator was run because direct GitHub clone access was unavailable; exact-head CI must validate the change.

Specialists: Android (platform/lifecycle); AI/agents (supervised plans; executor disconnected); security (consent/revocation); UX/accessibility (disclosure/TalkBack); CI/QA (instrumentation); hardware/release (Pixel 9 Pro, StrongBox, signing/OTA); independent supervisor (diff and evidence review). Human security/accessibility approval remains pending.

Milestones: M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED. No milestone is complete.

**Next task:** inspect the new exact-head SystemUI node diagnostics. Only adjust the resource/class predicate or timing if the captured hierarchy proves it; never fall back to guessed coordinates or Keyguard-dismiss APIs.
