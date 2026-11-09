#!/usr/bin/env bash
# QA-010: disposable emulator keyboard focus; not TalkBack.
set -euo pipefail
: "$ANDROID_SERIAL" "$QA010_OUTPUT"
case "$ANDROID_SERIAL" in emulator-*) ;; *) echo "Refusing non-emulator target" >&2; exit 2 ;; esac
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1
mkdir -p "$QA010_OUTPUT"
# QA-009 already restored stock HOME. Open preview without changing the role.
adb -s "$ANDROID_SERIAL" shell am start -W -n tech.mrnothing.os/.MainActivity > "$QA010_OUTPUT/start.txt"
grep -q 'Status: ok' "$QA010_OUTPUT/start.txt"
sleep 2
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa010-base.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa010-base.xml "$QA010_OUTPUT/base.xml" >/dev/null
python3 scripts/qa010_accessibility.py baseline "$QA010_OUTPUT/base.xml"
for i in $(seq 1 16); do
  adb -s "$ANDROID_SERIAL" shell input keyevent KEYCODE_TAB
  sleep 0.4
  adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa010-focus.xml >/dev/null
  adb -s "$ANDROID_SERIAL" pull /sdcard/qa010-focus.xml "$QA010_OUTPUT/focus-$i.xml" >/dev/null
  python3 scripts/qa010_accessibility.py focus "$QA010_OUTPUT/focus-$i.xml" >> "$QA010_OUTPUT/focus-labels.txt"
done
python3 scripts/qa010_accessibility.py sequence "$QA010_OUTPUT/base.xml" "$QA010_OUTPUT"
adb -s "$ANDROID_SERIAL" exec-out screencap -p > "$QA010_OUTPUT/keyboard-focus.png"
test -s "$QA010_OUTPUT/keyboard-focus.png"
echo "QA-010 PASS: keyboard focus reached accessible recovery control"
