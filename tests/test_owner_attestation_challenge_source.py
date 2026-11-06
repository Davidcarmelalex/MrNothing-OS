"""SEC-014K source gates; synthetic checks do not prove Android attestation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"


class OwnerAttestationSourceTests(unittest.TestCase):
    def test_unpredictable_challenge_is_generated_and_bound_to_key(self):
        helper = (SRC / "OwnerAttestationChallenge.kt").read_text()
        enroll = (SRC / "OwnerKeyEnrollment.kt").read_text()
        self.assertIn("SecureRandom().nextBytes(it)", helper)
        self.assertIn("private const val NONCE_BYTES = 32", helper)
        self.assertIn(".setAttestationChallenge(challenge)", enroll)
        self.assertIn("OwnerAttestationChallenge.create()", enroll)

    def test_postgeneration_local_extension_must_match(self):
        enroll = (SRC / "OwnerKeyEnrollment.kt").read_text()
        self.assertIn("getExtensionValue(OwnerAttestationChallenge.EXTENSION_OID)", enroll)
        self.assertIn("matchesLocalEvidence(", enroll)
        self.assertIn("return OwnerEnrollmentResult.BLOCKED_KEYSTORE", enroll)

    def test_strongbox_levels_and_nonce_are_checked(self):
        helper = (SRC / "OwnerAttestationChallenge.kt").read_text()
        self.assertIn("key.securityLevel() != 2", helper)
        self.assertIn("MessageDigest.isEqual(nonce, expected)", helper)
        self.assertIn("MAX_EXTENSION_BYTES = 8192", helper)
        self.assertIn("key.finished()", helper)

    def test_no_signing_consent_issuer_or_network_added(self):
        helper = (SRC / "OwnerAttestationChallenge.kt").read_text()
        for forbidden in (
            "Signature.getInstance", "sign(", "deleteEntry(", "generateKeyPair(",
            "ConsentCapability(", "HttpURLConnection", "Socket(", "requestPermissions(",
        ):
            self.assertNotIn(forbidden, helper)


if __name__ == "__main__":
    unittest.main()
