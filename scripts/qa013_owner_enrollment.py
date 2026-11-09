"""Strict local UI hierarchy assertions for emulator QA-013."""
import argparse
import re
import xml.etree.ElementTree as ET

BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\Z")


def find_button(xml, description):
    nodes = [n for n in ET.fromstring(xml).iter("node")
             if n.get("package") == "tech.mrnothing.os"
             and n.get("class") == "android.widget.Button"
             and n.get("content-desc") == description
             and n.get("enabled") == "true"
             and n.get("clickable") == "true"]
    if len(nodes) != 1:
        raise ValueError("Expected one enabled local button")
    bounds = BOUNDS.fullmatch(nodes[0].get("bounds", ""))
    if not bounds:
        raise ValueError("Invalid bounds")
    x1, y1, x2, y2 = map(int, bounds.groups())
    if x1 >= x2 or y1 >= y2:
        raise ValueError("Nonpositive bounds")
    return (x1+x2)//2, (y1+y2)//2


def assert_status(xml, expected):
    nodes = [n for n in ET.fromstring(xml).iter("node")
             if n.get("package") == "tech.mrnothing.os"
             and n.get("class") == "android.widget.TextView"
             and n.get("text") == expected]
    if len(nodes) != 1:
        raise ValueError("Expected exactly one local status")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("find", "status"))
    p.add_argument("path")
    p.add_argument("value")
    a = p.parse_args()
    with open(a.path, encoding="utf-8") as f:
        content = f.read()
    if a.mode == "find":
        print(*find_button(content, a.value))
    else:
        assert_status(content, a.value)
        print("Local status verified")
