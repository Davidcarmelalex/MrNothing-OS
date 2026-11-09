"""SEC-023B1B0: fail-closed, dormant Android Keystore inspection source gates."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "android/app/src/main/java/tech/mrnothing/os/MemoryVaultKeystorePreflight.kt"
MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"


class MemoryVaultKeystorePreflightSourceTest(unittest.TestCase):
    def test_inspection_is_read_only_and_does_not_expose_crypto_or_ipc(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('KeyStore.getInstance("AndroidKeyStore")', source)
        self.assertIn('getEntry(KEY_ALIAS, null)', source)
        self.assertIn('KeyInfo::class.java', source)
        self.assertNotRegex(source, r"\b(?:KeyGenerator|generateKey|setEntry|deleteEntry|Cipher|BiometricPrompt|Binder)\b")
        self.assertNotIn("setUserAuthenticationParameters(", source)

    def test_distinct_alias_and_strongbox_owner_auth_gates(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('mrnothing_memory_vault_aes_gcm_v1', source)
        self.assertNotIn('mrnothing_owner_consent_p256_v1', source)
        for required in (
            'SECURITY_LEVEL_STRONGBOX', 'AUTH_DEVICE_CREDENTIAL',
            'userAuthenticationValidityDurationSeconds == -1',
            'isUnlockedDeviceRequired', 'isRandomizedEncryptionRequired',
            'ORIGIN_GENERATED', 'PURPOSE_ENCRYPT', 'PURPOSE_DECRYPT',
            'BLOCK_MODE_GCM', 'ENCRYPTION_PADDING_NONE'
        ):
            self.assertIn(required, source)

    def test_preflight_not_integrated_with_existing_service_or_launcher(self):
        manifest = MANIFEST.read_text(encoding="utf-8")
        # This scoped branch intentionally does not import unmerged PR #16.
        self.assertNotIn('MemoryVaultService', manifest)
        for path in (
            ROOT / "android/app/src/main/java/tech/mrnothing/os/MainActivity.kt",
            ROOT / "android/app/src/main/java/tech/mrnothing/os/OwnerConsentSigner.kt",
        ):
            self.assertNotIn('MemoryVaultKeystorePreflight', path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
