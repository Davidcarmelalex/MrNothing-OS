#!/usr/bin/env bash
# QA-007: user-visible HOME role request and explicit cancellation, emulator only.
# Never use cmd role add-role-holder or silently accept the consent dialog.
set -euo pipefail
: "${ANDROID_SERIAL:?ANDROID_SERIAL required}"
case "$ANDROID_SERIAL" in emulator-*) ;; *) echo "Refusing non-emulator target" >&2; exit 2 ;; esac
: "${QA007_OUTPUT:?QA007_OUTPUT required}"
mkdir -p "$QA007_OUTPUT"
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1

adb -s "$ANDROID_SERIAL" shell cmd role holders android.app.role.HOME > "$QA007_OUTPUT/role-before.txt"
if grep -Fxq 'tech.mrnothing.os' "$QA007_OUTPUT/role-before.txt"; then
  echo "Unexpected pre-existing Mr. Nothing HOME role; cannot verify consent" >&2
  exit 1
fi

adb -s "$ANDROID_SERIAL" shell am force-stop tech.mrnothing.os
adb -s "$ANDROID_SERIAL" shell am start -W -n tech.mrnothing.os/.MainActivity > "$QA007_OUTPUT/activity-start.txt"
grep -q 'Status: ok' "$QA007_OUTPUT/activity-start.txt"
sleep 2
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa007-before.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa007-before.xml "$QA007_OUTPUT/before.xml" >/dev/null
read -r x y < <(python3 scripts/qa007_role_consent.py tap "$QA007_OUTPUT/before.xml")
adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
sleep 3
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa007-prompt.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa007-prompt.xml "$QA007_OUTPUT/prompt.xml" >/dev/null
python3 scripts/qa007_role_consent.py prompt "$QA007_OUTPUT/prompt.xml"

# Negative-consent path: dismiss without approving, then require original HOME role.
adb -s "$ANDROID_SERIAL" shell input keyevent KEYCODE_BACK
sleep 2
adb -s "$ANDROID_SERIAL" shell cmd role holders android.app.role.HOME > "$QA007_OUTPUT/role-after.txt"
python3 scripts/qa007_role_consent.py unchanged "$QA007_OUTPUT/role-before.txt" "$QA007_OUTPUT/role-after.txt"
echo "QA-007 PASS: explicit HOME consent prompt and no role change after dismissal"
