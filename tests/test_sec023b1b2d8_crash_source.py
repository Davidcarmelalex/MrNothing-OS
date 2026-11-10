"""SEC-023B1B2D8: offline crash-window isolation and exact-JUnit inventory."""
from pathlib import Path
import unittest

from scripts.qa023b1b2d3_unit_evidence import REQUIRED

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "android/app/src/main/java/tech/mrnothing/os"
SOURCE = APP / "MemoryVaultEnrollmentCrashPolicy.kt"
TEST = ROOT / "android/app/src/test/java/tech/mrnothing/os/MemoryVaultEnrollmentCrashPolicyTest.kt"


class EnrollmentCrashSourceTests(unittest.TestCase):
    def test_dormant_policy_has_no_runtime_callers_or_side_effects(self):
        callers = [
            p.name for p in APP.glob("*.kt")
            if p != SOURCE and "MemoryVaultEnrollmentCrashPolicy" in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(callers, [])
        text = SOURCE.read_text(encoding="utf-8")
        for forbidden in ("import android.", "KeyStore.getInstance(", "Cipher.getInstance(",
                          "File(", "writeAtomically(", "MemoryVaultService(",
                          "Runtime.getRuntime(", "STRUCTURALLY_COMPLETE_AUTHORIZED"):
            self.assertNotIn(forbidden, text)
        self.assertIn("STRUCTURALLY_COMPLETE_NOT_AUTHORIZED", text)
        self.assertIn("RECOVERY_REQUIRED_NOT_AUTHORIZED", text)

    def test_all_19_jvm_crash_methods_are_required_by_ci(self):
        methods = REQUIRED["MemoryVaultEnrollmentCrashPolicyTest"]
        self.assertEqual(len(methods), 19)
        source = TEST.read_text(encoding="utf-8")
        for name in methods:
            self.assertIn("@Test fun " + name + "(", source)

    def test_security_document_discloses_untrusted_provenance(self):
        doc = (ROOT / "docs/SEC-023B1B2D8-ENROLLMENT-CRASH-WINDOWS.md").read_text(encoding="utf-8")
        for phrase in ("caller-supplied", "rollback-resistant", "owner", "NOT AUTHORIZING"):
            self.assertIn(phrase, doc)


if __name__ == "__main__":
    unittest.main()
