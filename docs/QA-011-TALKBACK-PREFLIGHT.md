# QA-011 — TalkBack environment preflight (not screen-reader acceptance)

The disposable Android 15 emulator CI performs read-only detection of the
Google TalkBack package, global accessibility setting and enabled TalkBack
service. Evidence is retained in qa005-evidence/qa011/talkback-preflight.json.

Statuses: blocked_package_missing, blocked_service_disabled, or
ready_for_manual_validation. All states explicitly record acceptance_passed=false.
A successful CI preflight step does not mean spoken accessibility passed.

The script refuses physical devices, checks ro.kernel.qemu=1, does not modify
secure settings or install apps, and deletes the raw package inventory.

Remaining gate: with explicit consent on an approved test device or disposable
emulator with officially installed TalkBack, enable it through Android's own
accessibility UI. Independently validate spoken names, focus order, double-tap
activation, back/Home navigation, stock-launcher recovery and revocation.
Retain redacted evidence and require separate verifier approval. Never enable
TalkBack via ADB secure-setting overrides. No physical Pixel, speech output or
TalkBack navigation is claimed by this preflight.
