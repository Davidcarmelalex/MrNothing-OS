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
SYSTEM_EDGE_GUARD_MIN_PX = 96
SYSTEM_EDGE_GUARD_DIVISOR = 20


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


def find_prompt_cancel_target(path):
    """Return a SystemUI outside-panel point below the credential content.

    The top gap in the captured API 35 hierarchy is only the status-bar inset;
    tapping there does not cancel the credential prompt. Prefer a point below
    both credential content containers and above the bottom system-UI guard.
    If that safe region is absent, fail closed rather than tapping an edge.
    """
    nodes = parse_hierarchy(path)
    matches = [
        node for node in nodes
        if node.get("package") == CANCEL_SURFACE_PACKAGE
        and node.get("resource-id") == CANCEL_SURFACE_RESOURCE_ID
        and node.get("class") == "android.widget.ImageView"
        and node.get("content-desc") == CANCEL_SURFACE_DESCRIPTION
        and node.get("clickable") == "true"
        and node.get("enabled") == "true"
        and node.get("visible-to-user", "true") == "true"
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one visible SystemUI authentication-cancel surface")
    screen_left, screen_top, screen_right, screen_bottom = _bounds(matches[0])
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

    panel_bounds = [_bounds(panel_nodes[0]) for panel_nodes in panels_by_id.values()]
    if any(
        left < screen_left or top < screen_top
        or right > screen_right or bottom > screen_bottom
        for left, top, right, bottom in panel_bounds
    ):
        raise ValueError("Credential panel bounds escape the cancel surface")

    panel_bottom = max(bounds[3] for bounds in panel_bounds)
    screen_height = screen_bottom - screen_top
    edge_guard = max(SYSTEM_EDGE_GUARD_MIN_PX, screen_height // SYSTEM_EDGE_GUARD_DIVISOR)
    safe_bottom = screen_bottom - edge_guard
    if panel_bottom >= safe_bottom:
        raise ValueError("No safe outside-panel region exists above the bottom system-UI guard")

    safe_y = panel_bottom + (safe_bottom - panel_bottom) // 2
    if not (panel_bottom < safe_y < safe_bottom):
        raise ValueError("Unable to derive an outside-panel cancel point")
    return (screen_left + screen_right) // 2, safe_y


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
        "button", "cancel-target", "status", "assert-probe", "assert-status",
        "assert-status-prefix", "assert-prompt-visible"
    ))
    parser.add_argument("xml")
    parser.add_argument("expected", nargs="?")
    args = parser.parse_args()
    try:
        if args.command == "button":
            if args.expected is None:
                raise ValueError("Button label is required")
            print(*find_button(args.xml, args.expected))
        elif args.command == "cancel-target":
            print(*find_prompt_cancel_target(args.xml))
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
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
