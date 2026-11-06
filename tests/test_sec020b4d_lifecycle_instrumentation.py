"""SEC-020B4D source gates for debug-only trust commit lifecycle instrumentation."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "android/app/src/main"
DEBUG = ROOT / "android/app/src/debug"
TEST = ROOT / "android/app/src/androidTest/java/tech/mrnothing/os/OwnerAuthorityTrustActivityCommitLifecycleTest.kt"
ANDROID = "{http://schemas.android.com/apk/res/android}"


class Sec020B4DLifecycleInstrumentationTests(unittest.TestCase):
    def test_fake_host_is_non_exported_debug_only(self):
        main_app = ET.parse(MAIN / "AndroidManifest.xml").getroot().find("application")
        debug_app = ET.parse(DEBUG / "AndroidManifest.xml").getroot().find("application")
        self.assertNotIn(
            ".OwnerAuthorityTrustActivityTestHost",
            [n.get(ANDROID + "name") for n in main_app.findall("activity")],
        )
        hosts = [n for n in debug_app.findall("activity")
                 if n.get(ANDROID + "name") == ".OwnerAuthorityTrustActivityTestHost"]
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0].get(ANDROID + "exported"), "false")
        self.assertIsNone(hosts[0].get(ANDROID + "permission"))

    def test_test_covers_both_sides_of_commit_claim(self):
        source = TEST.read_text(encoding="utf-8")
        activity = (MAIN / "java/tech/mrnothing/os/OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("testDestroyBeforeCommitClaimPreventsFakeStoreMutation", source)
        self.assertIn("testDestroyAfterCommitClaimAllowsAtomicFakeCommitButSuppressesUiDelivery", source)
        self.assertIn("operationGate.claimCommit(token)", activity)
        self.assertIn("gate.isDeliverable", source)
        self.assertIn("onActivityDestroyed", source)

    def test_fake_backend_is_memory_only_and_uses_synthetic_credential(self):
        source = TEST.read_text(encoding="utf-8")
        self.assertIn("BlockingFakeTrustStore", source)
        self.assertIn("KeyPairGenerator.getInstance(\"Ed25519\")", source)
        self.assertIn("locksettings set-pin", source)
        self.assertIn("locksettings clear --old", source)
        for forbidden in ("AndroidOwnerAuthorityTrustStore(", "AndroidAuthorityTrustCrypto(",
                          "AndroidAtomicAuthorityRecordPersistence(", "fastboot", "adb root",
                          "ProcessBuilder(", "Runtime.getRuntime(", "CommandRouter(",
                          "requestPermissions(", "store.commit(real"):
            self.assertNotIn(forbidden, source)

    def test_activity_default_factory_remains_android_backend(self):
        source = (MAIN / "java/tech/mrnothing/os/OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("internal open fun createTrustStore(context: Context)", source)
        self.assertIn("AndroidOwnerAuthorityTrustStore(context)", source)
        self.assertEqual(source.count("createTrustStore(appContext)"), 3)


if __name__ == "__main__":
    unittest.main()
