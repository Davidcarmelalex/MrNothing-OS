#!/usr/bin/env python3
"""Unlock only the disposable emulator Keyguard PIN pad via exact SystemUI nodes.

This is a QA-only helper. It refuses non-emulator targets, requires ordinary
ADB shell identity, validates the complete visible PIN keypad hierarchy and
screen-bounded bounds, and never logs the synthetic PIN.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Tuple

SYSTEM_UI = "com.android.systemui"
PIN_VIEW_ID = "com.android.systemui:id/keyguard_pin_view"
CONTAINER_ID = "com.android.systemui:id/pin_container"
KEY_IDS = {str(digit): f"{SYSTEM_UI}:id/key{digit}" for digit in range(10)}
SUBMIT_ID = "com.android.systemui:id/key_enter"
BOUNDS_RE = re.compile(r"^\[(\d+),(\d+)\]\[(\d+),(\d+)\]$")
SIZE_RE = re.compile(r"(\d+)x(\d+)")


class KeyguardUnlockError(RuntimeError):
    """A required Keyguard or ADB safety condition was not met."""


def parse_bounds(node: ET.Element, width: int, height: int) -> Tuple[int, int]:
    raw = node.get("bounds", "")
    match = BOUNDS_RE.fullmatch(raw)
    if not match:
        raise KeyguardUnlockError("SystemUI node has missing or malformed bounds")
    left, top, right, bottom = (int(value) for value in match.groups())
    if (
        left < 0
        or top < 0
        or right <= left
        or bottom <= top
        or right > width
        or bottom > height
    ):
        raise KeyguardUnlockError("SystemUI node bounds are outside the emulator display")
    return ((left + right) // 2, (top + bottom) // 2)


def _usable_node(
    node: ET.Element, width: int, height: int, *, clickable: bool
) -> bool:
    if node.get("package") != SYSTEM_UI or node.get("enabled") != "true":
        return False
    if node.get("visible-to-user") == "false":
        return False
    if clickable and node.get("clickable") != "true":
        return False
    try:
        parse_bounds(node, width, height)
    except KeyguardUnlockError:
        return False
    return True


def collect_keypad_centers(
    hierarchy: Path, width: int, height: int
) -> Dict[str, Tuple[int, int]]:
    if width <= 0 or height <= 0:
        raise KeyguardUnlockError("Invalid emulator display dimensions")
    try:
        root = ET.parse(hierarchy).getroot()
    except (ET.ParseError, OSError) as exc:
        raise KeyguardUnlockError("Could not parse the captured SystemUI hierarchy") from exc

    pin_views = [
        node
        for node in root.iter("node")
        if node.get("package") == SYSTEM_UI
        and node.get("resource-id") == PIN_VIEW_ID
    ]
    if len(pin_views) != 1 or not _usable_node(
        pin_views[0], width, height, clickable=False
    ):
        raise KeyguardUnlockError("Exact visible SystemUI Keyguard PIN surface not found")

    containers = [
        node
        for node in pin_views[0].iter("node")
        if node.get("package") == SYSTEM_UI
        and node.get("resource-id") == CONTAINER_ID
    ]
    if len(containers) != 1 or not _usable_node(
        containers[0], width, height, clickable=False
    ):
        raise KeyguardUnlockError("Exact visible SystemUI PIN container not found")

    centers: Dict[str, Tuple[int, int]] = {}
    required = {**KEY_IDS, "enter": SUBMIT_ID}
    for label, resource_id in required.items():
        nodes = [
            node
            for node in containers[0].iter("node")
            if node.get("package") == SYSTEM_UI
            and node.get("resource-id") == resource_id
        ]
        valid = [
            node
            for node in nodes
            if _usable_node(node, width, height, clickable=True)
        ]
        if len(valid) != 1:
            raise KeyguardUnlockError(
                f"Expected one visible, enabled, clickable SystemUI PIN control: {label}"
            )
        centers[label] = parse_bounds(valid[0], width, height)
    return centers


def _adb(serial: str, *args: str, timeout: int = 10) -> str:
    try:
        result = subprocess.run(
            ["adb", "-s", serial, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise KeyguardUnlockError("Bounded ADB operation failed") from exc
    if result.returncode != 0:
        raise KeyguardUnlockError("ADB rejected a required Keyguard operation")
    return result.stdout


def parse_display_size(output: str) -> Tuple[int, int]:
    matches = SIZE_RE.findall(output)
    if not matches:
        raise KeyguardUnlockError("Could not determine emulator display dimensions")
    width, height = (int(value) for value in matches[-1])
    if width <= 0 or height <= 0:
        raise KeyguardUnlockError("Invalid emulator display dimensions")
    return width, height


def unlock_with_visible_systemui_pinpad(
    serial: str, hierarchy: Path, pin: str
) -> int:
    if not serial.startswith("emulator-"):
        raise KeyguardUnlockError("Refusing non-emulator target")
    identity = _adb(serial, "shell", "id")
    if "uid=2000(shell)" not in identity:
        raise KeyguardUnlockError("Refusing non-shell or privileged ADB identity")
    if not re.fullmatch(r"[0-9]{4,8}", pin):
        raise KeyguardUnlockError("Synthetic test PIN must contain 4 to 8 decimal digits")

    width, height = parse_display_size(_adb(serial, "shell", "wm", "size"))
    centers = collect_keypad_centers(hierarchy, width, height)

    for digit in pin:
        x, y = centers[digit]
        _adb(serial, "shell", "input", "tap", str(x), str(y))
        time.sleep(0.12)
    x, y = centers["enter"]
    _adb(serial, "shell", "input", "tap", str(x), str(y))
    time.sleep(0.25)
    return len(pin)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--hierarchy", required=True, type=Path)
    args = parser.parse_args(argv)
    pin = os.environ.get("TEST_PIN", "")
    try:
        count = unlock_with_visible_systemui_pinpad(args.serial, args.hierarchy, pin)
    except KeyguardUnlockError as exc:
        print(f"QA-005 Keyguard unlock refused: {exc}", file=sys.stderr)
        return 1
    print(
        f"Tapped {count} synthetic PIN digit controls and the submit control "
        "using exact visible SystemUI resource IDs; PIN omitted."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
