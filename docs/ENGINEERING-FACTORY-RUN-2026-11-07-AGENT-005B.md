# Mr Nothing OS Engineering Factory — AGENT-005B

**Date:** 2026-11-07  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Audited parent:** `c743588fc298b391c1f541f5140f860142a86ec7`  
**Task:** isolate the launcher instrumentation Intent from the blocking Accessibility Settings ActivityMonitor.

## Audit

- Recursive Git tree: 339 entries; not truncated.
- Latest 20 branch commits inspected; live head was `c743588fc298b391c1f541f5140f860142a86ec7`.
- Main: `f3c9a701d2a337de8ef393ac14df044a79843d60`.
- Branch comparison: 288 ahead, 0 behind.
- Open PRs: #1 and #3–#7. PR #1 is open/draft against main and tracked the authorized branch head. No submitted PR reviews or inline review threads.
- Branch protection: branch reports `protected=false`; repository rulesets endpoint returned `[]`.
- `PROJECT-ADAPTER.md` and engineering roadmap exist; repository `SKILL.md` is absent. The upstream shared factory package remains unverified and is not claimed as installed.

## Evidence inspected

QA-005 run [42393640119](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393640119), artifact [13582811813](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393640119/artifacts/13582811813).

The emulator booted; debug and AndroidTest APK builds passed; dependency negative control passed; all 30 instrumentation tests started. JUnit reported 30 tests, 1 failure, 0 errors, 0 skipped. The only failure was `testAccessibilitySettingsIntentIsIssuedOnlyAfterExplicitTap`, timing out in `launchMainActivity()` while waiting for MainActivity. The companion disclosure test passed. The disposable PIN cleanup succeeded. No ANR was recorded.

The failing test had installed a blocking `ActivityMonitor` using `IntentFilter(Settings.ACTION_ACCESSIBILITY_SETTINGS)`, then launched MainActivity with an explicit component but a null action. Android's IntentFilter matching does not reject a null incoming action during action comparison, so the blocking monitor can match and consume that launch. This is a test-harness interaction, not evidence of a production Activity crash.

## Implemented

- Launch MainActivity with `Intent.ACTION_MAIN`, explicit MainActivity component and `Intent.CATEGORY_LAUNCHER`.
- Add runtime assertions that action and category are present.
- Add a Python source regression test ensuring the launcher action remains explicit while the blocking Settings monitor is present.
- Update QA evidence, roadmap and project adapter.
- No production app code, manifest, permission, service, trust store, CommandRouter, executor or device behavior changed.

## Exact-parent validation

At `c743588fc298b391c1f541f5140f860142a86ec7`:
- Phase 1 push [42393636236](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393636236) and PR [42393639999](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393639999): passed; each Python policy job ran 720 tests. Android unit tests, debug assembly, repeat debug APK comparison, strict dependency verification and negative control passed.
- CI-003 push [42393636218](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393636218) and PR [42393640076](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393640076): passed. Independent builders produced byte-identical unsigned APKs (7,862,996 bytes; SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`). Normalized-entry SHA-256 `fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140`. Runtime SBOM SHA-256 `ee9157b34a0c3108d28e89226fec8b0784d24a042f79cc109b7ce8e9438272b2`; scoped build-environment inventory SHA-256 `12ace283d99bb359f3783797a1865e3c49ad6d53f6aedb9f8972f1e8c7ab61bc`. Provenance reports `release_ready=false`.
- QA-005 failed 1/30 instrumentation tests as described above. The downstream smoke steps were skipped. No exact-head emulator acceptance.

## Acceptance and blockers

New exact-head Phase 1, CI-003 and QA-005 runs must pass. QA-011 remains a TalkBack availability preflight, and QA-012 is structural semantics only, not spoken TalkBack acceptance. Independent human security/accessibility review remains pending. Physical Pixel 9 Pro, StrongBox, signed release, OTA and production readiness remain unverified.

Milestones: M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete.

## Specialist responsibilities

Android: instrumentation lifecycle and platform boundaries.  
AI/agents: deterministic supervised planning; executor remains disconnected.  
Security: consent, revocation, trust and fail-closed review.  
UX/accessibility: owner disclosure, TalkBack and keyboard accessibility.  
CI/QA: exact-head Gradle, Python, emulator and reproducibility evidence.  
Hardware/release: Pixel 9 Pro, StrongBox, signing and OTA.  
Independent supervisor: diff review, evidence challenge and separate acceptance; no self-approval.

**Next task:** verify the corrected exact-head emulator run. If it passes, inspect JUnit, screenshots, launcher/recovery, lifecycle and owner-trust runtime evidence. If it fails, diagnose from that exact artifact before changing production code.
