"""SEC-023B1B2D0: static fail-closed guards; not runtime CryptoObject proof."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
ANDROID = (SRC / "MemoryVaultCryptoObjectCallbackGate.kt").read_text(encoding="utf-8")
SERVICE = (SRC / "MemoryVaultService.kt").read_text(encoding="utf-8")
MANIFEST = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")

class MemoryVaultCryptoCallbackSourceTests(unittest.TestCase):
    def test_result_is_derived_from_platform_callback_not_reported_boolean(self):
        self.assertIn("BiometricPrompt.AuthenticationResult?", ANDROID)
        self.assertIn("result?.cryptoObject", ANDROID)
        self.assertIn("result?.authenticationType", ANDROID)
        self.assertIn("AUTHENTICATION_RESULT_TYPE_DEVICE_CREDENTIAL", ANDROID)
        self.assertNotIn("platformCredentialReported", ANDROID)

    def test_one_shot_identity_and_monotonic_deadline(self):
        for term in ("resultObject === active.promptObject", "resultCipher === active.cipher",
                     "pending = null", "now >= active.startedNanos",
                     "now - active.startedNanos <= MAX_AGE_NANOS",
                     "consentDigest == active.consentDigest"):
            self.assertIn(term, ANDROID)

    def test_never_grants_persistence_or_uses_a_key(self):
        self.assertIn("AWAITING_AUTHENTICATED_CIPHER_OPERATION", ANDROID)
        for forbidden in ("GRANTED", "KeyGenerator", "doFinal(", "KeyStore.getInstance",
                          "Cipher.getInstance", "startActivity(", "authenticate("):
            self.assertNotIn(forbidden, ANDROID)
        self.assertNotIn("MemoryVaultCryptoObjectCallbackGate", SERVICE)

    def test_service_stays_disabled(self):
        self.assertIn('android:name=".MemoryVaultService"', MANIFEST)
        self.assertIn('android:enabled="false"', MANIFEST)
        self.assertIn('android:exported="false"', MANIFEST)

if __name__ == "__main__":
    unittest.main()
