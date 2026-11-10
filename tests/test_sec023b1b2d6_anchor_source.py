"""SEC-023B1B2D6 source-level non-wiring and JUnit evidence inventory."""
from pathlib import Path
import unittest
from scripts.qa023b1b2d3_unit_evidence import REQUIRED

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "android/app/src/main/java/tech/mrnothing/os/MemoryVaultGenerationAnchorPolicy.kt"
TEST = ROOT / "android/app/src/test/java/tech/mrnothing/os/MemoryVaultGenerationAnchorPolicyTest.kt"

class AnchorPreflightSourceTests(unittest.TestCase):
    def test_is_diagnostic_only_and_no_android_keystore_or_storage(self):
        text = MAIN.read_text(encoding="utf-8")
        self.assertIn("CONSISTENT_INPUTS_NOT_AUTHORIZED", text)
        self.assertIn("RECOVERY_REQUIRED_NOT_AUTHORIZED", text)
        for forbidden in ("import android.", "KeyStore.getInstance(", "writeAtomically(", "MemoryVaultService(", "Cipher.getInstance("):
            self.assertNotIn(forbidden, text)

    def test_all_new_junit_methods_are_required_by_ci(self):
        source = TEST.read_text(encoding="utf-8")
        required = REQUIRED["MemoryVaultGenerationAnchorPolicyTest"]
        self.assertEqual(len(required), 17)
        for name in required:
            self.assertIn("@Test fun " + name + "(", source)

    def test_policy_not_wired_to_application_runtime(self):
        name = "MemoryVaultGenerationAnchorPolicy"
        app = ROOT / "android/app/src/main/java/tech/mrnothing/os"
        users = [p.name for p in app.glob("*.kt") if p != MAIN and name in p.read_text(encoding="utf-8")]
        self.assertEqual(users, [])

    def test_security_document_records_forged_witness_limitation(self):
        text = (ROOT / "docs/SEC-023B1B2D6-GENERATION-ANCHOR-PREFLIGHT.md").read_text(encoding="utf-8")
        self.assertIn("replacement of *all three* inputs", text)
        self.assertIn("not", text.lower())
        self.assertIn("per-use consent separately", text)
