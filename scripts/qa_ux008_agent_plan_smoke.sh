#!/usr/bin/env bash
# QA-UX-008: disposable emulator only; launch private preview through owner-visible launcher.
set -euo pipefail
: "${ANDROID_SERIAL:?Emulator serial required}" "${QAUX008_OUTPUT:?Evidence directory required}"
case "$ANDROID_SERIAL" in emulator-*) ;; *) echo 'Refusing physical device' >&2; exit 2 ;; esac
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1
mkdir -p "$QAUX008_OUTPUT"
size="$(adb -s "$ANDROID_SERIAL" shell wm size | tr -d '\r' | sed -n 's/^Physical size: //p' | tail -1)"
[[ "$size" =~ ^[0-9]+x[0-9]+$ ]] || { echo 'No emulator display bounds' >&2; exit 1; }
IFS=x read -r width height <<< "$size"
original_scale="$(adb -s "$ANDROID_SERIAL" shell settings get system font_scale | tr -d '\r')"
[[ "$original_scale" =~ ^[0-9]+([.][0-9]+)?$ ]] || { echo 'Refusing unknown font-scale state' >&2; exit 1; }
restore() {
  local rc=$?
  trap - EXIT INT TERM
  adb -s "$ANDROID_SERIAL" shell settings put system font_scale "$original_scale" || rc=1
  exit "$rc"
}
trap restore EXIT INT TERM
adb -s "$ANDROID_SERIAL" shell settings put system font_scale 2.0
actual_scale="$(adb -s "$ANDROID_SERIAL" shell settings get system font_scale | tr -d '\r')"
[[ "$actual_scale" == "2.0" ]] || { echo '200% font-scale not applied' >&2; exit 1; }
printf '%s\n' "$original_scale" > "$QAUX008_OUTPUT/original-font-scale.txt"
dump() {
  local name="$1" remote="/sdcard/qa-ux008-$1.xml"
  CURRENT_XML="$QAUX008_OUTPUT/$name.xml"
  timeout 20s adb -s "$ANDROID_SERIAL" shell uiautomator dump "$remote" >/dev/null
  timeout 15s adb -s "$ANDROID_SERIAL" pull "$remote" "$CURRENT_XML" >/dev/null
  test -s "$CURRENT_XML"
}
scroll_up() {
  adb -s "$ANDROID_SERIAL" shell input swipe "$((width/2))" "$((height*4/5))" "$((width/2))" "$((height/4))" 220
}
scroll_top() {
  for _ in 1 2 3 4 5 6 7 8; do
    adb -s "$ANDROID_SERIAL" shell input swipe "$((width/2))" "$((height/4))" "$((width/2))" "$((height*4/5))" 150
  done
}
tap() {
  local key="$1" point x y
  for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
    if point="$(python3 scripts/qa_ux008_agent_plan.py button "$CURRENT_XML" "$key" "$width" "$height" 2>/dev/null)"; then
      read -r x y <<< "$point"
      adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
      sleep 0.3
      return 0
    fi
    scroll_up
    dump "scroll-$key-$i"
  done
  echo "Control '$key' was not visible after bounded scroll" >&2
  exit 1
}
adb -s "$ANDROID_SERIAL" shell am force-stop tech.mrnothing.os || true
adb -s "$ANDROID_SERIAL" shell am start -W -S -n tech.mrnothing.os/.MainActivity > "$QAUX008_OUTPUT/launcher-start.txt"
grep -q 'Status: ok' "$QAUX008_OUTPUT/launcher-start.txt"
sleep 2
dump launcher
tap entry
scroll_top
dump preview-initial
python3 scripts/qa_ux008_agent_plan.py screen "$CURRENT_XML" initial
# FLAG_SECURE intentionally protects this Activity: screenshots are evidence of
# capture protection, NOT proof that its protected UI is visually legible.
adb -s "$ANDROID_SERIAL" exec-out screencap -p > "$QAUX008_OUTPUT/preview-secure.png"
test -s "$QAUX008_OUTPUT/preview-secure.png"
tap start
scroll_top
dump preview-review
python3 scripts/qa_ux008_agent_plan.py screen "$CURRENT_XML" review
tap cancel
scroll_top
dump preview-cleared
python3 scripts/qa_ux008_agent_plan.py screen "$CURRENT_XML" cleared
# Hardware keyboard navigation: require one focused, labeled button at 200% scale.
focused=0
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  adb -s "$ANDROID_SERIAL" shell input keyevent KEYCODE_TAB
  dump "focus-$i"
  if python3 scripts/qa_ux008_agent_plan.py focus "$CURRENT_XML" > "$QAUX008_OUTPUT/focused-control.txt" 2>/dev/null; then
    focused=1
    break
  fi
done
[[ "$focused" == 1 ]] || { echo 'No labeled keyboard-focused control' >&2; exit 1; }
tap return
sleep 1
scroll_top
dump launcher-return
grep -q 'MR. NOTHING' "$CURRENT_XML"
printf '%s\n' 'QA-UX-008 PASS: launcher entry, 200% hierarchy, deny-only review, clear, keyboard focus, return. FLAG_SECURE screenshot redacted.' > "$QAUX008_OUTPUT/result.txt"
cat "$QAUX008_OUTPUT/result.txt"
