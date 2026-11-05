#!/usr/bin/env bash
# QA-020B2: exercise the owner authority trust UI on a disposable emulator only.
# No authority material, credentials, keys, permissions or device actions are supplied.
set -euo pipefail

: "${ANDROID_SERIAL:?Set ANDROID_SERIAL to an emulator-* serial}"
: "${QA020B2_OUTPUT:?Set QA020B2_OUTPUT to an evidence directory}"
case "$ANDROID_SERIAL" in
  emulator-*) ;;
  *) echo "Refusing non-emulator target" >&2; exit 2 ;;
esac

mkdir -p "$QA020B2_OUTPUT"
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1

size="$(adb -s "$ANDROID_SERIAL" shell wm size | tr -d '\r' | sed -n 's/^Physical size: //p' | tail -1)"
[[ "$size" =~ ^[0-9]+x[0-9]+$ ]] || { echo "Unable to read emulator display size" >&2; exit 1; }
width="${size%x*}"
height="${size#*x}"
swipe_up() {
  adb -s "$ANDROID_SERIAL" shell input swipe "$((width / 2))" "$((height * 3 / 4))" \
    "$((width / 2))" "$((height / 4))" 300
}

dump_hierarchy() {
  local name="$1"
  local remote="/sdcard/qa020b2-$name.xml"
  CURRENT_XML="$QA020B2_OUTPUT/$name.xml"
  adb -s "$ANDROID_SERIAL" shell uiautomator dump "$remote" >/dev/null
  adb -s "$ANDROID_SERIAL" pull "$remote" "$CURRENT_XML" >/dev/null
  test -s "$CURRENT_XML"
}

tap_button() {
  local description="$1"
  local coords x y
  for attempt in $(seq 1 8); do
    if coords="$(python3 scripts/qa020b2_authority_trust.py button "$CURRENT_XML" "$description" 2>/dev/null)"; then
      read -r x y <<< "$coords"
      adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
      sleep 1
      return 0
    fi
    swipe_up
    dump_hierarchy "scroll-$RANDOM"
  done
  echo "Unable to find visible button: $description" >&2
  return 1
}

adb -s "$ANDROID_SERIAL" shell am force-stop tech.mrnothing.os || true
adb -s "$ANDROID_SERIAL" shell am start -W -S -n tech.mrnothing.os/.MainActivity \
  > "$QA020B2_OUTPUT/launcher-start.txt"
grep -q 'Status: ok' "$QA020B2_OUTPUT/launcher-start.txt"
sleep 2
dump_hierarchy "launcher"
tap_button "Open the owner-visible offline authority import and credential confirmation ceremony"
dump_hierarchy "authority-initial"
TRUST_STATE="$(python3 scripts/qa020b2_authority_trust.py screen "$CURRENT_XML")"

tap_button "Calculate the fingerprint of the entered Ed25519 public key"
dump_hierarchy "preview"
python3 scripts/qa020b2_authority_trust.py preview "$CURRENT_XML"

tap_button "Require separate fingerprint confirmation and fresh Android device credential"
sleep 1
dump_hierarchy "confirmation-result"
RESUMED="$(adb -s "$ANDROID_SERIAL" shell dumpsys activity activities | tr -d '\r' | \
  grep -E 'mResumedActivity|topResumedActivity' | tail -1 || true)"
if printf '%s' "$RESUMED" | grep -q 'tech.mrnothing.os/.OwnerAuthorityTrustActivity'; then
  python3 scripts/qa020b2_authority_trust.py denied "$CURRENT_XML"
elif printf '%s' "$RESUMED" | grep -Eq 'com\.android\.(systemui|settings)'; then
  # A credential UI may appear only if this supposedly fresh AVD has a secure lock.
  # Never type a PIN/password or approve it; immediately cancel and verify no mutation.
  adb -s "$ANDROID_SERIAL" shell input keyevent KEYCODE_BACK
  sleep 1
  dump_hierarchy "credential-cancelled"
  python3 scripts/qa020b2_authority_trust.py credential-cancelled "$CURRENT_XML"
else
  echo "Unexpected foreground activity after trust confirmation attempt: $RESUMED" >&2
  exit 1
fi

tap_button "Cancel any pending trust ceremony and clear imported public-key fields"
dump_hierarchy "cancelled"
AFTER_CANCEL="$(python3 scripts/qa020b2_authority_trust.py cancelled "$CURRENT_XML")"
python3 scripts/qa020b2_authority_trust.py same-state "$CURRENT_XML" "$TRUST_STATE"

tap_button "Return to Mr. Nothing without changing authority trust"
sleep 1
dump_hierarchy "launcher-return"
python3 scripts/qa020b2_authority_trust.py launcher "$CURRENT_XML"

printf '%s\n' \
  "QA-020B2 PASS: owner authority UI opened, fields and labels verified, invalid preview refused, credential boundary denied/canceled, import cleared, trust state unchanged, launcher restored." \
  > "$QA020B2_OUTPUT/result.txt"
printf '%s\n' "$TRUST_STATE" > "$QA020B2_OUTPUT/initial-trust-state.txt"
printf '%s\n' "$AFTER_CANCEL" > "$QA020B2_OUTPUT/final-trust-state.txt"
cat "$QA020B2_OUTPUT/result.txt"
