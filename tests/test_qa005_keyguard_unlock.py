"""Unit tests for the QA-005 exact SystemUI Keyguard PIN hierarchy parser."""
from __future__ import annotations

import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from qa005_unlock_keyguard import (  # noqa: E402
    KEY_IDS,
    PIN_VIEW_ID,
    CONTAINER_ID,
    SUBMIT_ID,
    SYSTEM_UI,
    KeyguardUnlockError,
    capture_fresh_systemui_keypad_hierarchy,
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


    def test_capture_retries_null_root_with_unique_fresh_remote_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            hierarchy = Path(directory) / "keyguard.xml"
            dump_paths = []

            def fake_run(command, **kwargs):
                if command[-2:] == ["shell", "id"]:
                    return SimpleNamespace(returncode=0, stdout="uid=2000(shell)", stderr="")
                if command[-3:] == ["shell", "wm", "size"]:
                    return SimpleNamespace(returncode=0, stdout="Physical size: 1080x1920", stderr="")
                if command[-3] == "rm":
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                if command[-4:-1] == ["uiautomator", "dump", "--compressed"]:
                    remote = command[-1]
                    dump_paths.append(remote)
                    if len(dump_paths) == 1:
                        return SimpleNamespace(
                            returncode=0,
                            stdout="",
                            stderr="ERROR: null root node returned by UiTestAutomationBridge.",
                        )
                    return SimpleNamespace(
                        returncode=0,
                        stdout=f"UI hierchary dumped to: {remote}",
                        stderr="",
                    )
                if command[-3] == "pull":
                    Path(command[-1]).write_text(fixture_xml(), encoding="utf-8")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                raise AssertionError(f"Unexpected ADB command: {command}")

            with patch("qa005_unlock_keyguard.subprocess.run", side_effect=fake_run), patch(
                "qa005_unlock_keyguard.time.sleep"
            ) as sleep:
                attempts = capture_fresh_systemui_keypad_hierarchy("emulator-5554", hierarchy)

            self.assertEqual(attempts, 2)
            self.assertEqual(len(dump_paths), 2)
            self.assertEqual(len(set(dump_paths)), 2)
            self.assertTrue(hierarchy.is_file())
            sleep.assert_called_once_with(1)

    def test_capture_fails_closed_on_non_null_root_error(self):
        with tempfile.TemporaryDirectory() as directory:
            hierarchy = Path(directory) / "keyguard.xml"

            def fake_run(command, **kwargs):
                if command[-2:] == ["shell", "id"]:
                    return SimpleNamespace(returncode=0, stdout="uid=2000(shell)", stderr="")
                if command[-3:] == ["shell", "wm", "size"]:
                    return SimpleNamespace(returncode=0, stdout="Physical size: 1080x1920", stderr="")
                if command[-3] == "rm":
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                if command[-4:-1] == ["uiautomator", "dump", "--compressed"]:
                    return SimpleNamespace(returncode=1, stdout="", stderr="permission denied")
                raise AssertionError(f"Unexpected ADB command: {command}")

            with patch("qa005_unlock_keyguard.subprocess.run", side_effect=fake_run):
                with self.assertRaises(KeyguardUnlockError):
                    capture_fresh_systemui_keypad_hierarchy("emulator-5554", hierarchy)

            self.assertFalse(hierarchy.exists())

    def test_capture_has_a_hard_attempt_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            hierarchy = Path(directory) / "keyguard.xml"
            dump_count = 0

            def fake_run(command, **kwargs):
                nonlocal dump_count
                if command[-2:] == ["shell", "id"]:
                    return SimpleNamespace(returncode=0, stdout="uid=2000(shell)", stderr="")
                if command[-3:] == ["shell", "wm", "size"]:
                    return SimpleNamespace(returncode=0, stdout="Physical size: 1080x1920", stderr="")
                if command[-3] == "rm":
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                if command[-4:-1] == ["uiautomator", "dump", "--compressed"]:
                    dump_count += 1
                    return SimpleNamespace(
                        returncode=0,
                        stdout="",
                        stderr="ERROR: null root node returned by UiTestAutomationBridge.",
                    )
                raise AssertionError(f"Unexpected ADB command: {command}")

            with patch("qa005_unlock_keyguard.subprocess.run", side_effect=fake_run), patch(
                "qa005_unlock_keyguard.time.sleep"
            ) as sleep:
                with self.assertRaises(KeyguardUnlockError):
                    capture_fresh_systemui_keypad_hierarchy("emulator-5554", hierarchy)

            self.assertEqual(dump_count, 5)
            self.assertEqual(sleep.call_count, 4)



if __name__ == "__main__":
    unittest.main()
