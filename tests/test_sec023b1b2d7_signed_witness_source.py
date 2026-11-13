"""SEC-023B1B2D7: source-only signed witness refusal and CI inventory gates."""
from pathlib import Path
import unittest

from scripts.qa023b1b2d3_unit_evidence import REQUIRED

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "android/app/src/main/java/tech/mrnothing/os"
SOURCE = APP / "MemoryVaultSignedWitnessPolicy.kt"
TEST = ROOT / "android/app/src/test/java/tech/mrnothing/os/MemoryVaultSignedWitnessPolicyTest.kt"


class SignedWitnessSourceTests(unittest.TestCase):
    def test_only_dormant_offline_diagnostic_not_wired_to_runtime(self):
        users = [
            p.name for p in APP.glob("*.kt")
            if p != SOURCE and "MemoryVaultSignedWitnessPolicy" in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(users, [])
        text = SOURCE.read_text(encoding="utf-8")
        for forbidden in ("import android.", "MemoryVaultService(", "Cipher.getInstance(",
                          "KeyStore.getInstance(", "writeAtomically(", "Runtime.getRuntime("):
            self.assertNotIn(forbidden, text)
        self.assertIn("VERIFIED_PROVENANCE_NOT_AUTHORIZED", text)
        self.assertIn('Signature.getInstance("Ed25519")', text)
        self.assertIn("MessageDigest.isEqual(actualKeyDigest, pin)", text)
        self.assertIn("trustedHighWatermark", text)

    def test_twelve_signed_witness_junit_methods_required_by_ci(self):
        source = TEST.read_text(encoding="utf-8")
        required = REQUIRED["MemoryVaultSignedWitnessPolicyTest"]
        self.assertEqual(len(required), 12)
        for name in required:
            self.assertIn("@Test fun " + name + "(", source)

    def test_document_refuses_caller_supplied_trust_provenance(self):
        doc = (ROOT / "docs/SEC-023B1B2D7-SIGNED-WITNESS-PREFLIGHT.md").read_text(encoding="utf-8")
        self.assertIn("pin and high-watermark are still caller-supplied", doc)
        self.assertIn("rollback", doc.lower())
        self.assertIn("NOT AUTHORIZING", doc)


if __name__ == "__main__":
    unittest.main()
