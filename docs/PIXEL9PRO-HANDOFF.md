# Pixel 9 Pro hardware handoff

**Device target:** Google Pixel 9 Pro, codename caiman. Do not assume that a Pixel 9 Pro XL, carrier-restricted unit or another model is equivalent.

## Pre-device completion gate
- [x] Android project and alternative HOME launcher shell committed.
- [x] App catalog, launch API and device diagnostics source committed.
- [x] Kotlin and Python authorization policies and tests written.
- [x] CI workflow to build debug APK and run policy tests committed.
- [ ] CI run green and APK downloaded/installed on emulator.
- [ ] Full agent transport, AI planning and voice integration implemented.
- [ ] Custom AOSP image compiled and signed.
- [ ] Installer validated against physical device.

## On arrival
1. Record model, device codename, build fingerprint, Android version and bootloader state. Keep serial numbers out of public logs.
2. Verify SIM voice/VoLTE, Wi-Fi, Bluetooth, microphone, speakers and battery.
3. Install signed test APK via ADB, choose MrNothing HOME role with explicit consent, and verify recovery to stock launcher.
4. Run UI app catalog, launch, battery and reboot tests.
5. Validate real bidirectional SIM audio as an independent high-risk research spike; root alone does not guarantee it.
6. Only after backup and documented approval consider bootloader unlocking. Unlocking generally wipes device data. Never auto-unlock or auto-flash.
7. If exploring AOSP, verify compatible Pixel vendor binaries, signing, verified boot, OTA, recovery and rollback before calling it an OS release.

## Safety
No universal access claims; banking, DRM, secure screens and accessibility limits apply. Do not publish secret keys, SIM identifiers or transcripts. Avoid distributing autonomous AccessibilityService automation via Google Play without a current policy review.


## Detailed M7 acceptance protocol

See [M7 — Pixel 9 Pro supervised hardware validation protocol](M7-PIXEL9PRO-HARDWARE-VALIDATION.md). The protocol is prepared but has not been executed; physical-device access, owner consent and independent review remain required.
