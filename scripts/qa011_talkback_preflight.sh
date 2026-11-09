#!/usr/bin/env bash
# Disposable emulator, read-only preflight; never enable an accessibility service.
set -euo pipefail
: "${ANDROID_SERIAL:?}" "${QA011_OUTPUT:?}"
case "$ANDROID_SERIAL" in emulator-*) ;; *) echo "Refusing non-emulator target" >&2; exit 2 ;; esac
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1
mkdir -p "$QA011_OUTPUT"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
adb -s "$ANDROID_SERIAL" shell pm list packages | tr -d '\r' > "$tmp/packages"
adb -s "$ANDROID_SERIAL" shell settings get secure accessibility_enabled | tr -d '\r' > "$tmp/accessibility"
adb -s "$ANDROID_SERIAL" shell settings get secure enabled_accessibility_services | tr -d '\r' > "$tmp/services"
python3 scripts/qa011_talkback_preflight.py --packages "$tmp/packages" \
  --accessibility "$tmp/accessibility" --services "$tmp/services" \
  --output "$QA011_OUTPUT/talkback-preflight.json"
# Raw package inventory is deleted; no Android setting is modified.
