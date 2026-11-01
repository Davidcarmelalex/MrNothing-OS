# MrNothing OS — Android launcher prototype

This is the first **native Android application scaffold** on the Phase 1 branch.
It declares an eligible HOME activity and provides a user-consented request to become the default launcher, plus a Settings shortcut.

## Build
Open `android/` in Android Studio with JDK 17 and Android SDK 35, sync Gradle, then run `:app:assembleDebug`. Install the resulting debug APK on a test device and choose Mr. Nothing as the Home app. Do not disable the stock launcher.

## Current limits
Not yet compiled in CI or tested on a Pixel. No root, agent orchestration, app automation, SIM call audio or custom AOSP image is implemented here. This is a launcher foundation only.

## Next
- Replace shell with accessible Compose UI, app drawer and task timeline.
- Add opt-in accessibility service with strict action authorization.
- Add authenticated pairing and command transport.
- Add role-qualified dialer and cellular-audio feasibility tests on Pixel 9 Pro.
- Add signed releases and reversible device provisioning before any firmware changes.
