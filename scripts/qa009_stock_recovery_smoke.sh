#!/usr/bin/env bash
# QA-009: UI-driven stock-launcher recovery on disposable emulator only.
set -euo pipefail
: "${ANDROID_SERIAL:?}" "${QA008_OUTPUT:?}" "${QA009_OUTPUT:?}"
case "$ANDROID_SERIAL" in emulator-*) ;; *) echo "Refusing non-emulator target" >&2; exit 2 ;; esac
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1
mkdir -p "$QA009_OUTPUT"
test -s "$QA008_OUTPUT/settings.xml"
adb -s "$ANDROID_SERIAL" shell cmd role get-role-holders android.app.role.HOME > "$QA009_OUTPUT/role-before.txt"
# The chooser is still open after QA-008; never override roles via shell.
read -r x y < <(python3 scripts/qa009_stock_recovery.py stock "$QA008_OUTPUT/settings.xml")
adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
sleep 3
adb -s "$ANDROID_SERIAL" shell cmd role get-role-holders android.app.role.HOME > "$QA009_OUTPUT/role-after.txt"
python3 scripts/qa009_stock_recovery.py role "$QA009_OUTPUT/role-before.txt" "$QA009_OUTPUT/role-after.txt"
adb -s "$ANDROID_SERIAL" shell input keyevent KEYCODE_HOME
sleep 3
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa009-stock-home.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa009-stock-home.xml "$QA009_OUTPUT/stock-home.xml" >/dev/null
python3 scripts/qa009_stock_recovery.py home "$QA009_OUTPUT/stock-home.xml"
adb -s "$ANDROID_SERIAL" exec-out screencap -p > "$QA009_OUTPUT/stock-home.png"
test -s "$QA009_OUTPUT/stock-home.png"
echo "QA-009 PASS: stock launcher restored through Android system UI"
