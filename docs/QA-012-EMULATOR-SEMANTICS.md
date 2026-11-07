# QA-012 — Read-only accessibility semantics, not spoken TalkBack acceptance

Evidence baseline: QA-011 GitHub CI run 41437333057 passed. Its retained talkback-preflight.json reports package_present=true, accessibility_enabled=false, talkback_service_enabled=false, status=blocked_service_disabled, and acceptance_passed=false.

QA-012 uses a disposable Android 15 emulator to open the preview launcher and capture the real UI hierarchy/screenshots. Android UIAutomator exposes the current ScrollView viewport rather than reliably including every below-fold child in one dump. The smoke therefore captures a top viewport, performs at most five display-size-derived upward swipes on the emulator, and captures a second viewport after the Installed apps heading becomes visible. The parser merges top-to-bottom snapshots, de-duplicates overlapping nodes, and verifies section/action reading order, uniquely labelled consent/recovery/settings controls, actionable semantics and at least 48dp touch bounds on system recovery/settings. It refuses physical-device serials and checks ro.kernel.qemu=1.

A passing semantics.json reports structural_checks_passed=true while always setting spoken_navigation_verified=false and acceptance_passed=false. This is NOT spoken screen-reader validation.

Remaining gate: with separately approved deliberate consent, use Android's accessibility UI on a disposable emulator or authorized test device to enable TalkBack; validate spoken labels, swipe/double-tap, Back/Home, stock-launcher recovery and revocation; retain redacted evidence and obtain independent supervisor approval. No physical Pixel, OTA or production readiness is implied.

The emulator test starts a fresh preview Activity with am start -W -S to reset keyboard-driven scroll from QA-010; it does not clear app data or change device settings. The QA-012 scroll gesture changes only the disposable emulator's viewport.
