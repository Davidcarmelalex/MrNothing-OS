"""Offline, fail-closed validator for a redacted Pixel 9 Pro ADB snapshot.

This module never invokes ADB or changes device state. Capture the documented
read-only properties manually only after the device owner approves connection.
A passing result is a preflight gate, not M7 hardware acceptance or StrongBox
key-level evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA = "mrnothing-m7-pixel9pro-preflight-v1"
EXPECTED_MANUFACTURER = "Google"
EXPECTED_MODEL = "Pixel 9 Pro"
EXPECTED_CODENAME = "caiman"
STRONGBOX_FEATURE = "feature:android.hardware.strongbox_keystore"
MAX_VALUE_LENGTH = 256


def _text(value: Any, field: str, *, required: bool = True) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    result = value.strip()
    if required and not result:
        raise ValueError(f"{field} is required")
    if len(result) > MAX_VALUE_LENGTH or any(ord(ch) < 32 for ch in result):
        raise ValueError(f"{field} is malformed")
    return result


def _features(value: Any) -> set[str]:
    if isinstance(value, str):
        rows = value.splitlines()
    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
        rows = value
    else:
        raise ValueError("features must be a list of strings or newline-delimited text")
    if len(rows) > 4096:
        raise ValueError("features contains too many entries")
    normalized = set()
    for row in rows:
        item = row.strip()
        if len(item) > MAX_VALUE_LENGTH or any(ord(ch) < 32 for ch in item):
            raise ValueError("features contains a malformed entry")
        if item:
            normalized.add(item)
    return normalized


def evaluate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Evaluate only allowlisted public device properties; never echo raw input."""
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be a JSON object")
    if snapshot.get("schema") != SCHEMA:
        raise ValueError("unsupported snapshot schema")
    properties = snapshot.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("properties must be a JSON object")

    required = (
        "ro.product.manufacturer",
        "ro.product.model",
        "ro.product.device",
        "ro.build.version.release",
        "ro.build.version.sdk",
        "ro.boot.flash.locked",
        "ro.boot.verifiedbootstate",
        "ro.boot.vbmeta.device_state",
    )
    values = {key: _text(properties.get(key), key) for key in required}
    adb_state = _text(snapshot.get("adb_state"), "adb_state")
    qemu = _text(properties.get("ro.kernel.qemu", ""), "ro.kernel.qemu", required=False)
    features = _features(snapshot.get("features"))

    try:
        api_level = int(values["ro.build.version.sdk"], 10)
    except ValueError as exc:
        raise ValueError("ro.build.version.sdk must be a decimal integer") from exc
    if api_level < 1 or api_level > 100:
        raise ValueError("ro.build.version.sdk is outside the accepted range")

    checks = {
        "adb_device_connected": adb_state == "device",
        "manufacturer_is_google": values["ro.product.manufacturer"].casefold() == EXPECTED_MANUFACTURER.casefold(),
        "model_is_pixel_9_pro": values["ro.product.model"].casefold() == EXPECTED_MODEL.casefold(),
        "codename_is_caiman": values["ro.product.device"].casefold() == EXPECTED_CODENAME,
        "android_api_parseable": api_level >= 34,
        "bootloader_locked": values["ro.boot.flash.locked"] == "1",
        "verified_boot_green": values["ro.boot.verifiedbootstate"].casefold() == "green",
        "vbmeta_device_locked": values["ro.boot.vbmeta.device_state"].casefold() == "locked",
        "emulator_marker_not_positive": qemu in {"", "0"},
        "strongbox_feature_advertised": STRONGBOX_FEATURE in features,
    }
    failures = [name for name, passed in checks.items() if not passed]
    passed = not failures

    # Only allowlisted, non-unique identity/build fields are emitted. Serial,
    # IMEI, phone/SIM identifiers, accounts, SSIDs, BSSIDs and raw fingerprint
    # values are neither read nor copied into the result.
    return {
        "schema": "mrnothing-m7-pixel9pro-preflight-result-v1",
        "status": "ready_for_supervised_hardware_session" if passed else "blocked",
        "preflight_passed": passed,
        "acceptance_passed": False,
        "identity": {
            "manufacturer": values["ro.product.manufacturer"],
            "model": values["ro.product.model"],
            "codename": values["ro.product.device"],
            "android_release": values["ro.build.version.release"],
            "api_level": api_level,
            "emulator_marker": qemu if qemu else "absent",
        },
        "checks": checks,
        "blocked_reasons": failures,
        "strongbox_key_security_level_verified": False,
        "note": (
            "Read-only snapshot preflight only. An absent ro.kernel.qemu marker is common on physical "
            "Android builds but is not proof of physical hardware; a positive or unknown marker blocks. "
            "Feature advertisement does not prove a generated key is StrongBox-backed. Verify "
            "KeyInfo.securityLevel == SECURITY_LEVEL_STRONGBOX in a separately approved on-device test. "
            "This result never completes M7."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path, help="redacted JSON snapshot captured by an approved operator")
    parser.add_argument("--output", required=True, type=Path, help="preflight JSON output path")
    args = parser.parse_args(argv)
    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        report = evaluate_snapshot(snapshot)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"M7 preflight input rejected: {exc}", file=sys.stderr)
        return 2
    print(f"M7 Pixel 9 Pro preflight: {report['status']} (NOT M7 acceptance)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
