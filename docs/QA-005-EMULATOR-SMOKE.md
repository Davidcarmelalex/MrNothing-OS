# QA-005 — Android emulator runtime evidence

## Scope
An isolated GitHub Actions job provisions a disposable Android API 35 x86_64 Google APIs emulator, builds the **debug** APK, launches Mr. Nothing, extracts the accessibility hierarchy, captures a screenshot, opens Android's default Home settings, and relaunches the app. It never changes the default Home role automatically, touches a physical device, or flashes firmware.

## Acceptance evidence
A **green QA-005 emulator workflow run** at the same commit must contain a nonempty screenshot, hierarchy XML with the branded launcher and visible stock-Home recovery action, successful activity-start outputs, and successful relaunch. CI results must be inspected after completion; committing a workflow is not runtime proof.

## Not covered
TalkBack speech/reading order, 200% font scale, RTL, rotation, full recovery from being the selected default Home, voice calling, Pixel 9 Pro device drivers, modem, AOSP firmware, OTA or release signing. The x86_64 emulator is **not** Pixel 9 Pro hardware.

## Failure handling
Emulator startup may fail from unavailable KVM, Android SDK downloads, resource limits or UI hierarchy timing. Preserve logs and treat failures as blockers, not successes. No signing keys or personal device data are used.

## Security
The smoke script refuses serials that do not begin with `emulator-` and checks `ro.kernel.qemu=1`. This is a testing-only guard, not a production authorization mechanism. Do not use this script to modify a real phone.

## 2026-11-02 failure investigation and bounded correction

The latest completed QA-005 job at `aadd18d7` **failed** before launcher execution. Its uploaded `emulator.log` explicitly reported `Unknown AVD name [mrnothing_qa005]` and a missing `$HOME/.android/avd/mrnothing_qa005.ini`; the 180-second ADB wait subsequently expired. The APK compilation itself passed. This is a confirmed AVD provisioning failure, not evidence of a launcher crash.

The follow-up change specifies a noninteractive `pixel` AVD hardware profile and checks `emulator -list-avds` before launching the emulator. If creation fails, CI now fails immediately with an AVD inventory instead of waiting for ADB. The `pixel` emulator profile is not proof of Pixel 9 Pro hardware compatibility.

**Acceptance remains open until a new QA-005 run is green and the hierarchy, screenshot, Home-settings and relaunch artifacts have been inspected.** Source-level regression tests do not substitute for runtime evidence.


## 2026-11-02 verified emulator smoke result

**QA-005 baseline smoke PASSED** on code commit `1c9eafe5b30c34758238d2faf85fa817a8d8992e` in GitHub Actions run [41383390521](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/41383390521). The corresponding Phase 1 push and PR workflows [41383390445](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/41383390445) and [41383385646](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/41383385646) both passed.

The AVD failure was resolved by configuring explicit isolated `ANDROID_AVD_HOME` and `ANDROID_USER_HOME` in the runner shell and passing the AVD path to `avdmanager create avd`. The prior intermediate workflow briefly failed validation because the `runner` expression was used in a job-level environment; that was corrected before the successful run.

**Artifact:** `qa005-emulator-evidence-not-for-release`, artifact ID `13114491297`, archive SHA-256 `329c0cbfa1bf3a12552fe2777c19e075436dec4905d7973e0f5989690d84c995` (retention until 2026-11-09). Its contents were downloaded and inspected: `launcher.png` (142,267 bytes), `hierarchy.xml` (6,621 bytes), activity launch results, Home settings launch, relaunch, AVD and emulator logs.

**Verified runtime evidence:** API 35 x86_64 emulator boot completed; APK installed; `tech.mrnothing.os/.MainActivity` cold-launched with `Status: ok`; hierarchy contained `MR. NOTHING`, `Installed apps`, `Choose Mr. Nothing as Home`, `Switch default Home app`, `Agent: Offline`, and installed app controls. Screenshot was inspected and visibly showed the launcher, device status, recovery button and installed app controls. `android.settings.HOME_SETTINGS` opened Android's default-app activity with `Status: ok`; launcher relaunch also returned `Status: ok`.

**Important limitations:** The emulator reported `Default Home: Another launcher`; therefore switching *to* Mr. Nothing as default and back to stock was **not** exercised. TalkBack spoken focus order, large fonts, rotation, RTL, real Pixel 9 Pro hardware, SIM audio, OTA, and production release signing remain unverified. No independent supervisor has signed off M2 or any other full milestone.


## 2026-11-07 API 35 Keyguard accessibility hierarchy correction

At exact head `0b2dd77cdbe1a5e53907a66cb29330ddb0a30542`, Phase 1 push/PR and CI-003 push/PR workflows passed, but QA-005 PR run [42297086987](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42297086987) executed 28 instrumentation tests with 26 passing and two SEC-020B4D lifecycle tests failing during disposable-emulator unlock. The workflow uploaded evidence artifact [13542627208](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42297086987/artifacts/13542627208); its pre-cleanup screenshot visibly showed the Android SystemUI `Enter PIN` keypad. The failure logs showed `keyguard_pin_view` as `android.widget.LinearLayout`, `pin_container` as `android.view.ViewGroup`, and digit resource nodes as `android.view.ViewGroup`. The prior test incorrectly required custom AOSP class names (`KeyguardPINView`, `ConstraintLayout`, `NumPadKey`) that UIAutomator did not report. Because the keypad was already displayed but failed the class gate, the helper then searched for a lockscreen device-entry icon that was not visible on the bouncer.

The test harness is corrected to identify the Keyguard PIN surface by exact SystemUI package, exact `keyguard_pin_view` and nested `pin_container` resource IDs, and the ten digit IDs plus `key_enter`. Every control must remain a visible, enabled, clickable descendant with non-zero bounds. Synthetic PIN taps are restricted to those exact descendants and screen-bounded AccessibilityNodeInfo coordinates under ordinary ADB shell UID 2000. The test no longer depends on UIAutomator reporting a particular Java class name. It does not guess coordinates, use root, dismiss Keyguard, target app-owned fields, alter production code or weaken BiometricPrompt validation.

The failed run's cleanup reported `Lock credential cleared`; the disposable emulator PIN was removed. This is a test-harness correction only. The new exact-head QA-005 run must pass both lifecycle cases and the full downstream workflow before this gate is accepted. The prior Phase 1 and CI-003 passes remain evidence for commit `0b2dd77`, not for this new correction. No physical Pixel 9 Pro was accessed.


## 2026-11-07 confirmed keyguard transition race and harness correction

At exact head 57d70638a78e4c8864f1528fd6bebed2df420cf6, QA-005 run [42360499918](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42360499918), attempt 2, failed before instrumentation. The downloaded evidence artifact [13571292518](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42360499918/artifacts/13571292518) showed the initial dumpsys window policy snapshot had both KeyguardServiceDelegate showing=false and KeyguardStateMonitor mIsShowing=false; after the old workflow waited for the screen to become unlocked, both fields had become true. The old flow treated the first transient unlocked snapshot as final and never sent the synthetic PIN. The failure was a confirmed disposable-emulator harness race, not an app assertion or crash.

The correction explicitly sends KEYCODE_SLEEP, waits for dumpsys power to confirm a non-interactive/asleep state, sends KEYCODE_WAKEUP, and then requires a positive Keyguard-showing observation before swiping and entering the synthetic test PIN through ordinary ADB shell UID 2000. It then requires both Keyguard state fields to report hidden before instrumentation. Power and post-wake Keyguard snapshots are uploaded for diagnosis. All waits remain bounded; the synthetic PIN cleanup trap remains in place. No adb root, production permission, manifest service, application source, executor, or real-device operation is added.

Acceptance requires a new exact-head QA-005 pass and inspection of its JUnit XML, screenshots, launcher/recovery outputs and lifecycle tests. This workflow correction does not itself establish emulator acceptance.


## 2026-11-07 follow-up: exact SystemUI PIN keypad input

At exact head 0b27ec5c8b0e527ab653cedbc5ad60182ba1d789, QA-005 run 42369272181 passed the forced sleep/wake transition: the artifact recorded mWakefulness=Asleep before wake and both Keyguard state fields true after wake. It then failed after the preflight shell input-text attempt; both post-entry Keyguard fields remained true. The failure screenshot showed the Android SystemUI Enter PIN screen with an empty credential field and visible numeric keypad. No instrumentation test had started; no ANR or app crash was recorded. The previous workflow therefore fixed the transition race but used a text-injection method that did not enter digits into this Keyguard keypad.

The follow-up reuses the exact-node safety policy already exercised by SEC-020B4D: SystemUI package, keyguard_pin_view, nested pin_container, key0 through key9 and key_enter. A new host-side Python helper parses the captured UIAutomator hierarchy, requires each control to be uniquely visible in the hierarchy, enabled, clickable, and bounded within the emulator display, then taps only the center of those exact bounds. It requires ordinary ADB shell UID 2000, accepts only emulator serials, validates a synthetic 4–8 digit PIN from the environment, and never logs the PIN. The workflow captures the hierarchy before input and then requires both Keyguard state fields to be hidden before instrumentation. It does not use guessed coordinates, root, accessibility activation, app-owned fields or a physical device.

New parser unit tests cover valid hierarchy, wrong package, disabled/non-clickable controls, missing and duplicate controls, out-of-screen bounds and invalid display dimensions. Exact-head QA-005 runtime acceptance remains pending.


## 2026-11-07 follow-up: AGENT-004Q helper invocation correction

At audit head 11cd5ae4ca0d84aabd146c04dcd40d990c613fd9, QA-005 run 42370256924 booted the disposable API 35 emulator, configured the synthetic PIN and captured the actual SystemUI keypad hierarchy. It then failed before instrumentation because the step's working directory is android/, while the helper was invoked using a repository-root-relative path. The helper reads TEST_PIN from its process environment, but the shell variable had not been exported. AGENT-004Q corrects the path to ../scripts/qa005_unlock_keyguard.py and passes TEST_PIN explicitly to the helper process without placing the PIN in arguments or logs. The source gate asserts this handoff. Exact-head emulator acceptance remains pending; the existing EXIT cleanup trap still clears the synthetic PIN. No production app, permission, service, executor or physical-device behavior changes.


## 2026-11-07 follow-up: AGENT-004R fresh SystemUI hierarchy acquisition

At audit head 7180daeb44908bcea1c83ef4a4753b6ec059c8bb, QA-005 run 42370944161 booted the disposable API 35 emulator and reached the synthetic PIN preflight. The UIAutomator command emitted ERROR: null root node returned by UiTestAutomationBridge.; no remote hierarchy XML was produced, and the subsequent adb pull failed. Artifact 13573334800 was inspected: the pre-cleanup screenshot showed the lockscreen rather than the PIN keypad; no instrumentation test started and last-anr reported no ANR. AGENT-004R moves capture into the QA-only helper, uses a unique cleared remote path per attempt, requires the exact success marker, retries only that null-root diagnostic at most five times, and validates the pulled XML through the existing exact SystemUI keypad parser before any tap. The helper remains emulator-only and ordinary-shell-only. Exact-head emulator acceptance remains pending; the existing EXIT cleanup still clears the synthetic PIN. No production app, permission, service, executor or physical-device behavior changes.


## 2026-11-07 wake-state readiness correction (AGENT-004T)

At exact head `38596a6b138cf039e26f244e780c63d5bd6032f7`, QA-005 run [42375122823](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42375122823) failed before instrumentation. Artifact [13575706693](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42375122823/artifacts/13575706693) showed the lockscreen still visible. The captured policy state reported KeyguardServiceDelegate and KeyguardStateMonitor as showing, while the display remained `SCREEN_STATE_TURNING_ON` / `INTERACTIVE_STATE_WAKING`. The previous preflight proceeded on Keyguard visibility alone and could issue its swipe during the wake transition.

AGENT-004T adds a bounded wait for `mWakefulness=Awake` and `mInteractive=true`, records the post-wake power snapshot, and requires both Keyguard policy indicators to be true before the existing single swipe. This is QA-harness-only. The synthetic PIN cleanup succeeded in the failed run. Exact-head emulator acceptance remains pending; this correction does not establish a passing emulator test.


## 2026-11-07 follow-up: AGENT-004U Android 15 PowerManager field correction

At exact head `81cbd72f3fdb240267cc19ee2aaabd985ad6f6e6`, QA-005 PR run [42377982743](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377982743) booted the disposable API 35 emulator, built the debug APK and passed the modified-dependency negative control. It failed before instrumentation because the workflow's awake predicate required `mInteractive=true`, a field absent from the captured Android 15 `dumpsys power` output. The actual snapshot reported `mWakefulness=Awake` and `mHalInteractiveModeEnabled=true`; the pre-wake snapshot reported `mWakefulness=Asleep` and `mHalInteractiveModeEnabled=false`. The screenshot showed the illuminated lockscreen. The EXIT trap cleared the synthetic PIN; last-anr reported no ANR and no application crash was established.

AGENT-004U changes the QA-only sleep/wake predicates to require the matching wakefulness and `mHalInteractiveModeEnabled` values. The source regression test now asserts the exact Android 15 fields and rejects the unsupported `mInteractive` predicates. Existing Keyguard validation, bounded gesture, exact SystemUI hierarchy parser and synthetic-PIN cleanup are unchanged. This is a harness correction only; exact-head reruns and complete QA-005 evidence are still required before emulator acceptance. No production app, permission, service, consent, router, executor or physical-device behavior changes.


## 2026-11-07 follow-up: AGENT-004V wait for wake transition completion

At exact head `8758ba1a9187acbec6a98fa0c7829dd1cf651f3b`, Phase 1 push/PR runs [42382193350](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382193350) and [42382197027](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197027) passed with 701 Python tests each and Android debug build/unit checks. CI-003 push/PR [42382193270](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382193270) and [42382197099](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197099) passed independent unsigned reproducibility: 7,862,996-byte APKs, 21 entries, SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`; normalized content SHA-256 `fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140`. Release remains unsigned and not release-ready.

QA-005 [42382197044](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197044) passed the Android 15 `mHalInteractiveModeEnabled` gate but failed after the bottom-edge swipe. Artifact [13578420997](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197044/artifacts/13578420997) shows `mWakefulness=Awake`, `mHalInteractiveModeEnabled=true`, but `mWakefulnessChanging=true` and `mLastWakeTime` only 97 ms old. The screenshot/hierarchy remained on the lockscreen with the exact device-entry icon; the PIN bouncer did not appear. Both Keyguard policy indicators reported showing. Synthetic PIN cleanup succeeded and last-anr reported no ANR.

AGENT-004V changes only the QA workflow and source regression gate: the awake predicate now also requires `mWakefulnessChanging=false` before the swipe. No product source, manifest, permissions, services, consent, router, executor or physical-device behavior changes. Exact-head reruns remain required; no emulator acceptance is claimed.


## 2026-11-07 follow-up: AGENT-004W minimum post-wake settle interval

At exact head `29c078a03ba7b509689ed90635f1c5e18fc4bc72`, Phase 1 push/PR [42382756758](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382756758) and [42382761141](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761141) passed with 702 Python tests each and Android debug unit/build checks. CI-003 push/PR [42382756740](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382756740) and [42382761169](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761169) passed independent unsigned reproducibility.

QA-005 [42382761144](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761144) passed emulator boot and the corrected Android 15 wake predicates, but the bottom-edge swipe did not reveal the PIN bouncer. Artifact [13578476716](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761144/artifacts/13578476716) shows `mWakefulness=Awake`, `mWakefulnessChanging=false`, `mHalInteractiveModeEnabled=true`, yet `mLastWakeTime` was only 67 ms old. Keyguard remained showing; screenshot/hierarchy showed the lockscreen and device-entry icon, not the PIN bouncer. Synthetic PIN cleanup succeeded; last-anr reported no ANR.

AGENT-004W changes only the QA workflow and source regression gate to require a 1,500 ms minimum age from `mLastWakeTime` before the existing swipe, in addition to the stable PowerManager flags. No product source, manifest, permissions, services, consent, router, executor or physical-device behavior changes. Exact-head reruns remain required; no emulator acceptance is claimed.


## Engineering Factory run — 2026-11-07, AGENT-004X QA-005 wake-age parser correction

Audit baseline: 0ffb78dfacf09b2856c836e4ee631e70b389425f; recursive tree contained 333 entries and was not truncated; latest 20 authorized-branch commits were inspected; branch comparison was 279 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 remained open/draft, targeted main, and matched the authorized branch head; PRs #3–#7 target separate scoped branches and were left untouched. PR #1 had no submitted reviews or inline review threads. Branch metadata reported protected=false; rulesets were empty, so enforcement remains unverified. PROJECT-ADAPTER.md and the engineering roadmap are present; repository SKILL.md is absent. The upstream shared engineering-factory package remains unverified and is not claimed installed.

At exact head, Phase 1 push [42383275068](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383275068) and PR [42383280140](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280140) passed. The PR Python policy job ran 703 tests and passed; Android debug unit/build, repeat APK comparison, strict Gradle dependency verification, modified-dependency negative control and source-manifest gate passed. CI-003 push [42383275207](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383275207) and PR [42383280178](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280178) passed independent unsigned release build and reproducibility verification.

QA-005 PR run [42383280219](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280219) booted the disposable API 35 emulator, built the debug APK and passed the dependency negative control, but stopped before instrumentation at the post-wake PowerManager gate. Artifact [13578492527](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280219/artifacts/13578492527) contains a valid snapshot: mWakefulness=Awake, mWakefulnessChanging=false, mHalInteractiveModeEnabled=true, and mLastWakeTime=32654 (22892 ms ago). The pre-cleanup screenshot shows the illuminated Android lockscreen. The last-ANR report says no ANR occurred; no app crash was established. The EXIT trap successfully cleared the synthetic emulator PIN.

Evidence-led root cause: the workflow's GNU sed -E expression contained double-escaped parentheses and back-reference (two backslashes before the parentheses and capture reference) in the actual shell source, so it did not extract the valid 22892 millisecond age and the fail-closed gate rejected an otherwise settled snapshot. The after-wake snapshot writer also used a double-escaped newline format.

AGENT-004X corrects the sed expression to the exact single-escape ERE form and corrects the snapshot writer to printf with a real newline. Two regression tests execute the exact expression against the captured Android 15 mLastWakeTime format, including a too-recent value and missing/malformed values; another checks the snapshot writer's newline escaping. This is a QA harness-only change. No Android production source, manifest, permission, service, owner-consent flow, CommandRouter, executor, physical device or release behavior changes.

Post-change exact-head Phase 1, CI-003 and full QA-005 results are required before acceptance. No new-head emulator acceptance is claimed by this run. Independent human security/accessibility review remains pending.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete.

Next: verify the parser regression tests and exact-head Phase 1/CI-003, then inspect the new QA-005 emulator artifact and JUnit results. Do not add an AccessibilityService declaration, connect MediaProjection or enable real agent dispatch until full emulator acceptance and independent security/accessibility review pass. CommandRouter remains fail-closed.
