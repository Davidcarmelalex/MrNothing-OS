"""SEC-023B1B1 source-only checks, not Android runtime security proof."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os/MemoryVaultProvisioningPolicy.kt"


class MemoryVaultProvisioningSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SRC.read_text(encoding="utf-8")

    def test_strongbox_no_fallback(self):
        self.assertIn(".setIsStrongBoxBacked(true)", self.source)
        self.assertNotIn(".setIsStrongBoxBacked(false)", self.source)

    def test_per_use_credential_only(self):
        self.assertIn("0, KeyProperties.AUTH_DEVICE_CREDENTIAL", self.source)
        self.assertNotIn("AUTH_BIOMETRIC_STRONG", self.source)

    def test_gcm_and_randomized_iv(self):
        for value in (
            ".setKeySize(256)",
            ".setBlockModes(KeyProperties.BLOCK_MODE_GCM)",
            ".setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)",
            ".setRandomizedEncryptionRequired(true)",
            ".setUnlockedDeviceRequired(true)",
        ):
            self.assertIn(value, self.source)

    def test_no_key_operations_or_call_sites(self):
        for forbidden in ("generateKey(", "deleteEntry(", "setEntry(", 'getInstance("AndroidKeyStore")'):
            self.assertNotIn(forbidden, self.source)
        for path in SRC.parent.glob("*.kt"):
            if path != SRC:
                self.assertNotIn("MemoryVaultKeySpecDraft.forSecurityReview(",
                                 path.read_text(encoding="utf-8"))

    def test_no_persistence_or_ipc_surface(self):
        for forbidden in ("android.permission.", "onBind(", "openFileOutput(",
                          "FileOutputStream(", "SharedPreferences", "Cipher.getInstance("):
            self.assertNotIn(forbidden, self.source)


if __name__ == "__main__":
    unittest.main()
