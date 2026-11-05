#!/usr/bin/env bash
# QA-020B3: exercise the production credential-only prompt factory on a disposable emulator.
# Cancellation uses a debug-only DUMP-protected control over the same BiometricPrompt CancellationSignal.
set -euo pipefail

: "${ANDROID_SERIAL:?ANDROID_SERIAL is required}"
: "${QA020B3_OUTPUT:?QA020B3_OUTPUT is required}"
case "$ANDROID_SERIAL" in
  emulator-*) ;;
  *) echo "Refusing non-emulator target" >&2; exit 2 ;;
esac

mkdir -p "$QA020B3_OUTPUT"
adb -s "$ANDROID_SERIAL" get-state | grep -qx device
adb -s "$ANDROID_SERIAL" shell getprop ro.kernel.qemu | tr -d '\r' | grep -qx 1
api="$(adb -s "$ANDROID_SERIAL" shell getprop ro.build.version.sdk | tr -d '\r')"
[[ "$api" =~ ^[0-9]+$ ]] && (( api >= 30 )) || { echo "Credential-only prompt requires API 30+" >&2; exit 1; }
shell_identity="$(adb -s "$ANDROID_SERIAL" shell id | tr -d '\r')"
printf '%s\n' "$shell_identity" > "$QA020B3_OUTPUT/adb-shell-identity.txt"
[[ "$shell_identity" == *"uid=2000(shell)"* ]] || { echo "Expected ordinary adb shell identity; refusing privileged execution" >&2; exit 1; }

TEST_PIN="${QA020B3_TEST_PIN:-2468}"
[[ "$TEST_PIN" =~ ^[0-9]{4,8}$ ]] || { echo "Test PIN must be 4-8 decimal digits" >&2; exit 1; }
PIN_CONFIGURED=0
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  if [[ "$PIN_CONFIGURED" == 1 ]]; then
    if adb -s "$ANDROID_SERIAL" shell locksettings clear --old "$TEST_PIN" > "$QA020B3_OUTPUT/test-pin-clear.txt" 2>&1; then
      PIN_CONFIGURED=0
    else
      echo "Failed to clear disposable emulator test PIN" >&2
      rc=1
    fi
  fi
  exit "$rc"
}
trap cleanup EXIT INT TERM

# QA-005 creates a fresh disposable AVD; never overwrite an existing credential.
adb -s "$ANDROID_SERIAL" shell locksettings set-pin "$TEST_PIN" > "$QA020B3_OUTPUT/test-pin-set.txt" 2>&1
PIN_CONFIGURED=1

dump_hierarchy() {
  local name="$1"
  local remote="/sdcard/qa0203-$name.xml"
  CURRENT_XML="$QA020B3_OUTPUT/$name.xml"
  adb -s "$ANDROID_SERIAL" shell uiautomator dump "$remote" >/dev/null
  adb -s "$ANDROID_SERIAL" pull "$remote" "$CURRENT_XML" >/dev/null
  test -s "$CURRENT_XML"
}

tap_button() {
  local label="$1" name="$2" coords x y
  dump_hierarchy "$name"
  coords="$(python3 scripts/qa0203_credential_prompt.py button "$CURRENT_XML" "$label")"
  read -r x y <<< "$coords"
  adb -s "$ANDROID_SERIAL" shell input tap "$x" "$y"
}

wait_for_prompt() {
  local name="$1"
  for attempt in $(seq 1 20); do
    dump_hierarchy "$name-$attempt"
    if python3 scripts/qa0203_credential_prompt.py assert-prompt-visible "$CURRENT_XML" >/dev/null 2>&1; then
      python3 scripts/qa0203_credential_prompt.py assert-no-credential-input "$CURRENT_XML"
      return 0
    fi
    sleep 1
  done
  echo "System PIN/password prompt did not become visible" >&2
  return 1
}

wait_for_status() {
  local prefix="$1" name="$2"
  for attempt in $(seq 1 25); do
    dump_hierarchy "$name-$attempt"
    if python3 scripts/qa0203_credential_prompt.py assert-status-prefix "$CURRENT_XML" "$prefix" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Probe did not reach expected status prefix: $prefix" >&2
  python3 scripts/qa0203_credential_prompt.py status "$CURRENT_XML" || true
  return 1
}

adb -s "$ANDROID_SERIAL" shell am force-stop tech.mrnothing.os || true
adb -s "$ANDROID_SERIAL" shell am start -W -S -n tech.mrnothing.os/.OwnerCredentialPromptProbeActivity > "$QA020B3_OUTPUT/probe-start.txt"
grep -q 'Status: ok' "$QA020B3_OUTPUT/probe-start.txt"
sleep 1
dump_hierarchy "probe-ready"
python3 scripts/qa0203_credential_prompt.py assert-probe "$CURRENT_XML"

tap_button "Authenticate with device credential" "cancel-start"
wait_for_prompt "cancel-prompt"
python3 scripts/qa0203_credential_prompt.py assert-no-credential-input "$CURRENT_XML"
# This tests CancellationSignal delivery; it does not claim a user SystemUI outside-tap interaction.
adb -s "$ANDROID_SERIAL" shell am broadcast -n tech.mrnothing.os/.OwnerCredentialPromptProbeCancelReceiver \
  -a tech.mrnothing.os.debug.CANCEL_CREDENTIAL_PROMPT > "$QA020B3_OUTPUT/cancel-broadcast.txt" 2>&1
wait_for_status "STATUS: PROMPT_ERROR:" "cancel-result"
python3 scripts/qa0203_credential_prompt.py assert-prompt-absent "$CURRENT_XML"
python3 scripts/qa0203_credential_prompt.py assert-no-credential-input "$CURRENT_XML"

tap_button "Authenticate with device credential" "success-start"
wait_for_prompt "success-prompt"
adb -s "$ANDROID_SERIAL" shell input text "$TEST_PIN"
adb -s "$ANDROID_SERIAL" shell input keyevent KEYCODE_ENTER
wait_for_status "STATUS: DEVICE_CREDENTIAL_ACCEPTED" "success-result"
python3 scripts/qa0203_credential_prompt.py assert-status "$CURRENT_XML" "STATUS: DEVICE_CREDENTIAL_ACCEPTED"
python3 scripts/qa0203_credential_prompt.py assert-prompt-absent "$CURRENT_XML"

printf '%s\n' \
  "QA-020B3 PASS: prompt visible; DUMP-protected cancellation signal produced prompt-error callback; test-only PIN returned DEVICE_CREDENTIAL; cleanup trap registered; no trust store, permission grant or executor connected." \
  > "$QA020B3_OUTPUT/result.txt"
cat "$QA020B3_OUTPUT/result.txt"
