"""SEC-023B1B2A: static fail-closed checks; not runtime Android/crypto proof."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os/MemoryVaultConsentCeremony.kt"
TEST = ROOT / "android/app/src/test/java/tech/mrnothing/os/MemoryVaultConsentCeremonyTest.kt"


class MemoryVaultConsentSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SRC.read_text(encoding="utf-8")
        cls.tests = TEST.read_text(encoding="utf-8")

    def test_nonce_helper_reuses_existing_local_csprng(self):
        self.assertIn("internal object MemoryVaultConsentNonce", self.source)
        self.assertIn("OwnerAttestationChallenge.create()", self.source)
        self.assertIn("check(bytes.size == 32)", self.source)

    def test_nonce_helper_zeroizes_temporary_byte_array(self):
        self.assertIn("finally {", self.source)
        self.assertIn("bytes.fill(0)", self.source)

    def test_nonce_generation_remains_separate_from_authorization(self):
        for name in ("localFreshNonceIsCanonical256BitHex",
                     "localFreshNoncesAreDistinctAcrossBoundedSample",
                     "freshNonceChangesConsentBindingWithoutGrantingAuthorization"):
            self.assertIn("fun " + name, self.tests)
        self.assertNotIn("MemoryVaultConsentNonce.freshHex()", self.source.split(
            "internal class MemoryVaultConsentCeremony", 1)[1])

    def test_dormant_no_android_side_effects(self):
        for forbidden in (
            "KeyStore.getInstance(", "KeyGenerator.getInstance(",
            "Cipher.getInstance(", "SharedPreferences", "openFileOutput(",
            "startActivity(", "onBind(", "Binder(", "ProcessBuilder(",
            "save_memory(", "Runtime.getRuntime("
        ):
            self.assertNotIn(forbidden, self.source)

    def test_only_awaits_real_cryptographic_proof(self):
        self.assertIn("AWAITING_CRYPTOOBJECT_PROOF", self.source)
        self.assertNotIn("AUTHORIZED", self.source)
        self.assertNotIn("ENABLED", self.source.split("internal enum class MemoryVaultConsentProgress")[1].split("}")[0])

    def test_reuses_existing_one_shot_state_and_serializes_calls(self):
        self.assertIn("OwnerAuthorityConfirmationState(clockNanos)", self.source)
        self.assertGreaterEqual(self.source.count("@Synchronized"), 3)
        self.assertIn("confirmation.finish(binding, platformCredentialReported)", self.source)

    def test_owner_identity_retention_nonce_and_consent_are_bound(self):
        for term in ("snapshot.ownerUserId != 0", "snapshot.retentionDays !in 1..90",
                     "sha256Hex.matches(snapshot.appSigningSha256)",
                     "sha256Hex.matches(snapshot.requestNonceHex)",
                     "!snapshot.explicitCheckboxChecked", "!snapshot.aliasAbsent",
                     "out.writeInt(encoded.size)", "MRNOTHING-MEMORY-OWNER-CONSENT-V1"):
            self.assertIn(term, self.source)

    def test_negative_jvm_regressions_are_present(self):
        for case in ("changedRetentionConsumesIntent", "changedSigningIdentityConsumesIntent",
                     "changedNonceConsumesIntent", "cancellationConsumesIntentAndCannotRestart",
                     "explicitRevocationConsumesIntent", "timeoutAndClockRollbackDenied",
                     "concurrentFinishAtMostOnePositive"):
            self.assertIn("fun " + case, self.tests)


if __name__ == "__main__":
    unittest.main()
