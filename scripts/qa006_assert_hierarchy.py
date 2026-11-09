#!/usr/bin/env python3
"""QA-006: require actual larger launcher heading bounds at 200% font scale.

Uses uiautomator XML from an Android emulator. It is not a TalkBack test.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BOUNDS = re.compile(r"^\[(\d+),(\d+)\]\[(\d+),(\d+)\]$")


def heading_height(path: Path) -> int:
    root = ET.parse(path).getroot()
    for node in root.iter("node"):
        if node.attrib.get("text") == "MR. NOTHING":
            match = BOUNDS.fullmatch(node.attrib.get("bounds", ""))
            if match is None:
                raise ValueError("launcher heading lacks valid bounds")
            left, top, right, bottom = map(int, match.groups())
            if right <= left or bottom <= top:
                raise ValueError("launcher heading bounds are empty")
            return bottom - top
    raise ValueError("MR. NOTHING heading missing from hierarchy")


def verify(normal: Path, large: Path) -> tuple[int, int]:
    normal_height, large_height = heading_height(normal), heading_height(large)
    if large_height <= normal_height:
        raise ValueError(
            f"200% font did not increase heading height: {normal_height} -> {large_height}"
        )
    return normal_height, large_height


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: qa006_assert_hierarchy.py NORMAL.xml LARGE.xml")
    before, after = verify(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"QA-006 PASS: heading bounds grew from {before}px to {after}px")
