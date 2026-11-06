from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SIGNER = ROOT / "android/app/src/main/java/tech/mrnothing/os/OwnerConsentSigner.kt"
ROUTER = ROOT / "android/app/src/main/java/tech/mrnothing/os/CommandRouter.kt"
MAIN = ROOT / "android/app/src/main/java/tech/mrnothing/os/MainActivity.kt"


class OwnerConsentSignerSourceTests(unittest.TestCase):
    def test_signer_requires_existing_strongbox_readiness_and_fixed_alias(self):
        source = SIGNER.read_text(encoding="utf-8")
        self.assertIn("OwnerKeystorePreflight.inspectExisting()", source)
        self.assertIn("OwnerKeystorePreflight.KEY_ALIAS", source)
        self.assertIn('KeyStore.getInstance("AndroidKeyStore")', source)
        self.assertNotIn("KeyPairGenerator", source)
        self.assertNotIn("generateKeyPair", source)

    def test_signing_operation_is_bound_to_system_crypto_object(self):
        source = SIGNER.read_text(encoding="utf-8")
        self.assertIn('Signature.getInstance("SHA256withECDSA")', source)
        self.assertIn("BiometricPrompt.CryptoObject(signature)", source)
        self.assertIn("setAllowedAuthenticators(authenticators)", source)
        self.assertIn("CancellationSignal()", source)
        self.assertIn("onAuthenticationSucceeded", source)
        self.assertIn("onAuthenticationError", source)

    def test_signer_is_not_connected_to_command_execution(self):
        self.assertNotIn("OwnerConsentSigner", ROUTER.read_text(encoding="utf-8"))
        self.assertNotIn("OwnerConsentSigner", MAIN.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
