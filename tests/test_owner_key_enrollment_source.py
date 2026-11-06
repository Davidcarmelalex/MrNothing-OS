"""SEC-014H static security boundaries; no claim of Android runtime validation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"

class OwnerKeyEnrollmentSourceTests(unittest.TestCase):
    def test_explicit_local_entry_and_non_exported_activity(self):
        main = (SRC / "MainActivity.kt").read_text()
        manifest = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text()
        self.assertIn('addAction(root, "Enroll local hardware security key"', main)
        self.assertIn('android:name=".OwnerKeyEnrollmentActivity" android:exported="false"', manifest)
        self.assertNotIn('android.permission.BIND_ACCESSIBILITY_SERVICE', manifest)

    def test_strongbox_only_and_per_use_owner_auth(self):
        code = (SRC / "OwnerKeyEnrollment.kt").read_text()
        for token in ('KeyPairGenerator.getInstance(', '"AndroidKeyStore"',
                      'ECGenParameterSpec("secp256r1")', '.setIsStrongBoxBacked(true)',
                      '.setUserAuthenticationRequired(true)',
                      '.setUserAuthenticationParameters(', 'AUTH_DEVICE_CREDENTIAL',
                      'Build.VERSION_CODES.S',
                      'OwnerCredentialSafetyGate.isSafe(context)',
                      'store.containsAlias(OwnerKeystorePreflight.KEY_ALIAS)',
                      'OwnerKeystorePreflight.inspectExisting()'):
            self.assertIn(token, code)

    def test_no_consent_signing_deletion_or_agent_execution(self):
        for name in ('OwnerKeyEnrollment.kt', 'OwnerKeyEnrollmentActivity.kt'):
            code = (SRC / name).read_text()
            for forbidden in ('deleteEntry(', 'Signature.getInstance(', 'sign(', 'ConsentCapability(',
                              'CommandRouter(', 'requestPermissions(', 'Settings.Secure.put',
                              'getEncoded(', '.encoded', 'setIsStrongBoxBacked(false)'):
                self.assertNotIn(forbidden, code)

    def test_credential_and_overlay_gates(self):
        code = (SRC / 'OwnerKeyEnrollmentActivity.kt').read_text()
        for token in ('FLAG_SECURE', 'filterTouchesWhenObscured = true',
                      'OwnerConsentTouchGate.isUnobscured', 'state.revoke()',
                      'createConfirmDeviceCredentialIntent', 'state.finish(',
                      'OwnerCredentialSafetyGate.isSafe(this)'):
            self.assertIn(token, code)

    def test_preview_stays_isolated(self):
        preview = (SRC / 'OwnerConsentPreviewActivity.kt').read_text()
        self.assertNotIn('OwnerKeyEnrollment', preview)
        self.assertNotIn('generateKeyPair(', preview)

if __name__ == "__main__":
    unittest.main()
