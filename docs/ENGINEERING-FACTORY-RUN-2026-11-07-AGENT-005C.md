# Engineering Factory Run AGENT-005C — QA-005 ActivityMonitor isolation

**Date:** 2026-11-07  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Audited parent:** `c06404f6a25b9b4c2a55fae415efe5f6d702adcf`  
**Selected workstream:** CI/QA + Android instrumentation reliability

## Audit

- Recursive Git tree: 340 entries, not truncated.
- Latest 20 branch commits inspected; branch was 289 commits ahead of `main`, zero behind.
- Open PRs: #1 and #3–#7. PR #1 is open/draft against `main`; its head matched the authorized branch. PRs #3–#7 were inspected and left untouched.
- PR #1 has zero submitted reviews and zero inline review threads.
- `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` exist. Repository `SKILL.md` is absent. Authorized Library searches did not surface the upstream shared engineering-factory package; it remains unverified and is not claimed installed.
- The branch is reported unprotected; no repository rulesets were returned. Protection enforcement is not established.

## Exact-head CI at the audited parent

- Phase 1 push [42396553303](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42396553303) and PR [42396557827](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42396557827): passed.
- The PR Python policy log reports 721 tests passed; static compilation and Android source-manifest security gate passed.
- Android debug job passed `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat debug APK comparison, strict Gradle dependency verification and modified-dependency negative control.
- CI-003 push [42396553277](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42396553277) and PR [42396557817](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42396557817): passed. Two independent runners produced byte-identical unsigned APKs (7,862,996 bytes; 21 entries; SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`), matching normalized contents SHA-256 `fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140`. Runtime SBOM and scoped build-environment inventory matched. Provenance reports `release_ready=false`.

## QA-005 failure evidence

QA-005 PR run [42396557841](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42396557841) booted the disposable API 35 x86_64 emulator, built the debug and instrumentation APKs, passed the dependency-verification negative control, and executed 30 instrumentation tests: 29 passed, 1 failed, 0 errors, 0 skipped.

Evidence artifact [13584455104](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42396557841/artifacts/13584455104) was downloaded and inspected. The sole failure was `AccessibilityDisclosureActivityTest.testAccessibilitySettingsIntentIsIssuedOnlyAfterExplicitTap`, at `openDisclosureFromLauncher` line 86: “launcher entry did not open the private disclosure Activity.” Per-test logcat shows MainActivity was displayed with `ACTION_MAIN` and `CATEGORY_LAUNCHER`, but no AccessibilityDisclosureActivity launch was observed. No ANR was reported; the workflow's EXIT cleanup cleared the disposable synthetic PIN.

The current test registered a **blocking** `ActivityMonitor(IntentFilter(Settings.ACTION_ACCESSIBILITY_SETTINGS), ..., true)` before launching MainActivity. AGENT-005B fixed the MainActivity test Intent by giving it the real launcher action/category, but the same blocking monitor remained active while the launcher issued its next actionless explicit component Intent to the private AccessibilityDisclosureActivity. The monitor therefore remained able to consume the disclosure launch. This is a test-harness monitor-scope defect; no production application crash is established.

## Implementation

- Keep the explicit `ACTION_MAIN` / `CATEGORY_LAUNCHER` test Intent.
- Move registration of the blocking Accessibility Settings ActivityMonitor until **after** the private disclosure Activity has opened, immediately before checking that the Settings button has not yet been tapped.
- Track registration and remove the monitor only if it was registered.
- Add a Python source regression gate requiring the ordering: disclosure Activity opened → blocking Settings monitor registered → explicit Settings button tap.
- No production Activity, manifest, permission, service, trust-store, CommandRouter, executor, device-control, release-signing or deployment code changed.

## Acceptance and limitations

The source-order assertion was checked in the authoring step. No local Gradle build or emulator was run in this environment (GitHub clone access was unavailable); exact-head GitHub Actions must verify Python policy, AndroidTest compilation, instrumentation and the full emulator smoke sequence. The parent-head Python/Android/CI-003 passes are baseline only, not acceptance for this change.

Specialist assignments remain: Android (lifecycle/platform); AI/agents (supervised planning, executor disconnected); security (consent/revocation); UX/accessibility (disclosure/TalkBack); CI/QA (instrumentation); hardware/release (Pixel 9 Pro, StrongBox, signing/OTA); independent supervisor (diff and evidence review). Independent human security/accessibility review remains pending.

Milestones: M1 foundation IN PROGRESS; M2 OS interface IN PROGRESS; M3 agentic intelligence PARTIAL; M4 permission-controlled integrations NOT STARTED; M5 Pixel 9 Pro compatibility NOT ACCEPTED; M6 security/privacy IN PROGRESS; M7 physical hardware validation BLOCKED; M8 production readiness BLOCKED. No milestone is complete.

**Next task:** verify this exact-head monitor-order correction in Phase 1 and QA-005. Do not register AccessibilityService, connect MediaProjection, enable agent dispatch, flash hardware, sign a production release or deploy OTA before the applicable tests, owner-consent review and independent security gates pass.
