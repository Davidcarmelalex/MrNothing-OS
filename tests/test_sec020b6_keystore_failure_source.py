from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BACKEND = (ROOT / "android/app/src/main/java/tech/mrnothing/os/AndroidAuthorityTrustBackend.kt").read_text()
INSTRUMENTATION = (
    ROOT / "android/app/src/androidTest/java/tech/mrnothing/os/AndroidAuthorityTrustCryptoFailureModeTest.kt"
).read_text()


class AndroidAuthorityTrustCryptoFailureSourceTests(unittest.TestCase):
    def test_production_keystore_alias_defaults_are_preserved(self):
        self.assertIn('private const val DEFAULT_AES_ALIAS = "mrnothing_authority_record_aes_v1"', BACKEND)
        self.assertIn('private const val DEFAULT_MARKER_PREFIX = "mrnothing_authority_marker_v1_"', BACKEND)
        self.assertIn("AndroidAuthorityTrustCrypto()", BACKEND)
        self.assertIn('KeyPairGenerator.getInstance("Ed25519", BouncyCastleProvider())', INSTRUMENTATION)

    def test_both_generation_marker_and_aes_keys_require_strongbox(self):
        self.assertEqual(2, BACKEND.count(".setIsStrongBoxBacked(true)"))
        self.assertNotIn(".setIsStrongBoxBacked(false)", BACKEND)
        self.assertIn(
            "info.securityLevel == KeyProperties.SECURITY_LEVEL_STRONGBOX",
            BACKEND,
        )

    def test_marker_aliases_must_be_positive_canonical_decimal(self):
        self.assertIn("suffix.toLongOrNull() ?: return null", BACKEND)
        self.assertIn("generation <= 0L || generation.toString() != suffix", BACKEND)

    def test_test_alias_namespace_is_unique_and_cleaned(self):
        self.assertIn("UUID.randomUUID()", INSTRUMENTATION)
        self.assertIn("mrnothing_sec020b6_", INSTRUMENTATION)
        self.assertIn("cleanup.deleteEntry(alias)", INSTRUMENTATION)
        self.assertIn("cleanup.deleteEntry(aesAlias)", INSTRUMENTATION)

    def test_strongbox_absence_is_checked_without_tee_fallback(self):
        self.assertIn("PackageManager.FEATURE_STRONGBOX_KEYSTORE", INSTRUMENTATION)
        self.assertIn('assertNull("StrongBox absence must fail closed", proof)', INSTRUMENTATION)
        self.assertIn("no TEE marker alias may be created as a fallback", INSTRUMENTATION)

    def test_emulator_negative_cases_are_explicit(self):
        for name in (
            "testMissingMarkerAliasCannotVerifyAProof",
            "testMalformedMarkerSuffixMakesTrustStoreUnavailable",
            "testNonCanonicalGenerationSuffixMakesTrustStoreUnavailable",
            "testZeroGenerationMarkerMakesTrustStoreUnavailable",
            "testTeeOnlyMarkerCannotBecomeGenerationWatermark",
            "testEncryptionKeyWithoutAnyMarkerIsNotFreshInstall",
            "testWrongKeyTypeUnderMarkerPrefixIsRejected",
        ):
            self.assertIn(name, INSTRUMENTATION)


if __name__ == "__main__":
    unittest.main()
