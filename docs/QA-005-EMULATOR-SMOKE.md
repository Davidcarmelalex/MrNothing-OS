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
