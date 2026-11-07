# Engineering Factory Run — AGENT-004M

Repository: `Davidcarmelalex/MrNothing-OS`  
Authorized branch: `feat/phase1-agentic-phone`  
Audit baseline: `8b021b682b0aa8677a464f9495631b9fa55a180d`  
Scope: QA-005 emulator harness recovery; no production Android behavior changed.

## Repository and governance audit

- Recursive Git tree: 320 entries, `truncated=false`.
- Latest 20 commits inspected. Branch comparison: 262 commits ahead of `main`, zero behind.
- Six open draft PRs inspected: #1 and #3–#7. PR #1 targets `main`, is the umbrella draft, and its head matched the authorized branch at audit.
- PR #3/#4 cover QA-014 certificate-chain regressions; PR #5/#6 cover SEC-016 attestation trust; PR #7 covers AGENT-004A timestamp bounds. No unrelated PR was modified.
- `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` exist. Repository `SKILL.md` is absent. The upstream shared factory package remains unverified and is not claimed as installed.
- Branch metadata reports `protected=false`; rulesets are empty. The branch-protection detail endpoint returned HTTP 403, so required-review enforcement remains unverified.
- Existing AGENT-004L disclosure Activity is non-exported and read-only. The main manifest still declares no AccessibilityService or MediaProjection service and no new permissions. `CommandRouter` remains fail-closed and disconnected from the platform session registry.

## Baseline exact-head CI

At `8b021b682b0aa8677a464f9495631b9fa55a180d`:
- Phase 1 push [42356568198](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42356568198): PASS.
- Phase 1 PR [42356572084](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42356572084): PASS.
- CI-003 push [42356568200](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42356568200): PASS.
- CI-003 PR [42356572111](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42356572111): PASS.
- QA-005 emulator PR [42356572086](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42356572086): FAIL in the instrumentation step.

The failed QA-005 job's 180-second `connectedDebugAndroidTest` command exited 124. The instrumentation report showed the first test was `AccessibilityDisclosureActivityTest.testAccessibilitySettingsIntentIsIssuedOnlyAfterExplicitTap`; 0/30 tests completed. The pre-cleanup screenshot showed the Android lockscreen. No app assertion failure or app crash was recorded before timeout. The evidence strongly indicates that the emulator returned to keyguard during the interval between synthetic PIN setup and instrumentation startup; this is a test-harness precondition failure, not yet a demonstrated app defect.

## Selected bounded task and implementation

Repair the disposable-emulator test precondition without weakening app tests:

1. Preassemble `:app:assembleDebugAndroidTest` before the emulator PIN is configured, so test APK compilation does not consume the unlocked-screen window.
2. Set the disposable AVD screen-off timeout to ten minutes.
3. Wake the emulator immediately before instrumentation.
4. Read `dumpsys window policy`; if keyguard is showing, use ordinary `uid=2000(shell)` ADB input to swipe to the credential pad, enter only the fixed synthetic test PIN, and submit.
5. Require an observed `KeyguardServiceDelegate showing=false and KeyguardStateMonitor mIsShowing=false` state before launching UI instrumentation; unknown state fails closed with diagnostic capture.
6. Preserve the existing EXIT cleanup that clears the synthetic PIN.

The workflow remains pinned to `ANDROID_SERIAL=emulator-5554`, verifies the emulator identity and ordinary shell UID, and does not use `adb root`. The AVD is disposable. No physical device is targeted.

A Python workflow regression gate now asserts the test APK is prebuilt, the synthetic credential is cleared through the existing trap, the emulator is explicitly awake/unlocked before instrumentation, and no root command is introduced.

## Verification status

- Failure diagnosis: based on exact-head GitHub Actions job log, instrumentation test-results log, UTP log and pre-cleanup screenshot.
- Patch syntax/static checks and exact-head GitHub Actions: pending the new commit.
- No local Android SDK/AVD run is claimed.
- No AccessibilityService or MediaProjection service was declared or enabled; no permission was granted; no screen capture, gesture, real action executor or CommandRouter integration was added.
- Independent human security/accessibility review remains pending.

## Specialist responsibilities

Android owns the future service boundary; AI/agents owns action planning and policy; Security owns consent, identity and revocation; UX/accessibility owns disclosure and spoken/structural accessibility; CI/QA owns the disposable-emulator and reproducibility gates; Hardware/release owns Pixel 9 Pro, StrongBox, signing and OTA. The independent supervisor must inspect the final diff and exact-head evidence; automation is not independent human approval.

## Milestones

M1 FOUNDATION — IN PROGRESS.  
M2 OS INTERFACE — IN PROGRESS.  
M3 AGENTIC INTELLIGENCE — PARTIAL.  
M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED.  
M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED.  
M6 SECURITY/PRIVACY — IN PROGRESS.  
M7 PHYSICAL HARDWARE VALIDATION — BLOCKED.  
M8 PRODUCTION READINESS — BLOCKED.

No milestone is complete.

## Next task

After the QA-005 exact-head rerun passes, obtain independent security/accessibility review of AGENT-004L disclosure and revocation design. Only after that review may a narrowly scoped AccessibilityService provider be considered. MediaProjection remains separate. Keep `CommandRouter` fail-closed.


## QA-005 parser correction — Android 15 keyguard policy fields

The first AGENT-004M exact-head rerun passed SDK installation, debug plus instrumentation APK assembly, dependency negative control and disposable AVD boot, then failed closed before instrumentation because the parser expected `mShowingLockscreen`, a field not present in this Android 15 emulator's `dumpsys window policy` output. The captured policy explicitly reported `KeyguardServiceDelegate showing=false` and `KeyguardStateMonitor mIsShowing=false`; the PIN cleanup trap completed successfully. This was a QA harness parser mismatch, not an application test failure. The parser now reads those two observed Android 15 fields and requires both false before UI tests; if either is true it attempts the synthetic-PIN dismissal, and if either field is unavailable it fails closed. The next exact-head QA-005 run is required.
