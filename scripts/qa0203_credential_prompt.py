"""Strict UIAutomator assertions for the debug-only credential prompt probe."""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PACKAGE = "tech.mrnothing.os"
TITLE = "Device credential prompt probe"
BUTTONS = (
    "Authenticate with device credential",
    "Cancel prompt",
)
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\Z")
SYSTEM_PACKAGES = {"com.android.systemui", "com.android.settings"}
CANCEL_SURFACE_PACKAGE = "com.android.systemui"
CANCEL_SURFACE_RESOURCE_ID = "com.android.systemui:id/background"
CANCEL_SURFACE_DESCRIPTION = "Tap to cancel authentication"
PROMPT_PANEL_RESOURCE_IDS = {
    "com.android.systemui:id/auth_credential_header",
    "com.android.systemui:id/auth_credential_input",
}
CREDENTIAL_INPUT_RESOURCE_ID = "com.android.systemui:id/lockPassword"
SIDE_GUTTER_GUARD_PX = 48


def parse_hierarchy(path):
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise ValueError("Unable to parse UIAutomator hierarchy") from exc
    if root.tag != "hierarchy":
        raise ValueError("Expected UIAutomator hierarchy root")
    return list(root.iter("node"))


def _bounds(node):
    match = BOUNDS.fullmatch(node.get("bounds", ""))
    if not match:
        raise ValueError("Invalid UI node bounds")
    x1, y1, x2, y2 = map(int, match.groups())
    if x1 >= x2 or y1 >= y2:
        raise ValueError("Nonpositive UI node bounds")
    return x1, y1, x2, y2


def _center(node):
    if node.get("visible-to-user", "true") != "true":
        raise ValueError("Target node is not visible")
    match = BOUNDS.fullmatch(node.get("bounds", ""))
    if not match:
        raise ValueError("Invalid UI node bounds")
    x1, y1, x2, y2 = map(int, match.groups())
    if x1 >= x2 or y1 >= y2:
        raise ValueError("Nonpositive UI node bounds")
    return (x1 + x2) // 2, (y1 + y2) // 2


def find_button(path, label):
    nodes = parse_hierarchy(path)
    matches = [
        node for node in nodes
        if node.get("package") == PACKAGE
        and node.get("class") == "android.widget.Button"
        and (node.get("text") == label or node.get("content-desc") == label)
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one probe button: {label}")
    return _center(matches[0])


def find_prompt_cancel_gutter_target(path):
    """Return a point in the side gutter beside the actual credential EditText.

    The API 35 keyguard keypad occupies the lower screen even though its keys
    are not represented in the captured UIAutomator hierarchy. Never tap the
    bottom margin. Derive a side gutter from the unique lockPassword EditText,
    then reject any point overlapping another visible clickable SystemUI node.
    """
    nodes = parse_hierarchy(path)
    backgrounds = [
        node for node in nodes
        if node.get("package") == CANCEL_SURFACE_PACKAGE
        and node.get("resource-id") == CANCEL_SURFACE_RESOURCE_ID
        and node.get("class") == "android.widget.ImageView"
        and node.get("content-desc") == CANCEL_SURFACE_DESCRIPTION
        and node.get("clickable") == "true"
        and node.get("enabled") == "true"
        and node.get("visible-to-user", "true") == "true"
    ]
    if len(backgrounds) != 1:
        raise ValueError("Expected exactly one visible SystemUI authentication-cancel surface")
    background = backgrounds[0]
    screen_left, screen_top, screen_right, screen_bottom = _bounds(background)
    if (screen_left, screen_top) != (0, 0):
        raise ValueError("Authentication-cancel surface must cover the screen origin")

    panels_by_id = {
        resource_id: [
            node for node in nodes
            if node.get("package") == CANCEL_SURFACE_PACKAGE
            and node.get("resource-id") == resource_id
        ]
        for resource_id in PROMPT_PANEL_RESOURCE_IDS
    }
    if any(len(panel_nodes) != 1 for panel_nodes in panels_by_id.values()):
        raise ValueError("Credential header and input panels must each be uniquely present")
    input_container = _bounds(panels_by_id["com.android.systemui:id/auth_credential_input"][0])

    fields = [
        node for node in nodes
        if node.get("package") == CANCEL_SURFACE_PACKAGE
        and node.get("resource-id") == CREDENTIAL_INPUT_RESOURCE_ID
        and node.get("class") == "android.widget.EditText"
        and node.get("clickable") == "true"
        and node.get("enabled") == "true"
        and node.get("visible-to-user", "true") == "true"
    ]
    if len(fields) != 1:
        raise ValueError("Expected exactly one visible SystemUI credential input")
    field_left, field_top, field_right, field_bottom = _bounds(fields[0])
    if not (
        input_container[0] <= field_left < field_right <= input_container[2]
        and input_container[1] <= field_top < field_bottom <= input_container[3]
    ):
        raise ValueError("Credential input bounds escape their SystemUI container")
    if not (
        screen_left <= field_left < field_right <= screen_right
        and screen_top <= field_top < field_bottom <= screen_bottom
    ):
        raise ValueError("Credential input bounds escape the cancel surface")

    left_gutter = field_left - screen_left
    right_gutter = screen_right - field_right
    side, width = max((("left", left_gutter), ("right", right_gutter)), key=lambda item: item[1])
    if width <= SIDE_GUTTER_GUARD_PX * 2:
        raise ValueError("No sufficiently wide side gutter exists outside the credential input")
    x = screen_left + width // 2 if side == "left" else field_right + width // 2
    y = field_top + (field_bottom - field_top) // 2
    if field_left <= x <= field_right or not (
        screen_left < x < screen_right and screen_top < y < screen_bottom
    ):
        raise ValueError("Derived cancellation point overlaps credential input or screen edge")

    for node in nodes:
        if node is background or node.get("package") != CANCEL_SURFACE_PACKAGE:
            continue
        if (
            node.get("clickable") != "true"
            or node.get("enabled") != "true"
            or node.get("visible-to-user", "true") != "true"
        ):
            continue
        left, top, right, bottom = _bounds(node)
        if left <= x <= right and top <= y <= bottom:
            raise ValueError("Cancellation point overlaps another clickable SystemUI control")
    return x, y


def assert_no_credential_input(path):
    """Pass only if the prompt is gone or its credential EditText is still empty."""
    nodes = parse_hierarchy(path)
    fields = [
        node for node in nodes
        if node.get("package") == CANCEL_SURFACE_PACKAGE
        and node.get("resource-id") == CREDENTIAL_INPUT_RESOURCE_ID
        and node.get("class") == "android.widget.EditText"
    ]
    if len(fields) > 1:
        raise ValueError("Multiple SystemUI credential inputs are present")
    if fields and fields[0].get("text", "").strip():
        raise ValueError("Cancellation gesture changed the credential input")

def status(path):
    nodes = parse_hierarchy(path)
    matches = [
        node.get("text", "")
        for node in nodes
        if node.get("package") == PACKAGE
        and node.get("class") == "android.widget.TextView"
        and node.get("text", "").startswith("STATUS:")
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one probe status label")
    return matches[0]


def assert_probe(path):
    nodes = parse_hierarchy(path)
    titles = [
        node for node in nodes
        if node.get("package") == PACKAGE
        and node.get("class") == "android.widget.TextView"
        and node.get("text") == TITLE
    ]
    if len(titles) != 1 or status(path) != "STATUS: READY":
        raise ValueError("Credential probe is not in its initial ready state")
    for label in BUTTONS:
        find_button(path, label)


def assert_status(path, expected):
    actual = status(path)
    if actual != expected:
        raise ValueError(f"Expected status {expected!r}, received {actual!r}")


def assert_status_prefix(path, prefix):
    actual = status(path)
    if not actual.startswith(prefix):
        raise ValueError(f"Expected status prefix {prefix!r}, received {actual!r}")


def assert_prompt_visible(path):
    nodes = parse_hierarchy(path)
    for node in nodes:
        if node.get("package") not in SYSTEM_PACKAGES:
            continue
        text = (node.get("text", "") + " " + node.get("content-desc", "")).lower()
        if "pin" in text or "password" in text:
            return
    raise ValueError("System credential UI (PIN/password) was not visible")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=(
        "button", "cancel-gutter-target", "status", "assert-probe", "assert-status",
        "assert-status-prefix", "assert-prompt-visible", "assert-no-credential-input"
    ))
    parser.add_argument("xml")
    parser.add_argument("expected", nargs="?")
    args = parser.parse_args()
    try:
        if args.command == "button":
            if args.expected is None:
                raise ValueError("Button label is required")
            print(*find_button(args.xml, args.expected))
        elif args.command == "cancel-gutter-target":
            print(*find_prompt_cancel_gutter_target(args.xml))
        elif args.command == "status":
            print(status(args.xml))
        elif args.command == "assert-probe":
            assert_probe(args.xml)
        elif args.command == "assert-status":
            if args.expected is None:
                raise ValueError("Expected status is required")
            assert_status(args.xml, args.expected)
        elif args.command == "assert-status-prefix":
            if args.expected is None:
                raise ValueError("Expected status prefix is required")
            assert_status_prefix(args.xml, args.expected)
        elif args.command == "assert-prompt-visible":
            assert_prompt_visible(args.xml)
        elif args.command == "assert-no-credential-input":
            assert_no_credential_input(args.xml)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
