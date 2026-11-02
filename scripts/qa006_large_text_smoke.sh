#!/usr/bin/env bash
# QA-006: 200% font scale and visible recovery action on disposable emulator only.
set -euo pipefail
: "${ANDROID_SERIAL:?ANDROID_SERIAL required}"
case "$ANDROID_SERIAL" in emulator-*) ;; *) echo "Refusing non-emulator target" >&2; exit 2 ;; esac
: "${QA005_OUTPUT:?QA005_OUTPUT required}"
: "${QA006_OUTPUT:?QA006_OUTPUT required}"
test -s "$QA005_OUTPUT/hierarchy.xml"
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1

mkdir -p "$QA006_OUTPUT"
original_scale="$(adb -s "$ANDROID_SERIAL" shell settings get system font_scale | tr -d '\r')"
printf '%s\n' "$original_scale" > "$QA006_OUTPUT/original-font-scale.txt"
restore_font_scale() {
  if [[ "$original_scale" == "null" || -z "$original_scale" ]]; then
    adb -s "$ANDROID_SERIAL" shell settings delete system font_scale >/dev/null 2>&1 || true
  else
    adb -s "$ANDROID_SERIAL" shell settings put system font_scale "$original_scale" >/dev/null 2>&1 || true
  fi
}
trap restore_font_scale EXIT

adb -s "$ANDROID_SERIAL" shell settings put system font_scale 2.0
adb -s "$ANDROID_SERIAL" shell settings get system font_scale | tr -d '\r' | grep -Eq '^2(\.0+)?$'
adb -s "$ANDROID_SERIAL" shell am force-stop tech.mrnothing.os
adb -s "$ANDROID_SERIAL" shell am start -W -n tech.mrnothing.os/.MainActivity > "$QA006_OUTPUT/large-activity-start.txt"
grep -q 'Status: ok' "$QA006_OUTPUT/large-activity-start.txt"
sleep 4
adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa006-large.xml >/dev/null
adb -s "$ANDROID_SERIAL" pull /sdcard/qa006-large.xml "$QA006_OUTPUT/large-hierarchy.xml" >/dev/null
adb -s "$ANDROID_SERIAL" exec-out screencap -p > "$QA006_OUTPUT/large-font.png"
test -s "$QA006_OUTPUT/large-font.png"
python3 scripts/qa006_assert_hierarchy.py "$QA005_OUTPUT/hierarchy.xml" "$QA006_OUTPUT/large-hierarchy.xml"

# Scroll to check that the stock-Home recovery action remains discoverable.
found=0
for attempt in 0 1 2 3 4 5; do
  adb -s "$ANDROID_SERIAL" shell uiautomator dump /sdcard/qa006-scroll.xml >/dev/null
  adb -s "$ANDROID_SERIAL" pull /sdcard/qa006-scroll.xml "$QA006_OUTPUT/scroll-${attempt}.xml" >/dev/null
  if grep -Fq 'Switch default Home app' "$QA006_OUTPUT/scroll-${attempt}.xml"; then
    found=1
    break
  fi
  adb -s "$ANDROID_SERIAL" shell input swipe 500 1450 500 450 400
  sleep 1
done
if [[ "$found" != 1 ]]; then
  echo "Recovery action not discoverable at 200% font scale" >&2
  exit 1
fi
echo "QA-006 PASS: 200% font scale, larger heading, screenshot, scrollable recovery action"
