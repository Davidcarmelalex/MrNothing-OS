# QA-020B3 cancellation harness — failure analysis and acceptance record

**Repository:** Davidcarmelalex/MrNothing-OS  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Audit head:** `b6bc52b6ba1db009d1cd8f5415f6c1efcd4c07ad`  
**Failed exact-head emulator run:** [42079017623](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42079017623)  
**Evidence artifact:** [13440251753](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42079017623/artifacts/13440251753)

## Audit baseline

The recursive Git tree at the audited head contains 248 entries and is not truncated. `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` are present; repository `SKILL.md` is absent. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed.

Open PRs #1 and #3–#7 were inspected. PR #1 is the umbrella draft from `feat/phase1-agentic-phone` to `main`, at the audited head, with 160 commits and 189 changed files. It has zero submitted reviews and zero inline review threads. PRs #3–#7 are separate draft workstreams targeting the authorized feature branch or their own QA-014 branches; they were not modified. Main remains unchanged. No merge, force-push, physical-device action or unrelated branch write occurred.

The branch architecture includes a Kotlin HOME launcher, debug-only credential prompt probe, offline SEC-020 authority import/trust ceremony, Python HERMES/consent policy prototypes, and CI for Phase 1, reproducibility and emulator QA. The command executor remains disconnected.

## Exact-head CI at b6bc52b

- Phase 1 PR run [42079017628](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42079017628): passed. Android Gradle unit tests, debug assembly, repeat-build comparison, strict dependency verification and modified-dependency negative control passed; Python-policy job and manifest gate passed.
- CI-003 PR run [42079017604](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42079017604): passed. Both independent release builders and the artifact/toolchain equivalence verifier passed.
- QA-005 PR run [42079017623](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42079017623): failed only at QA-020B3 cancellation. Emulator boot, launcher/recovery, QA-006 through QA-013 and QA-020B2 passed. QA-011 was a read-only TalkBack availability preflight (`blocked_service_disabled`); QA-012 was structural semantics only, not spoken TalkBack acceptance.

The QA job log shows the system credential prompt became visible. The first outside-tap correction derived (540,31) and tapped it. The prompt remained visible for all 25 status polls, so the probe status label was not present in the hierarchy. The EXIT cleanup recorded `Lock credential cleared`. This is a test-harness geometry error; it is not evidence that the production authentication callback is defective.

## Root cause

The captured hierarchy has a 1080×1920 screen. The full-screen SystemUI cancel background is [0,0][1080,1920]. The credential header is [0,63][1080,903], and the credential input is [0,903][1080,1164]. The previous helper chose the midpoint between screen top and the minimum panel top: y=31. That point is in the status-bar inset, not a reliable outside-content touch target. The earlier fixture also incorrectly extended the credential input almost to the bottom of the screen, so it did not model the captured hierarchy.

## Bounded correction

- Require exactly one visible, enabled, clickable SystemUI cancel background with the expected package, resource ID, class and content description.
- Require exactly one credential header and one credential input node; validate both bounds against the full-screen background.
- Compute the union's bottom edge and select the midpoint of the bottom safe margin, reserving `max(96 px, 5% of screen height)` for system UI. For the captured hierarchy, the expected point is (540,1494).
- Fail closed if the bottom safe region does not exist; never fall back to status-bar or navigation-bar taps.
- Add before/after screenshots around the cancellation tap to make the next failure diagnosable.
- Add parser tests for the captured geometry, status-bar-only margin rejection, missing/ambiguous surfaces, non-clickable surfaces and incomplete panel hierarchies.

The script continues to target only a freshly created `emulator-*` AVD with `ro.kernel.qemu=1`, requires ordinary `uid=2000(shell)`, uses a fixed test-only PIN, and clears it in an EXIT/INT/TERM trap. It does not use adb root, `su`, fastboot, physical devices, trust-store commits, permission grants or the executor.

## Local checks executed for this correction

- Seven focused Python hierarchy/parser tests: passed.
- Captured failure hierarchy parsed to (540,1494): passed.
- `bash -n scripts/qa0203_credential_prompt_smoke.sh`: passed.
- `python -m compileall` for the helper and test module: passed.

These local checks do not establish emulator interaction. The exact-head QA-005 rerun is the acceptance gate for cancellation and the subsequent test-PIN success callback.

## Roles and independent acceptance

- Android: maintain the shared production/debug prompt factory and Activity lifecycle behavior.
- AI/agents: keep the executor disconnected; no action authorization is in this task.
- Security: verify DEVICE_CREDENTIAL-only result handling and ensure the probe cannot reach trust storage or device controls.
- UX/accessibility: ensure the prompt probe remains non-release and does not overstate TalkBack acceptance.
- CI/QA: execute the exact-head emulator cancellation and success path and retain screenshots/XML/logs.
- Hardware/release: no hardware or release activity is authorized by this task.
- Independent supervisor/verifier: inspect the diff and evidence independently; gate remains PENDING until an independent reviewer signs off.

## Milestones and limitations

M1 Foundation: IN PROGRESS. M2 OS interface: IN PROGRESS. M3 Agentic intelligence: PARTIAL. M4 permission-controlled integrations: NOT STARTED. M5 Pixel 9 Pro compatibility: NOT ACCEPTED. M6 security/privacy: IN PROGRESS. M7 physical hardware validation: BLOCKED. M8 production readiness: BLOCKED. No milestone is complete.

The next acceptance result must report the exact commit, emulator API/image, cancellation callback, successful DEVICE_CREDENTIAL callback, test-PIN cleanup, screenshots and CI status. StrongBox, trust-store commit, physical Pixel 9 Pro, spoken TalkBack, independent security review, signed OTA and production readiness remain unverified.


## QA-020B3 exact-head cancellation failure and side-gutter correction — 2026-11-06

At branch head `c92fad5dd8fea0fd5029cd01d14a36fd59924d6d`, Phase 1 push/PR runs 42084891699 and 42084902087 passed, and CI-003 push/PR runs 42084891920 and 42084901849 passed. QA-005 run 42084901826 failed at the QA-020B3 cancellation assertion. The captured hierarchy and artifact 13442612292 show that the revised bottom-margin tap at (540,1494) left the SystemUI prompt visible and changed the `lockPassword` EditText text to a bullet. The coordinate therefore struck the hidden keypad, not a safe cancellation area. The fixed test PIN was not submitted for authentication; the EXIT cleanup cleared it. This is a harness defect. The earlier claim that the bottom margin was safe is superseded.

The bounded correction now derives the cancellation point from the actual visible `com.android.systemui:id/lockPassword` EditText. It selects the widest side gutter, validates the point against screen/input bounds, and rejects any overlap with another visible clickable SystemUI control. The captured hierarchy yields (133,1033), outside the password field. Immediately after the tap, the helper accepts either a dismissed prompt or an empty input field and fails if any character was entered. The bottom-margin tap and secure-screen screenshots are removed. Parser tests cover the captured geometry, narrow gutters, missing/ambiguous input, overlapping controls and accidental input detection.

The script remains restricted to a freshly created API 30+ x86_64 emulator, `ro.kernel.qemu=1`, ordinary `uid=2000(shell)`, a fixed test-only PIN, and cleanup via EXIT/INT/TERM. No root, physical device, trust-store mutation, permission grant, executor or production credential is used. The next exact-head QA-005 run must pass both the cancellation callback and subsequent successful `DEVICE_CREDENTIAL` callback before QA-020B3 runtime acceptance. Independent security review, StrongBox and Pixel 9 Pro validation remain pending.
