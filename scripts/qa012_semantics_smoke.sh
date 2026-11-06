#!/usr/bin/env bash
# Disposable emulator only; no accessibility settings or role changes.
set -euo pipefail
: "$ANDROID_SERIAL" "$QA012_OUTPUT"
case "$ANDROID_SERIAL" in emulator-*) ;; *) echo 'Refusing non-emulator target' >&2; exit 2 ;; esac
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1
mkdir -p "$QA012_OUTPUT"
adb -s "$ANDROID_SERIAL" shell am start -W -S -n tech.mrnothing.os/.MainActivity > "$QA012_OUTPUT/start.txt"
grep -q 'Status: ok' "$QA012_OUTPUT/start.txt"
sleep 2
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa012-hierarchy.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa012-hierarchy.xml "$QA012_OUTPUT/hierarchy.xml" >/dev/null
density="$(adb -s "$ANDROID_SERIAL" shell wm density | tr -d '\r' | sed -n 's/^Physical density: \([0-9][0-9]*\)$/\1/p' | head -1)"
test -n "$density"
python3 scripts/qa012_semantics.py --hierarchy "$QA012_OUTPUT/hierarchy.xml" \
  --density "$(python3 -c 'import sys; print(int(sys.argv[1])/160)' "$density")" \
  --output "$QA012_OUTPUT/semantics.json"
adb -s "$ANDROID_SERIAL" exec-out screencap -p > "$QA012_OUTPUT/semantics.png"
test -s "$QA012_OUTPUT/semantics.png"
echo 'QA-012 structural audit only; spoken TalkBack unverified'
