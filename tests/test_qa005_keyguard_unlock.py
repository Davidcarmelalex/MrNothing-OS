"""Unit tests for the QA-005 exact SystemUI Keyguard PIN hierarchy parser."""
from __future__ import annotations

import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from qa005_unlock_keyguard import (  # noqa: E402
    KEY_IDS,
    PIN_VIEW_ID,
    CONTAINER_ID,
    SUBMIT_ID,
    SYSTEM_UI,
    KeyguardUnlockError,
    collect_keypad_centers,
    parse_display_size,
)


def fixture_xml(
    *,
    wrong_package_id: str | None = None,
    bad_attribute: tuple[str, str, str] | None = None,
    missing_digit: str | None = None,
    duplicate_digit: str | None = None,
    out_of_bounds_id: str | None = None,
) -> str:
    root = ET.Element("hierarchy", {"rotation": "0"})
    pin = ET.SubElement(
        root,
        "node",
        {
            "package": SYSTEM_UI,
            "resource-id": PIN_VIEW_ID,
            "enabled": "true",
            "bounds": "[0,0][1080,1920]",
        },
    )
    container = ET.SubElement(
        pin,
        "node",
        {
            "package": SYSTEM_UI,
            "resource-id": CONTAINER_ID,
            "enabled": "true",
            "bounds": "[100,300][980,1400]",
        },
    )
    for digit in range(10):
        label = str(digit)
        resource_id = KEY_IDS[label]
        if label == missing_digit:
            continue
        x = 100 + digit * 80
        bounds = f"[{x},400][{x + 50},450]"
        if resource_id == out_of_bounds_id:
            bounds = "[1070,400][1100,450]"
        package = "com.example.untrusted" if resource_id == wrong_package_id else SYSTEM_UI
        attrs = {
            "package": package,
            "resource-id": resource_id,
            "enabled": "true",
            "clickable": "true",
            "bounds": bounds,
        }
        if bad_attribute and bad_attribute[0] == resource_id:
            attrs[bad_attribute[1]] = bad_attribute[2]
        ET.SubElement(container, "node", attrs)
        if label == duplicate_digit:
            duplicate = dict(attrs)
            duplicate["bounds"] = f"[{x + 10},500][{x + 60},550]"
            ET.SubElement(container, "node", duplicate)

    submit_attrs = {
        "package": SYSTEM_UI,
        "resource-id": SUBMIT_ID,
        "enabled": "true",
        "clickable": "true",
        "bounds": "[800,1300][900,1400]",
    }
    if bad_attribute and bad_attribute[0] == SUBMIT_ID:
        submit_attrs[bad_attribute[1]] = bad_attribute[2]
    ET.SubElement(container, "node", submit_attrs)
    return ET.tostring(root, encoding="unicode")


class Qa005KeyguardUnlockTests(unittest.TestCase):
    def _parse(self, xml: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hierarchy.xml"
            path.write_text(xml, encoding="utf-8")
            return collect_keypad_centers(path, 1080, 1920)

    def test_accepts_exact_complete_systemui_pin_hierarchy(self):
        centers = self._parse(fixture_xml())
        self.assertEqual(set(centers), set(KEY_IDS) | {"enter"})
        self.assertTrue(all(0 <= x < 1080 and 0 <= y < 1920 for x, y in centers.values()))

    def test_rejects_wrong_package_digit_control(self):
        with self.assertRaises(KeyguardUnlockError):
            self._parse(fixture_xml(wrong_package_id=KEY_IDS["4"]))

    def test_rejects_disabled_digit_control(self):
        with self.assertRaises(KeyguardUnlockError):
            self._parse(fixture_xml(bad_attribute=(KEY_IDS["2"], "enabled", "false")))

    def test_rejects_nonclickable_submit_control(self):
        with self.assertRaises(KeyguardUnlockError):
            self._parse(fixture_xml(bad_attribute=(SUBMIT_ID, "clickable", "false")))

    def test_rejects_missing_digit_control(self):
        with self.assertRaises(KeyguardUnlockError):
            self._parse(fixture_xml(missing_digit="7"))

    def test_rejects_duplicate_visible_digit_control(self):
        with self.assertRaises(KeyguardUnlockError):
            self._parse(fixture_xml(duplicate_digit="1"))

    def test_rejects_out_of_screen_bounds(self):
        with self.assertRaises(KeyguardUnlockError):
            self._parse(fixture_xml(out_of_bounds_id=KEY_IDS["1"]))

    def test_rejects_invalid_display_dimensions(self):
        with self.assertRaises(KeyguardUnlockError):
            collect_keypad_centers(Path("unused"), 0, 1920)
        self.assertEqual(parse_display_size("Physical size: 1080x1920"), (1080, 1920))
        with self.assertRaises(KeyguardUnlockError):
            parse_display_size("Physical size: unknown")


if __name__ == "__main__":
    unittest.main()
