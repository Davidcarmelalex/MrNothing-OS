"""SEC-014G source guards; no claim of Android runtime or hardware testing."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
FILE = SRC / "OwnerKeystorePreflight.kt"


class OwnerKeystorePreflightSourceTests(unittest.TestCase):
    def test_android_keystore_read_only_and_fixed_alias(self):
        code = FILE.read_text()
        for token in (
            'KeyStore.getInstance("AndroidKeyStore")',
            "getEntry(KEY_ALIAS, null)",
            'KEY_ALIAS = "mrnothing_owner_consent_p256_v1"',
            "KeyInfo::class.java",
            "info.isInsideSecureHardware",
            "Build.VERSION_CODES.S",
            "info.securityLevel == KeyProperties.SECURITY_LEVEL_STRONGBOX",
            "info.userAuthenticationType",
            "KeyProperties.AUTH_DEVICE_CREDENTIAL",
            "info.isUserAuthenticationRequired",
            "userAuthenticationValidityDurationSeconds",
        ):
            self.assertIn(token, code)

    def test_tee_or_unknown_level_never_meets_strongbox_gate(self):
        code = FILE.read_text()
        self.assertIn("signals.strongBoxBacked &&", code)
        self.assertIn("signals.credentialAuthAllowed &&", code)
        self.assertIn("SDK_INT < Build.VERSION_CODES.S", code)

    def test_no_key_creation_deletion_export_or_signing(self):
        code = FILE.read_text()
        for forbidden in (
            "KeyPairGenerator", "KeyGenerator", "generateKeyPair",
            "generateKey(", "deleteEntry(", "setEntry(", "setKeyEntry(",
            ".encoded", "Signature.getInstance", "Mac.getInstance",
            "Cipher.getInstance", "startActivityForResult", "requestPermissions(",
            "CommandRouter(", "ConsentCapability(", "Settings.Secure.put",
        ):
            self.assertNotIn(forbidden, code)

    def test_no_exposed_enrollment_or_agent_executor(self):
        code = FILE.read_text()
        self.assertIn("internal object OwnerKeystorePreflight", code)
        self.assertIn("EXISTING_KEY_REQUIRES_OWNER_AUTH", code)
        self.assertNotIn("fun enroll(", code)
        self.assertNotIn("fun execute(", code)
        manifest = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text()
        self.assertNotIn("OwnerKeystorePreflight", manifest)

    def test_no_key_or_consent_issuer_is_wired_to_preview(self):
        code = (SRC / "OwnerConsentPreviewActivity.kt").read_text()
        self.assertNotIn("OwnerKeystorePreflight", code)
        self.assertNotIn("generateKeyPair(", code)
        self.assertNotIn("ConsentCapability(", code)


if __name__ == "__main__":
    unittest.main()
