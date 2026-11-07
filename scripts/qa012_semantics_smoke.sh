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
# UIAutomator exposes only the current ScrollView viewport. Capture top, then
# boundedly scroll until the below-fold Installed apps section is visible.
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa012-top.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa012-top.xml "$QA012_OUTPUT/top-hierarchy.xml" >/dev/null
adb -s "$ANDROID_SERIAL" exec-out screencap -p > "$QA012_OUTPUT/semantics-top.png"
cp "$QA012_OUTPUT/top-hierarchy.xml" "$QA012_OUTPUT/bottom-hierarchy.xml"
set -- --hierarchy "$QA012_OUTPUT/top-hierarchy.xml"
found=0
if grep -Fq 'Installed apps' "$QA012_OUTPUT/top-hierarchy.xml"; then
  found=1
else
  size="$(adb -s "$ANDROID_SERIAL" shell wm size | tr -d '\r' | sed -n 's/.*size: \([0-9][0-9]*x[0-9][0-9]*\).*/\1/p' | tail -1)"
  if [[ ! "$size" =~ ^[0-9]+x[0-9]+$ ]]; then
    echo "Could not determine emulator display size: $size" >&2
    exit 1
  fi
  IFS='x' read -r width height <<< "$size"
  scroll_x=$((width / 2))
  scroll_start_y=$((height * 4 / 5))
  scroll_end_y=$((height / 4))
  for attempt in 1 2 3 4 5; do
    adb -s "$ANDROID_SERIAL" shell input swipe "$scroll_x" "$scroll_start_y" "$scroll_x" "$scroll_end_y" 400
    sleep 1
    adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa012-bottom.xml >/dev/null
    adb -s "$ANDROID_SERIAL" pull /sdcard/qa012-bottom.xml "$QA012_OUTPUT/bottom-hierarchy.xml" >/dev/null
    if grep -Fq 'Installed apps' "$QA012_OUTPUT/bottom-hierarchy.xml"; then
      found=1
      set -- "$@" --hierarchy "$QA012_OUTPUT/bottom-hierarchy.xml"
      break
    fi
  done
fi
if [[ "$found" != 1 ]]; then
  echo "Installed apps section did not enter the UIAutomator viewport after five bounded scrolls" >&2
  exit 1
fi
adb -s "$ANDROID_SERIAL" exec-out screencap -p > "$QA012_OUTPUT/semantics.png"
test -s "$QA012_OUTPUT/semantics-top.png"
test -s "$QA012_OUTPUT/semantics.png"
density="$(adb -s "$ANDROID_SERIAL" shell wm density | tr -d '\r' | sed -n 's/^Physical density: \([0-9][0-9]*\)$/\1/p' | head -1)"
test -n "$density"
python3 scripts/qa012_semantics.py "$@" \
  --density "$(python3 -c 'import sys; print(int(sys.argv[1])/160)' "$density")" \
  --output "$QA012_OUTPUT/semantics.json"
echo 'QA-012 structural audit only; spoken TalkBack unverified'
