#!/usr/bin/env bash
# QA-005: runtime smoke test against an ephemeral, disposable Android emulator.
# Never run against a physical device; requires explicit emulator serial.
set -euo pipefail
: "${ANDROID_SERIAL:?Set ANDROID_SERIAL to an emulator-* serial}"
case "$ANDROID_SERIAL" in emulator-*) ;; *) echo "Refusing non-emulator target" >&2; exit 2 ;; esac
: "${QA005_APK:?Set QA005_APK to the debug APK path}"
: "${QA005_OUTPUT:?Set QA005_OUTPUT to an evidence directory}"
mkdir -p "$QA005_OUTPUT"
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1
adb -s "$ANDROID_SERIAL" shell getprop ro.build.version.sdk > "$QA005_OUTPUT/api-level.txt"
adb -s "$ANDROID_SERIAL" install -r "$QA005_APK"
adb -s "$ANDROID_SERIAL" shell am force-stop tech.mrnothing.os || true
adb -s "$ANDROID_SERIAL" shell am start -W -n tech.mrnothing.os/.MainActivity > "$QA005_OUTPUT/activity-start.txt"
grep -q 'Status: ok' "$QA005_OUTPUT/activity-start.txt"
sleep 3
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa005-hierarchy.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa005-hierarchy.xml "$QA005_OUTPUT/hierarchy.xml" >/dev/null
grep -q 'MR. NOTHING' "$QA005_OUTPUT/hierarchy.xml"
grep -q 'Switch default Home app' "$QA005_OUTPUT/hierarchy.xml"
grep -q 'Agent: Offline' "$QA005_OUTPUT/hierarchy.xml"
adb -s "$ANDROID_SERIAL" exec-out screencap -p > "$QA005_OUTPUT/launcher.png"
test -s "$QA005_OUTPUT/launcher.png"
# Test that system Home selection is accessible, without silently switching the default.
adb -s "$ANDROID_SERIAL" shell am start -W -a android.settings.HOME_SETTINGS > "$QA005_OUTPUT/home-settings-start.txt"
grep -q 'Status: ok' "$QA005_OUTPUT/home-settings-start.txt"
adb -s "$ANDROID_SERIAL" shell am start -W -n tech.mrnothing.os/.MainActivity > "$QA005_OUTPUT/relaunch.txt"
grep -q 'Status: ok' "$QA005_OUTPUT/relaunch.txt"
echo "QA-005 PASS: emulator launch, UI hierarchy, screenshot, Home settings and relaunch"
