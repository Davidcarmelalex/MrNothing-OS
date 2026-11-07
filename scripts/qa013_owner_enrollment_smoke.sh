#!/usr/bin/env bash
# Disposable emulator only: negative path with no secure lock or credential entry.
set -euo pipefail
: "$ANDROID_SERIAL" "$QA013_OUTPUT"
case "$ANDROID_SERIAL" in emulator-*) ;; *) echo "Refusing non-emulator target" >&2; exit 2 ;; esac
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1
mkdir -p "$QA013_OUTPUT"
adb -s "$ANDROID_SERIAL" shell am start -W -S -n tech.mrnothing.os/.MainActivity > "$QA013_OUTPUT/start.txt"
grep -q 'Status: ok' "$QA013_OUTPUT/start.txt"
size=$(adb -s "$ANDROID_SERIAL" shell wm size | tr -d '\r' | sed -n 's/^Physical size: \([0-9]*x[0-9]*\)$/\1/p' | head -1)
test -n "$size"
width=$(echo "$size" | cut -dx -f1)
height=$(echo "$size" | cut -dx -f2)
description="Optional local credential-confirmed StrongBox key enrollment; no agent access granted"
found=0
for attempt in 1 2 3 4 5; do
  sleep 1
  adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa013.xml >/dev/null
  adb -s "$ANDROID_SERIAL" pull /sdcard/qa013.xml "$QA013_OUTPUT/launcher-$attempt.xml" >/dev/null
  if coords=$(python3 scripts/qa013_owner_enrollment.py find "$QA013_OUTPUT/launcher-$attempt.xml" "$description" 2>/dev/null); then
    found=1
    break
  fi
  adb -s "$ANDROID_SERIAL" shell input swipe "$((width/2))" "$((height*3/4))" "$((width/2))" "$((height/4))" 350
done
test "$found" -eq 1
read -r x y <<< "$coords"
adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
sleep 2
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa013.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa013.xml "$QA013_OUTPUT/before.xml" >/dev/null
python3 scripts/qa013_owner_enrollment.py status "$QA013_OUTPUT/before.xml" "Local security-key enrollment"
coords=$(python3 scripts/qa013_owner_enrollment.py find "$QA013_OUTPUT/before.xml" "Confirm device credential to create a local hardware security key only")
read -r x y <<< "$coords"
adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
sleep 2
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa013.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa013.xml "$QA013_OUTPUT/denied.xml" >/dev/null
python3 scripts/qa013_owner_enrollment.py status "$QA013_OUTPUT/denied.xml" "Unlocked, active device with secure lock required. Refused."
adb -s "$ANDROID_SERIAL" exec-out screencap -p > "$QA013_OUTPUT/denied.png"
test -s "$QA013_OUTPUT/denied.png"
echo "QA-013 PASS: insecure emulator denied local owner enrollment"
