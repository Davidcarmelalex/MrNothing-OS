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


def parse_hierarchy(path):
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise ValueError("Unable to parse UIAutomator hierarchy") from exc
    if root.tag != "hierarchy":
        raise ValueError("Expected UIAutomator hierarchy root")
    return list(root.iter("node"))


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
        "button", "status", "assert-probe", "assert-status",
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
