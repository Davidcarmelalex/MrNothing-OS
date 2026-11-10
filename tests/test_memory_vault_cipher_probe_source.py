"""SEC-023B1B2D1 static guards; NOT AndroidKeyStore runtime proof."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
PROBE = (SRC / "MemoryVaultAuthenticatedCipherProbe.kt").read_text()
SERVICE = (SRC / "MemoryVaultService.kt").read_text()
MANIFEST = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text()


class MemoryVaultCipherProbeSourceTests(unittest.TestCase):
    def test_existing_keystore_key_and_no_software_fallback(self):
        for term in ('KeyStore.getInstance("AndroidKeyStore")',
                     'MemoryVaultKeystorePreflight.inspectExisting()',
                     'MemoryVaultKeystorePreflight.KEY_ALIAS',
                     'startsWith("AndroidKeyStore")',
                     'Cipher.getInstance("AES/GCM/NoPadding")'):
            self.assertIn(term, PROBE)
        for forbidden in ("KeyGenerator", "SecretKeySpec", "setIsStrongBoxBacked(false)"):
            self.assertNotIn(forbidden, PROBE)

    def test_canonical_digest_aad_and_empty_synthetic_plaintext(self):
        for term in ("cipher.updateAAD(aad)", "cipher.doFinal(ByteArray(0))",
                     "ByteArray(32)", "tag?.fill(0)", "aad?.fill(0)"):
            self.assertIn(term, PROBE)

    def test_callback_precedes_operation_and_replay_is_blocked(self):
        self.assertLess(PROBE.index("callbackGate.consume(consentDigest, result)"),
                        PROBE.index("cipher.doFinal(ByteArray(0))"))
        self.assertLess(PROBE.index("pendingCipher = null", PROBE.index("fun complete")),
                        PROBE.index("callbackGate.consume(consentDigest, result)"))
        self.assertIn("if (attempted) return null", PROBE)
        self.assertIn("callbackGate.revoke()", PROBE)

    def test_no_authorization_or_persistence_wiring(self):
        self.assertIn("CRYPTO_OPERATION_EXECUTED_NOT_AUTHORIZED", PROBE)
        for forbidden in ("GRANTED", "MemoryVaultService(", "startActivity(", "authenticate(",
                          "writeBytes(", "FileOutputStream", "PaperClip", "CommandRouter"):
            self.assertNotIn(forbidden, PROBE)
        self.assertNotIn("MemoryVaultAuthenticatedCipherProbe", SERVICE)

    def test_service_still_disabled(self):
        self.assertIn('android:name=".MemoryVaultService"', MANIFEST)
        self.assertIn('android:enabled="false"', MANIFEST)
        self.assertIn('android:exported="false"', MANIFEST)

    def test_hardware_and_consent_limits_disclosed(self):
        self.assertIn("NOT authorization", PROBE)
        self.assertIn("no prompt is launched", PROBE)
        self.assertIn("interoperability remain unverified", PROBE)


if __name__ == "__main__":
    unittest.main()
