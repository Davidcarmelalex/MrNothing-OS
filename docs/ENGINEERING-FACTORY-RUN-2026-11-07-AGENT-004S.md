# Engineering Factory Run — AGENT-004S: exact SystemUI lockscreen entry handoff

Date: 2026-11-07  
Repository: Davidcarmelalex/MrNothing-OS  
Authorized branch: feat/phase1-agentic-phone  
Audit baseline: 43351639df5d82bdec0593b27a7ec71d24c17f64

## Repository audit

- Complete recursive tree: 328 entries; not truncated.
- Latest 20 branch commits inspected. Branch comparison: 271 commits ahead of main, zero behind; merge base f3c9a701d2a337de8ef393ac14df044a79843d60.
- Six open PRs (#1 and #3–#7) inspected. PR #1 is the existing open/draft umbrella targeting main and its head matched the authorized branch at the audit. It has no submitted reviews or inline review threads. Other PR branches were not modified.
- PROJECT-ADAPTER.md and the engineering roadmap are present. Repository SKILL.md is absent. The authorized supplied shared package remains unverified and is not claimed installed.
- Repository rulesets endpoint returned an empty list; branch-protection enforcement remains unverified.
- Latest exact-head Phase 1 push [42372281825](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42372281825) and PR [42372285594](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42372285594) passed. The Android debug unit/build/dependency gates passed.
- CI-003 push [42372281828](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42372281828) and PR [42372285643](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42372285643) passed both independent unsigned release builders and the cross-runner verifier.
- QA-005 [42372285619](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42372285619) booted the disposable API 35 x86_64 emulator and reached the bounded credential preflight, but failed before instrumentation because the helper could not find the exact PIN-bouncer hierarchy. Its evidence artifact [13574063028](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42372285619/artifacts/13574063028) was downloaded and inspected.

## Evidence-led diagnosis

The QA-005 screenshot shows the Android 15 lockscreen, not the PIN bouncer. The fresh UIAutomator XML contains:
- `com.android.systemui:id/device_entry_icon_view`, a unique enabled/clickable SystemUI FrameLayout with bounds [446,1538][634,1726].
- Its child `com.android.systemui:id/device_entry_icon_fg`, with content description `Device locked` and matching bounds.
- No `keyguard_pin_view`, `pin_container`, digit controls or submit control.

The previous harness performed a swipe, then immediately required the PIN keypad. On this emulator, the swipe left the lockscreen visible; the exact lock-entry control was available but never tapped. The EXIT cleanup log confirms the synthetic emulator credential was cleared. The failure is a QA precondition/handoff failure; no application crash or ANR is established.

## Selected task and implementation

The first AGENT-004S candidate validated the exact lock-entry icon and attempted one bounds-derived tap. Artifact 13574907764 showed that this tap did not open the PIN bouncer; the screenshot and fresh hierarchy remained on the lockscreen. The final correction removes all helper-side taps. It validates the exact locked-state SystemUI parent/child only as a read-only state marker, and changes the workflow's single gesture to start 120 pixels above the bottom edge and end at mid-screen over 450 ms. The helper then captures fresh unique hierarchies within five attempts and requires the full exact PIN keypad before entering the synthetic PIN. No guessed keypad coordinates, text injection, PIN logging or repeated gestures are added.

This modifies only the QA helper, its unit/source tests, the project adapter and roadmap. No production app source, manifest, permission, AccessibilityService, MediaProjection, owner-consent protocol, CommandRouter, executor, physical device, firmware, OTA or deployment changes.

## Validation and acceptance

Pre-change evidence: Phase 1 push/PR passed; CI-003 push/PR passed; QA-005 failed before instrumentation. Post-change exact-head Phase 1, CI-003 and full QA-005 runs are required. No post-change test pass or emulator acceptance is claimed in this document until those runs complete.

The helper continues to refuse non-emulator serials and any ADB identity other than ordinary UID 2000 shell. The synthetic PIN remains process-environment-only and is cleared by the workflow EXIT trap. No root escalation is used.

## Specialist assignments and independent gates

- Android: SystemUI/Android lifecycle and platform boundaries.
- AI/agents: deterministic supervised plans and closed action schemas.
- Security: owner consent, identity binding, replay, revocation and fail-closed execution.
- UX/accessibility: disclosure, Settings handoff, keyboard and TalkBack.
- CI/QA: bounded instrumentation, artifact/JUnit inspection and reproducibility.
- Hardware/release: Pixel 9 Pro, StrongBox, signed artifacts and OTA rollback.
- Independent supervisor/verifier: inspect the exact diff, CI runs, artifacts and safety boundaries. Human security/accessibility approval remains pending.

## Milestones

M1 FOUNDATION — IN PROGRESS.  
M2 OS INTERFACE — IN PROGRESS.  
M3 AGENTIC INTELLIGENCE — PARTIAL.  
M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED.  
M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED.  
M6 SECURITY/PRIVACY — IN PROGRESS.  
M7 PHYSICAL HARDWARE VALIDATION — BLOCKED pending supervised physical-device access.  
M8 PRODUCTION READINESS — BLOCKED.  

No milestone is complete.

## Next task

Run exact-head Phase 1 and CI-003, then inspect full QA-005 instrumentation/JUnit and every downstream smoke step. Do not declare SEC-020B4D accepted until the complete current-head workflow passes and its artifact is independently checked. Obtain independent security/accessibility review before any AccessibilityService declaration. Keep MediaProjection separate and CommandRouter fail-closed.


## Source-gate correction

The first pushed candidate `a8f4adf70e150bf7f1dc97f8be8aa158ed0c05fe` ran 699 Python tests on both push and PR: 698 passed and one newly added source-gate assertion failed because its expected source fragment contained an extra leading quote. The assertion was corrected to match the exact bounds-derived `_adb(serial, "shell", "input", "tap", str(x), str(y))` call. The helper implementation itself was not changed. All post-correction exact-head runs remain required.


## Follow-up evidence — bottom-edge swipe correction

The exact-head QA-005 run on `a8f4adf70e150bf7f1dc97f8be8aa158ed0c05fe` showed the initial bounds-derived tap on `device_entry_icon_view` did not open the PIN bouncer. Artifact [13574907764](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42374293034/artifacts/13574907764) showed the lockscreen still visible after the tap, with the synthetic PIN successfully cleared by the EXIT trap. The final correction removes the helper-side tap entirely and moves the workflow's one swipe to the bottom gesture region (display height minus 120 px to mid-screen, 450 ms). The helper now only validates the exact lockscreen state and waits for the PIN hierarchy; it performs no input events. Exact-head CI and full QA-005 remain pending.


## Source-gate follow-up correction

The first read-only helper candidate renamed the parser to `validate_keyguard_locked_surface` but left the static test looking for `collect_keyguard_entry_center` and `entry_tapped`. GitHub Actions ran 699 Python tests on both push and PR; 698 passed and one source-gate test errored with ValueError before assertions. The source gate now targets the renamed parser and verifies the capture helper performs no input tap. No runtime behavior changed in this correction. Post-correction exact-head tests and emulator evidence remain required.
