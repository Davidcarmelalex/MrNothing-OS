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
