"""SEC-023B1B0: fail-closed, dormant Android Keystore inspection source gates."""
import pathlib
import re
import unittest
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "android/app/src/main/java/tech/mrnothing/os/MemoryVaultKeystorePreflight.kt"
MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"


class MemoryVaultKeystorePreflightSourceTest(unittest.TestCase):
    def test_inspection_is_read_only_and_does_not_expose_crypto_or_ipc(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('KeyStore.getInstance("AndroidKeyStore")', source)
        self.assertIn('getEntry(KEY_ALIAS, null)', source)
        self.assertIn('KeyInfo::class.java) as? KeyInfo', source)
        self.assertNotRegex(source, r"\b(?:KeyGenerator|generateKey|setEntry|deleteEntry|Cipher|BiometricPrompt|Binder)\b")
        self.assertNotIn("setUserAuthenticationParameters(", source)

    def test_distinct_alias_and_strongbox_owner_auth_gates(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('mrnothing_memory_vault_aes_gcm_v1', source)
        self.assertNotIn('mrnothing_owner_consent_p256_v1', source)
        for required in (
            'SECURITY_LEVEL_STRONGBOX', 'AUTH_DEVICE_CREDENTIAL',
            'userAuthenticationValidityDurationSeconds == -1',
            'ORIGIN_GENERATED', 'PURPOSE_ENCRYPT', 'PURPOSE_DECRYPT',
            'BLOCK_MODE_GCM', 'ENCRYPTION_PADDING_NONE'
        ):
            self.assertIn(required, source)

    def test_does_not_invent_unavailable_keyinfo_signals(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("info.isUnlockedDeviceRequired", source)
        self.assertNotIn("info.isRandomizedEncryptionRequired", source)
        self.assertIn("KeyInfo does not", source)

    def test_preflight_remains_disconnected_from_disabled_service_and_launcher(self):
        # The reconciled composite retains exactly one disabled private service.
        # Assert the actual XML boundary rather than the former PR-local absence.
        namespace = "{http://schemas.android.com/apk/res/android}"
        application = ET.parse(MANIFEST).getroot().find("application")
        self.assertIsNotNone(application)
        services = [
            node for node in application.findall("service")
            if node.get(namespace + "name") in (
                ".MemoryVaultService", "tech.mrnothing.os.MemoryVaultService")
        ]
        self.assertEqual(1, len(services))
        self.assertEqual("false", services[0].get(namespace + "enabled"))
        self.assertEqual("false", services[0].get(namespace + "exported"))
        self.assertEqual([], services[0].findall("intent-filter"))
        for path in (
            ROOT / "android/app/src/main/java/tech/mrnothing/os/MemoryVaultService.kt",
            ROOT / "android/app/src/main/java/tech/mrnothing/os/MainActivity.kt",
            ROOT / "android/app/src/main/java/tech/mrnothing/os/OwnerConsentSigner.kt",
        ):
            self.assertNotIn("MemoryVaultKeystorePreflight", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
