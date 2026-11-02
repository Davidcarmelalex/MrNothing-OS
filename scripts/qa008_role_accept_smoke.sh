#!/usr/bin/env bash
# Disposable emulator only. The system dialog is approved by an explicit UI tap.
set -euo pipefail
: "$ANDROID_SERIAL" "$QA008_OUTPUT"
case "$ANDROID_SERIAL" in emulator-*) ;; *) echo "Refusing non-emulator target" >&2; exit 2 ;; esac
mkdir -p "$QA008_OUTPUT"
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1
adb -s "$ANDROID_SERIAL" shell cmd role get-role-holders android.app.role.HOME > "$QA008_OUTPUT/role-before.txt"
test -s "$QA008_OUTPUT/role-before.txt"
! grep -Fxq tech.mrnothing.os "$QA008_OUTPUT/role-before.txt"
adb -s "$ANDROID_SERIAL" shell am force-stop tech.mrnothing.os
adb -s "$ANDROID_SERIAL" shell am start -W -n tech.mrnothing.os/.MainActivity > "$QA008_OUTPUT/start.txt"
grep -q 'Status: ok' "$QA008_OUTPUT/start.txt"
sleep 2
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa008-before.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa008-before.xml "$QA008_OUTPUT/before.xml" >/dev/null
read -r x y < <(python3 scripts/qa007_role_consent.py tap "$QA008_OUTPUT/before.xml")
adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
sleep 3
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa008-prompt.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa008-prompt.xml "$QA008_OUTPUT/prompt.xml" >/dev/null
# The Android 15 system chooser initially disables Set as default until
# the owner explicitly selects the Mr. Nothing radio option.
read -r x y < <(python3 scripts/qa008_role_accept.py select "$QA008_OUTPUT/prompt.xml")
adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
sleep 2
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa008-selected.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa008-selected.xml "$QA008_OUTPUT/selected.xml" >/dev/null
read -r x y < <(python3 scripts/qa008_role_accept.py approve "$QA008_OUTPUT/selected.xml")
adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
sleep 3
adb -s "$ANDROID_SERIAL" shell cmd role get-role-holders android.app.role.HOME > "$QA008_OUTPUT/role-after.txt"
python3 scripts/qa008_role_accept.py granted "$QA008_OUTPUT/role-before.txt" "$QA008_OUTPUT/role-after.txt"
adb -s "$ANDROID_SERIAL" shell input keyevent KEYCODE_HOME
sleep 3
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa008-home.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa008-home.xml "$QA008_OUTPUT/home.xml" >/dev/null
python3 scripts/qa008_role_accept.py home "$QA008_OUTPUT/home.xml"
adb -s "$ANDROID_SERIAL" exec-out screencap -p > "$QA008_OUTPUT/home.png"
test -s "$QA008_OUTPUT/home.png"
read -r x y < <(python3 scripts/qa008_role_accept.py recovery "$QA008_OUTPUT/home.xml")
adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
sleep 3
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa008-settings.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa008-settings.xml "$QA008_OUTPUT/settings.xml" >/dev/null
python3 scripts/qa008_role_accept.py settings "$QA008_OUTPUT/settings.xml"
echo "QA-008 PASS: explicit HOME consent, HOME launch and recovery settings"
