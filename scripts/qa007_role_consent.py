#!/usr/bin/env python3
"""QA-007: inspect user-visible HOME-role consent UI, never grant a role.

Read-only parser for Android uiautomator XML captured on a disposable emulator.
"""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

BOUNDS = re.compile(r"^\[(\d+),(\d+)\]\[(\d+),(\d+)\]$")
PACKAGE = "tech.mrnothing.os"
CHOOSER_LABEL = "Choose Mr. Nothing as Home"


def tap_coordinates(path: Path, label: str = CHOOSER_LABEL) -> tuple[int, int]:
    root = ET.parse(path).getroot()
    for node in root.iter("node"):
        if label not in (node.attrib.get("text"), node.attrib.get("content-desc")):
            continue
        if node.attrib.get("clickable") != "true" or node.attrib.get("enabled") != "true":
            raise ValueError("HOME chooser control is not enabled and clickable")
        match = BOUNDS.fullmatch(node.attrib.get("bounds", ""))
        if not match:
            raise ValueError("HOME chooser control has invalid bounds")
        left, top, right, bottom = map(int, match.groups())
        if right <= left or bottom <= top:
            raise ValueError("HOME chooser control has empty bounds")
        return (left + right) // 2, (top + bottom) // 2
    raise ValueError("HOME chooser control missing")


def verify_consent_prompt(path: Path) -> None:
    root = ET.parse(path).getroot()
    nodes = list(root.iter("node"))
    if not any("permissioncontroller" in n.attrib.get("package", "").lower() for n in nodes):
        raise ValueError("Android permission controller is not foreground")
    if not any(
        "Mr. Nothing" in n.attrib.get("text", "") or
        "Mr. Nothing" in n.attrib.get("content-desc", "")
        for n in nodes
    ):
        raise ValueError("Mr. Nothing is not identified in the consent prompt")



def classify_consent_screen(path: Path) -> str:
    """Classify only a valid Android role prompt or the unchanged launcher.

    An unknown window or a malformed system dialog must fail closed: the
    harness may retry a lost tap, but must never tap through an overlay.
    """
    nodes = list(ET.parse(path).getroot().iter("node"))
    if any("permissioncontroller" in n.attrib.get("package", "").lower() for n in nodes):
        verify_consent_prompt(path)
        return "prompt"
    if not nodes or any(n.attrib.get("package") != PACKAGE for n in nodes):
        raise ValueError("Unexpected foreground window during HOME consent")
    tap_coordinates(path)
    return "launcher"

def verify_no_implicit_grant(before: str, after: str) -> None:
    def normalize(raw: str) -> list[str]:
        return sorted(line.strip() for line in raw.splitlines() if line.strip())
    original, current = normalize(before), normalize(after)
    if PACKAGE in current or original != current:
        raise ValueError("HOME role changed without affirmative consent")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "tap":
        x, y = tap_coordinates(Path(sys.argv[2]))
        print(f"{x} {y}")
    elif len(sys.argv) == 3 and sys.argv[1] == "prompt":
        verify_consent_prompt(Path(sys.argv[2]))
        print("QA-007: permission-controller prompt is visible")
    elif len(sys.argv) == 3 and sys.argv[1] == "state":
        print(classify_consent_screen(Path(sys.argv[2])))
    elif len(sys.argv) == 4 and sys.argv[1] == "unchanged":
        verify_no_implicit_grant(Path(sys.argv[2]).read_text(), Path(sys.argv[3]).read_text())
        print("QA-007: HOME role unchanged after dismissing consent")
    else:
        raise SystemExit("usage: qa007_role_consent.py tap|prompt|state XML or unchanged BEFORE AFTER")
