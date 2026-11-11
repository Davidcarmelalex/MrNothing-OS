"""SEC-023B1B2D5 static contract; NOT StrongBox or owner-auth proof."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
VERIFIER = (SRC / "MemoryVaultGenerationCanaryVerifier.kt").read_text()
PROBE = (SRC / "MemoryVaultAuthenticatedCipherProbe.kt").read_text()
SERVICE = (SRC / "MemoryVaultService.kt").read_text()
TEST = (ROOT / "android/app/src/test/java/tech/mrnothing/os/MemoryVaultGenerationCanaryVerifierTest.kt").read_text()
GATE = (ROOT / "scripts/qa023b1b2d3_unit_evidence.py").read_text()


class MemoryVaultGenerationCanarySourceTests(unittest.TestCase):
    def test_pure_offline_no_runtime_wiring(self):
        for forbidden in ("KeyStore.getInstance", "KeyGenerator", "SecretKeySpec",
                          "FileOutputStream", "MemoryVaultService(", "BiometricPrompt",
                          "startActivity(", "CommandRouter", "PaperClip"):
            self.assertNotIn(forbidden, VERIFIER)
        self.assertNotIn("MemoryVaultGenerationCanaryVerifier", PROBE)
        self.assertNotIn("MemoryVaultGenerationCanaryVerifier", SERVICE)

    def test_aead_and_non_authorizing_outcome(self):
        for required in ("decryptCipher.updateAAD(aad)", "decryptCipher.doFinal(ciphertext)",
                         "MessageDigest.isEqual", "REFERENCE_MATCH_NOT_AUTHORIZED",
                         "NONCE_BYTES = 12", "ID_BYTES = 32", "TAG_BYTES = 16",
                         "plaintext?.fill(0)"):
            self.assertIn(required, VERIFIER)
        self.assertNotIn("GRANTED", VERIFIER)

    def test_adversarial_methods_required_in_hosted_junit_gate(self):
        for method in ("replacedSamePolicyKeyIsRejected", "modifiedCiphertextIsRejected",
                       "modifiedGenerationIdIsRejected", "modifiedConsentDigestIsRejected",
                       "wrongNonceIsRejected", "missingReferenceIsRejected",
                       "truncatedTagIsRejected", "arbitraryPlaintextIsRejected"):
            self.assertIn("fun " + method, TEST)
            self.assertIn('"' + method + '"', GATE)


if __name__ == "__main__":
    unittest.main()
