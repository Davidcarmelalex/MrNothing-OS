"""SEC-023B1B2D9: source-only recovery preflight isolation and exact JUnit inventory."""
from pathlib import Path
import unittest
from scripts.qa023b1b2d3_unit_evidence import REQUIRED

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'android/app/src/main/java/tech/mrnothing/os'
SRC = APP / 'MemoryVaultOwnerRecoveryPreflight.kt'
TEST = ROOT / 'android/app/src/test/java/tech/mrnothing/os/MemoryVaultOwnerRecoveryPreflightTest.kt'

class OwnerRecoverySourceTests(unittest.TestCase):
    def test_dormant_no_runtime_wiring(self):
        callers = [p.name for p in APP.glob('*.kt') if p != SRC and
                   'MemoryVaultOwnerRecoveryPreflight' in p.read_text(encoding='utf-8')]
        self.assertEqual(callers, [])
        source = SRC.read_text(encoding='utf-8')
        for forbidden in ('import android.', 'KeyStore.getInstance', 'FileOutputStream',
                          'MemoryVaultService(', 'startActivity(', 'CommandRouter',
                          'Runtime.getRuntime', 'OWNER_RECOVERY_AUTHORIZED'):
            self.assertNotIn(forbidden, source)
        self.assertIn('OWNER_REVIEW_RECORDED_NOT_AUTHORIZED', source)
        self.assertIn('OwnerAuthorityConfirmationState(clockNanos)', source)

    def test_junit_inventory_complete(self):
        required = REQUIRED['MemoryVaultOwnerRecoveryPreflightTest']
        self.assertEqual(len(required), 25)
        source = TEST.read_text(encoding='utf-8')
        for method in required:
            self.assertIn('@Test fun '+method+'(', source)

    def test_documentation_disclaims_trust_provenance(self):
        doc = (ROOT/'docs/SEC-023B1B2D9-OWNER-RECOVERY-PREFLIGHT.md').read_text()
        for phrase in ('NOT AUTHORIZING', 'caller-supplied', 'rollback-resistant', 'physical Pixel'):
            self.assertIn(phrase, doc)

if __name__ == '__main__':
    unittest.main()
