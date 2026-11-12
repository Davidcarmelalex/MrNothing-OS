"""Synthetic, offline tests for the M7 Pixel 9 Pro preflight validator."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.m7_pixel9pro_preflight import SCHEMA, STRONGBOX_FEATURE, evaluate_snapshot

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/m7_pixel9pro_preflight.py").read_text(encoding="utf-8")


def fixture():
    return {
        "schema": SCHEMA,
        "adb_state": "device",
        "properties": {
            "ro.product.manufacturer": "Google",
            "ro.product.model": "Pixel 9 Pro",
            "ro.product.device": "caiman",
            "ro.build.version.release": "16",
            "ro.build.version.sdk": "36",
            "ro.boot.flash.locked": "1",
            "ro.boot.verifiedbootstate": "green",
            "ro.boot.vbmeta.device_state": "locked",
            "ro.kernel.qemu": "0",
        },
        "features": ["feature:android.hardware.camera", STRONGBOX_FEATURE],
    }


class Pixel9ProPreflightTests(unittest.TestCase):
    def test_exact_secure_pixel_9_pro_is_preflight_ready_not_accepted(self):
        report = evaluate_snapshot(fixture())
        self.assertEqual(report["status"], "ready_for_supervised_hardware_session")
        self.assertTrue(report["preflight_passed"])
        self.assertFalse(report["acceptance_passed"])
        self.assertFalse(report["strongbox_key_security_level_verified"])

    def test_wrong_model_blocks(self):
        data = fixture(); data["properties"]["ro.product.model"] = "Pixel 9 Pro XL"
        report = evaluate_snapshot(data)
        self.assertEqual(report["status"], "blocked")
        self.assertIn("model_is_pixel_9_pro", report["blocked_reasons"])

    def test_wrong_codename_blocks(self):
        data = fixture(); data["properties"]["ro.product.device"] = "komodo"
        self.assertIn("codename_is_caiman", evaluate_snapshot(data)["blocked_reasons"])

    def test_wrong_manufacturer_blocks(self):
        data = fixture(); data["properties"]["ro.product.manufacturer"] = "Google LLC"
        self.assertIn("manufacturer_is_google", evaluate_snapshot(data)["blocked_reasons"])

    def test_unlocked_bootloader_blocks(self):
        data = fixture(); data["properties"]["ro.boot.flash.locked"] = "0"
        self.assertIn("bootloader_locked", evaluate_snapshot(data)["blocked_reasons"])

    def test_non_green_verified_boot_blocks(self):
        data = fixture(); data["properties"]["ro.boot.verifiedbootstate"] = "orange"
        self.assertIn("verified_boot_green", evaluate_snapshot(data)["blocked_reasons"])

    def test_unlocked_vbmeta_blocks(self):
        data = fixture(); data["properties"]["ro.boot.vbmeta.device_state"] = "unlocked"
        self.assertIn("vbmeta_device_locked", evaluate_snapshot(data)["blocked_reasons"])

    def test_missing_strongbox_feature_blocks_without_fallback(self):
        data = fixture(); data["features"] = ["feature:android.hardware.keystore"]
        report = evaluate_snapshot(data)
        self.assertIn("strongbox_feature_advertised", report["blocked_reasons"])
        self.assertFalse(report["strongbox_key_security_level_verified"])

    def test_emulator_blocks(self):
        data = fixture(); data["properties"]["ro.kernel.qemu"] = "1"
        self.assertIn("emulator_marker_not_positive", evaluate_snapshot(data)["blocked_reasons"])

    def test_missing_emulator_marker_is_not_physical_acceptance(self):
        data = fixture(); del data["properties"]["ro.kernel.qemu"]
        report = evaluate_snapshot(data)
        self.assertTrue(report["preflight_passed"])
        self.assertEqual(report["identity"]["emulator_marker"], "absent")
        self.assertFalse(report["acceptance_passed"])
        self.assertFalse(report["strongbox_key_security_level_verified"])

    def test_unknown_emulator_indicator_blocks(self):
        data = fixture(); data["properties"]["ro.kernel.qemu"] = "unknown"
        self.assertIn("emulator_marker_not_positive", evaluate_snapshot(data)["blocked_reasons"])

    def test_noncanonical_emulator_indicator_blocks(self):
        data = fixture(); data["properties"]["ro.kernel.qemu"] = "false"
        self.assertIn("emulator_marker_not_positive", evaluate_snapshot(data)["blocked_reasons"])

    def test_adb_unauthorized_blocks(self):
        data = fixture(); data["adb_state"] = "unauthorized"
        self.assertIn("adb_device_connected", evaluate_snapshot(data)["blocked_reasons"])

    def test_unknown_boot_state_blocks(self):
        data = fixture(); data["properties"]["ro.boot.verifiedbootstate"] = "unknown"
        self.assertIn("verified_boot_green", evaluate_snapshot(data)["blocked_reasons"])

    def test_api_below_pixel9_launch_baseline_blocks(self):
        data = fixture(); data["properties"]["ro.build.version.sdk"] = "33"
        self.assertIn("android_api_parseable", evaluate_snapshot(data)["blocked_reasons"])

    def test_malformed_api_is_rejected(self):
        data = fixture(); data["properties"]["ro.build.version.sdk"] = "36x"
        with self.assertRaises(ValueError):
            evaluate_snapshot(data)

    def test_missing_required_property_is_rejected(self):
        data = fixture(); del data["properties"]["ro.boot.flash.locked"]
        with self.assertRaises(ValueError):
            evaluate_snapshot(data)

    def test_wrong_schema_is_rejected(self):
        data = fixture(); data["schema"] = "other"
        with self.assertRaises(ValueError):
            evaluate_snapshot(data)

    def test_privacy_identifiers_are_not_echoed(self):
        data = fixture()
        data["serial"] = "SERIAL-DO-NOT-LEAK"
        data["properties"]["ro.serialno"] = "SERIAL-DO-NOT-LEAK"
        data["properties"]["persist.radio.imei"] = "IMEI-DO-NOT-LEAK"
        data["properties"]["ro.build.fingerprint"] = "private/fingerprint/value"
        rendered = json.dumps(evaluate_snapshot(data))
        for secret in ("SERIAL-DO-NOT-LEAK", "IMEI-DO-NOT-LEAK", "private/fingerprint/value"):
            self.assertNotIn(secret, rendered)

    def test_cli_writes_report_without_touching_adb(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "snapshot.json"
            output = Path(folder) / "report.json"
            source.write_text(json.dumps(fixture()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/m7_pixel9pro_preflight.py"),
                 "--snapshot", str(source), "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "ready_for_supervised_hardware_session")
            self.assertIn("NOT M7 acceptance", result.stdout)

    def test_source_is_offline_and_read_only(self):
        self.assertNotIn("subprocess", SCRIPT)
        self.assertNotIn("adb ", SCRIPT)
        self.assertNotIn("fastboot", SCRIPT)
        self.assertNotIn("os.system", SCRIPT)
        self.assertIn('"acceptance_passed": False', SCRIPT)


if __name__ == "__main__":
    unittest.main()
