# Engineering Factory Run — 2026-11-07 — AGENT-005A

## Scope and audit

Repository: `Davidcarmelalex/MrNothing-OS`  
Exclusive branch: `feat/phase1-agentic-phone`  
Audit baseline: `655ec3b1003eb422f0cf64a4f100f599e6e2ac48`  
Target: Google Pixel 9 Pro (`caiman`).

The recursive branch tree contained 338 entries and was not truncated. The latest 20 commits were inspected. The branch was 284 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected; PR #1 was open/draft, targeted main, matched the authorized head, and had no submitted reviews or inline review threads. Other PRs were left untouched.

`PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` are present. No repository `SKILL.md` exists. The upstream shared engineering-factory package remains unverified and is not claimed installed.

## Highest-priority finding

At exact head `655ec3b1003eb422f0cf64a4f100f599e6e2ac48`:

- Phase 1 push [42387158468](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387158468) and PR [42387163287](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387163287) passed. The PR policy suite ran 717 Python tests. Android debug unit/build, repeat-build, strict dependency verification and negative control passed.
- CI-003 push [42387158534](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387158534) and PR [42387163311](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387163311) passed independent unsigned reproducibility.
- QA-005 [42387163255](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387163255) failed before instrumentation. Artifact [13580410837](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387163255/artifacts/13580410837) showed an awake, secure emulator with Keyguard visible. The workflow had set the synthetic PIN, then required Keyguard to already be hidden. Its own instrumentation test already contains the bounded, visible-SystemUI credential flow, but was never reached.

## Implementation

1. Removed the contradictory workflow-level Keyguard-hidden gate. Kept synthetic PIN setup and EXIT cleanup, the Android 15 PowerManager awake/settle gate, and a read-only Keyguard diagnostic snapshot.
2. Replaced a normal tap of the SystemUI device-entry affordance with the exact semantic `ACTION_LONG_CLICK`, requiring one visible, enabled, clickable, long-clickable `com.android.systemui:id/device_entry_icon_view` node with screen-bounded bounds.
3. Preserved exact SystemUI keypad validation, the synthetic test PIN, ordinary ADB shell UID 2000, bounded waits, and fail-closed behavior.
4. Updated Python source gates to ensure the workflow delegates locked-device authentication to instrumentation and that the long-press cannot become an arbitrary coordinate action.
5. Updated project adapter, roadmap and QA-005 evidence history.

No production application source, manifest, permission, service, consent, trust-store, router or executor behavior was changed.

## Verification status

The baseline exact-head Phase 1 and CI-003 workflows passed as recorded above. The baseline QA-005 workflow failed before instrumentation for the preflight contradiction.

AGENT-005A's post-change exact-head Phase 1, CI-003 and QA-005 runs are triggered by the new commit. They are **pending** at this documentation point. No local Android Gradle or emulator run is claimed. GitHub Actions is the actual build/test environment for this change.

## Safety

- No root escalation or privileged ADB.
- No Keyguard-dismiss API or authentication bypass.
- Synthetic PIN is configured and cleared only on the disposable CI emulator.
- PIN entry is permitted only after exact SystemUI hierarchy validation.
- No physical flashing, production deployment, signed release or main merge.
- CommandRouter remains fail-closed.
- Independent human security and accessibility review remains pending.

## Milestones

- M1 Foundation — IN PROGRESS.
- M2 OS interface — IN PROGRESS.
- M3 Agentic intelligence — PARTIAL; no integrated executor.
- M4 Permission-controlled integrations — NOT STARTED.
- M5 Pixel 9 Pro compatibility — NOT ACCEPTED.
- M6 Security/privacy — IN PROGRESS.
- M7 Physical hardware validation — BLOCKED.
- M8 Production readiness — BLOCKED.

No milestone is complete.

## Next task

Verify the exact-head emulator sequence and inspect JUnit, Keyguard and BiometricPrompt evidence. Only after complete QA acceptance and independent security/accessibility review may a narrowly scoped AccessibilityService registration be considered. Keep MediaProjection separate and keep real agent dispatch disabled.


## AGENT-005A independent diff correction

Independent review of the first candidate commit `8c70ebe36ed2396659b56d72cb1a4571eb1af2f0` found that the workflow tree edit had retained the old Gradle command at the replacement boundary, producing a duplicated `:app:connectedDebugAndroidTest` invocation on one shell line. The candidate is not accepted. This follow-up removes the duplicate, adds a source regression assertion requiring exactly one instrumentation invocation, and corrects the Kotlin helper documentation to describe its long-click behavior. The new exact-head CI runs, not the candidate runs, determine acceptance.


## AGENT-005A test-gate correction

The first exact-head policy jobs on candidate `948ae030cf9ec2a605b2f5c5bd056168c5d25af5` ran 719 tests and reported one error: the newly added exactly-once assertion referenced `boundary_step` before the test assigned it. The failure is confined to the new Python test's statement order; the long-click source test itself passed. This follow-up moves the assertion immediately after the boundary slice is assigned. The candidate policy jobs are not accepted; a fresh exact-head rerun is required.


## AGENT-005A instrumentation compilation correction

The QA-005 run on candidate `948ae030cf9ec2a605b2f5c5bd056168c5d25af5` completed SDK installation and compiled the main debug APK, then failed at `:app:compileDebugAndroidTestKotlin`: the earlier source-block replacement had left a duplicate, incomplete `awaitCredentialPrompt` declaration immediately before the real method. No emulator was started. The duplicate line is removed here, and a new source regression test requires exactly one complete helper declaration and rejects the incomplete form. This is a test-harness compile defect; it is not evidence of a production application crash. The exact-head AndroidTest build and emulator sequence must be rerun.
