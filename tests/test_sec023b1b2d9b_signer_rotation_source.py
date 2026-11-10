"""SEC-023B1B2D9B: offline dual-signer rotation proof must stay non-authorizing."""
from pathlib import Path
import unittest
from scripts.qa023b1b2d3_unit_evidence import REQUIRED

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "android/app/src/main/java/tech/mrnothing/os"
SRC = APP / "MemoryVaultSignerRotationProof.kt"
TEST = ROOT / "android/app/src/test/java/tech/mrnothing/os/MemoryVaultSignerRotationProofTest.kt"


class SignerRotationSourceTests(unittest.TestCase):
    def test_dormant_no_android_or_runtime_callers(self):
        callers = [p.name for p in APP.glob("*.kt") if p != SRC and
                   "MemoryVaultSignerRotationProof" in p.read_text(encoding="utf-8")]
        self.assertEqual(callers, [])
        source = SRC.read_text(encoding="utf-8")
        for forbidden in ("import android.", "KeyStore.getInstance", "FileOutputStream",
                          "MemoryVaultService(", "CommandRouter", "startActivity(",
                          "Runtime.getRuntime", "ROTATION_AUTHORIZED"):
            self.assertNotIn(forbidden, source)
        self.assertIn("DUAL_SIGNATURES_VALID_NOT_AUTHORIZED", source)

    def test_exact_junit_inventory(self):
        methods = REQUIRED["MemoryVaultSignerRotationProofTest"]
        self.assertEqual(len(methods), 23)
        source = TEST.read_text(encoding="utf-8")
        for name in methods:
            self.assertIn("@Test fun " + name + "(", source)

    def test_explicit_provenance_and_rollback_limitations(self):
        doc = (ROOT / "docs/SEC-023B1B2D9B-SIGNER-ROTATION-PROOF.md").read_text()
        for phrase in ("NOT AUTHORIZING", "independently authenticated",
                       "rollback-resistant", "physical Pixel 9 Pro", "SKILL.md"):
            self.assertIn(phrase, doc)


if __name__ == "__main__":
    unittest.main()
