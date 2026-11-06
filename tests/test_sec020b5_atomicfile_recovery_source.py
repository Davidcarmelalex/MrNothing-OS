"""SEC-020B5 source gates for Android AtomicFile interruption semantics."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "android/app/src/androidTest/java/tech/mrnothing/os/AndroidAtomicAuthorityRecordPersistenceTest.kt"
DOC = ROOT / "docs/SEC-020B5-ATOMICFILE-RECOVERY.md"


class Sec020B5AtomicFileRecoverySourceTests(unittest.TestCase):
    def test_interrupted_first_write_is_classified_by_marker_aware_store(self):
        source = TEST.read_text(encoding="utf-8")
        start = source.index("fun testInterruptedFirstWriteLeavesNoCommittedRecordButMarkerRequiresRecovery")
        end = source.index("\n    fun ", start + 8)
        case = source[start:end]
        self.assertIn("AuthorityRecordRead.Missing", case)
        self.assertIn("MarkerOnlyCrypto(highestGeneration = 1L)", case)
        self.assertIn("AuthorityRecoveryReason.ACTIVE_RECORD_MISSING", case)
        self.assertIn("AuthorityTrustStoreState.RecoveryRequired", case)
        self.assertNotIn("AuthorityRecordRead.Present", case)

    def test_marker_only_fixture_cannot_create_or_verify_trust_material(self):
        source = TEST.read_text(encoding="utf-8")
        start = source.index("private class MarkerOnlyCrypto")
        end = source.index("\n    private fun withPersistence", start)
        fixture = source[start:end]
        self.assertIn("override fun highestObservedGeneration(): Long = highestGeneration", fixture)
        self.assertIn("override fun createGenerationMarker", fixture)
        self.assertIn("override fun verifyGenerationMarker", fixture)
        self.assertIn("override fun encrypt", fixture)
        self.assertIn("override fun decrypt", fixture)
        self.assertIn("= null", fixture)
        self.assertIn("= false", fixture)

    def test_documentation_distinguishes_missing_file_from_recovery_required(self):
        doc = DOC.read_text(encoding="utf-8")
        self.assertIn("reports Missing", doc)
        self.assertIn("RecoveryRequired(ACTIVE_RECORD_MISSING)", doc)
        self.assertIn("never Empty", doc)
        self.assertIn("process-kill, kernel crash, sudden power-loss", doc)


if __name__ == "__main__":
    unittest.main()
