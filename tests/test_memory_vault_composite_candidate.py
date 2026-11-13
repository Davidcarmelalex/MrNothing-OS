"""SEC-023B1B2B-C: structural integration gates for a dormant composite candidate.

These tests are source-level invariants, not cryptographic, emulator, or Pixel proof.
"""
import pathlib
import unittest
from xml.etree import ElementTree as ET

from test_memory_vault_integration_audit import module as audit_module

ROOT = pathlib.Path(__file__).resolve().parents[1]
NS = "{http://schemas.android.com/apk/res/android}"


class MemoryVaultCompositeCandidateTests(unittest.TestCase):
    def test_all_seven_components_require_review_not_approval(self):
        result = audit_module.audit(ROOT)
        self.assertEqual("REVIEW_REQUIRED", result["status"], result)
        self.assertEqual([], result["findings"])
        self.assertEqual([], result["missing_components"])
        self.assertEqual("PENDING", result["independent_security_review"])
        self.assertEqual("NOT_EVALUATED", result["runtime_crypto_proof"])

    def test_no_new_permission_or_enabled_vault(self):
        manifest = ET.parse(ROOT / audit_module.MANIFEST).getroot()
        permissions = {node.get(NS + "name") for node in manifest.findall("uses-permission")}
        self.assertEqual({"android.permission.USE_BIOMETRIC"}, permissions)
        application = manifest.find("application")
        self.assertIsNotNone(application)
        services = [node for node in application.findall("service")
                    if node.get(NS + "name") == ".MemoryVaultService"]
        self.assertEqual(1, len(services))
        self.assertEqual("false", services[0].get(NS + "enabled"))
        self.assertEqual("false", services[0].get(NS + "exported"))

    def test_launcher_and_paperclip_have_no_vault_wiring(self):
        for path in (
            "android/app/src/main/java/tech/mrnothing/os/MainActivity.kt",
            "agents/paperclip/agent.py",
        ):
            source = (ROOT / path).read_text(encoding="utf-8")
            self.assertNotIn("MemoryVaultService", source)
            self.assertNotIn("MemoryVaultConsentCeremony", source)
            self.assertNotIn("MemoryVaultKeystorePreflight", source)


if __name__ == "__main__":
    unittest.main()
