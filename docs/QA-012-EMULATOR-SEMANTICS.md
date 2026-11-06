# QA-012 — Read-only accessibility semantics, not spoken TalkBack acceptance

Evidence baseline: QA-011 GitHub CI run 41437333057 passed. Its retained talkback-preflight.json reports package_present=true, accessibility_enabled=false, talkback_service_enabled=false, status=blocked_service_disabled, and acceptance_passed=false.

QA-012 uses a disposable Android 15 emulator to open the preview launcher, capture the real UI hierarchy/screenshot, verify section reading order, uniquely labelled consent/recovery/settings controls, actionable semantics and at least 48dp touch bounds on system recovery/settings. It refuses physical-device serials and checks ro.kernel.qemu=1. It does not change the Home role, enable TalkBack, override accessibility settings, use root or flash firmware.

A passing semantics.json reports structural_checks_passed=true while always setting spoken_navigation_verified=false and acceptance_passed=false. This is NOT spoken screen-reader validation.

Remaining gate: with separately approved deliberate consent, use Android's accessibility UI on a disposable emulator or authorized test device to enable TalkBack; validate spoken labels, swipe/double-tap, Back/Home, stock-launcher recovery and revocation; retain redacted evidence and obtain independent supervisor approval. No physical Pixel, OTA or production readiness is implied.

The emulator test starts a fresh preview Activity with am start -S to reset keyboard-driven scroll from QA-010; it does not clear app data or change device settings.
