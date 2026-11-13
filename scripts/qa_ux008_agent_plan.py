"""QA-UX-008: strict, viewport-aware UIAutomator checks for offline plan preview.

Only parses hierarchy snapshots; never grants Android permissions or executes actions.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PACKAGE = "tech.mrnothing.os"
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\Z")
BUTTONS = {
    "entry": "Inspect fixed sample agent actions; no AI inference or device control",
    "start": "Start a supervised display-only sample, not an agent execution",
    "cancel": "Clear the sample plan preview",
    "return": "Close preview without any device action",
}
TITLE = "Offline agent plan preview"
INITIAL = "Select a fixed sample action. This is not AI inference, owner consent or device control. Nothing will run."
CLEARED = "Preview cleared. No consent, permission or device action granted."


def nodes(xml):
    root = ET.fromstring(xml)
    if root.tag != "hierarchy":
        raise ValueError("Expected UIAutomator hierarchy")
    return [n for n in root.iter("node") if n.get("package") == PACKAGE]


def exact_text(items, value):
    matches = [n for n in items if n.get("class") == "android.widget.TextView" and n.get("text") == value]
    if len(matches) != 1:
        raise ValueError("Expected exactly one local TextView: " + value)
    return matches[0]


def button_center(xml, description, width, height):
    if description not in BUTTONS.values():
        raise ValueError("Unrecognized control description")
    matches = [
        n for n in nodes(xml)
        if n.get("class") == "android.widget.Button"
        and n.get("content-desc") == description
        and n.get("enabled") == "true"
        and n.get("clickable") == "true"
        and n.get("visible-to-user", "true") == "true"
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one visible, enabled local control")
    match = BOUNDS.fullmatch(matches[0].get("bounds", ""))
    if not match:
        raise ValueError("Invalid bounds")
    x1, y1, x2, y2 = map(int, match.groups())
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise ValueError("Control bounds outside emulator display")
    return (x1 + x2) // 2, (y1 + y2) // 2


def assert_screen(xml, state):
    items = nodes(xml)
    if state == "initial":
        exact_text(items, TITLE)
        exact_text(items, INITIAL)
    elif state == "cleared":
        exact_text(items, CLEARED)
    elif state == "review":
        status = [n.get("text", "") for n in items
                  if n.get("class") == "android.widget.TextView"
                  and n.get("text", "").startswith("Offline sample rehearsal (no AI inference):")]
        if len(status) != 1:
            raise ValueError("Rehearsal status not uniquely visible")
        for token in ("State: REVIEW_REQUIRED", "Previewed: 0/3",
                      "Supervisor gate: BLOCKED_NO_ACTIVE_STEP",
                      "Authorized: No", "Device actions executed: No",
                      "No consent granted."):
            if token not in status[0]:
                raise ValueError("Rehearsal status missing invariant: " + token)
    else:
        raise ValueError("Unknown state")


def focused_button(xml):
    matches = [
        n.get("content-desc", "") for n in nodes(xml)
        if n.get("class") == "android.widget.Button"
        and n.get("focused") == "true"
        and n.get("enabled") == "true"
        and n.get("content-desc")
    ]
    if len(matches) != 1:
        raise ValueError("Expected one keyboard-focused labeled button")
    return matches[0]


def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: qa_ux008_agent_plan.py MODE XML [ARGUMENTS]")
    mode, path = sys.argv[1:3]
    xml = Path(path).read_text(encoding="utf-8")
    try:
        if mode == "button":
            if len(sys.argv) != 6:
                raise ValueError("button requires control key and display width/height")
            key, width, height = sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
            if key not in BUTTONS or width <= 0 or height <= 0:
                raise ValueError("Invalid control key or display")
            print(*button_center(xml, BUTTONS[key], width, height))
        elif mode == "screen":
            if len(sys.argv) != 4:
                raise ValueError("screen requires expected state")
            assert_screen(xml, sys.argv[3])
        elif mode == "focus":
            print(focused_button(xml))
        else:
            raise ValueError("Unknown command")
    except (ValueError, ET.ParseError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
