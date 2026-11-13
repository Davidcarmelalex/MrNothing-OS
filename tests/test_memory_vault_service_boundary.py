"""SEC-023B1A source-only regression: disabled private Android component.

These tests do not execute Android Binder, Keystore, a Pixel, or an emulator.
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from scripts.android_manifest_gate import ANDROID, check_file, inspect_manifest

MANIFEST = Path("android/app/src/main/AndroidManifest.xml")
SERVICE = Path("android/app/src/main/java/tech/mrnothing/os/MemoryVaultService.kt")


class MemoryVaultServiceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.xml = MANIFEST.read_text(encoding="utf-8")

    def mutate(self, before, after):
        self.assertEqual(self.xml.count(before), 1)
        return inspect_manifest(ET.fromstring(self.xml.replace(before, after)))

    def test_checked_in_manifest_has_exactly_one_disabled_private_vault(self):
        self.assertEqual(check_file(MANIFEST), [])
        root = ET.fromstring(self.xml)
        services = [s for s in root.findall("application/service")
                    if s.get(ANDROID + "name") == ".MemoryVaultService"]
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0].get(ANDROID + "enabled"), "false")
        self.assertEqual(services[0].get(ANDROID + "exported"), "false")

    def test_enabled_service_is_rejected(self):
        self.assertIn("MemoryVaultService must remain disabled", self.mutate(
            'android:name=".MemoryVaultService" android:exported="false" android:enabled="false"',
            'android:name=".MemoryVaultService" android:exported="false" android:enabled="true"'))

    def test_exported_service_is_rejected(self):
        self.assertTrue(self.mutate(
            'android:name=".MemoryVaultService" android:exported="false"',
            'android:name=".MemoryVaultService" android:exported="true"'))

    def test_intent_filter_is_rejected(self):
        self.assertIn("MemoryVaultService must have no intent filters", self.mutate(
            '<service android:name=".MemoryVaultService" android:exported="false" android:enabled="false"/>',
            '<service android:name=".MemoryVaultService" android:exported="false" android:enabled="false">'
            '<intent-filter><action android:name="vault.OPEN"/></intent-filter></service>'))

    def test_process_and_permission_are_rejected(self):
        for attribute, value in (("process", ":vault"), ("permission", "android.permission.INTERNET"),
                                 ("foregroundServiceType", "dataSync"), ("isolatedProcess", "true")):
            with self.subTest(attribute=attribute):
                self.assertIn("MemoryVaultService forbidden attribute: " + attribute, self.mutate(
                    'android:name=".MemoryVaultService"',
                    f'android:name=".MemoryVaultService" android:{attribute}="{value}"'))

    def test_duplicate_vault_service_is_rejected(self):
        declaration = '<service android:name=".MemoryVaultService" android:exported="false" android:enabled="false"/>'
        self.assertIn("MemoryVaultService must not be duplicated", self.mutate(
            declaration, declaration + declaration))

    def test_direct_boot_access_is_rejected(self):
        self.assertIn("MemoryVaultService cannot be direct-boot aware", self.mutate(
            'android:name=".MemoryVaultService"',
            'android:name=".MemoryVaultService" android:directBootAware="true"'))

    def test_service_source_has_no_binder_or_persistence_path(self):
        source = SERVICE.read_text(encoding="utf-8")
        self.assertIn("override fun onBind(intent: Intent?): IBinder? = null", source)
        self.assertIn("stopSelfResult(startId)", source)
        self.assertIn("return START_NOT_STICKY", source)
        for forbidden in ("KeyStore.getInstance", "openFileOutput(", "startForeground(",
                          "Binder()", "FileOutputStream(", "SharedPreferences"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
