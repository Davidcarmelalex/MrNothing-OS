"""SEC-023B1B2B: synthetic source-audit regressions, not Android tests."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/memory_vault_integration_audit.py"
spec = importlib.util.spec_from_file_location("memory_vault_integration_audit", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IntegrationAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, relative in module.COMPONENTS.items():
            p = self.root / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            content = "placeholder"
            if name in module.ALIAS_SOURCES:
                content = f'const val KEY_ALIAS = "{module.KEY_ALIAS}"\n'
            if name == "service":
                content = "onBind(intent: Intent?): IBinder? = null\nstopSelfResult(startId)\nSTART_NOT_STICKY\n"
            if name == "consent":
                content += "\nAWAITING_CRYPTOOBJECT_PROOF\n"
            p.write_text(content, encoding="utf-8")
        self.manifest = self.root / module.MANIFEST
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.set_manifest('<service android:name=".MemoryVaultService" '
                          'android:exported="false" android:enabled="false"/>')

    def set_manifest(self, services):
        self.manifest.write_text(
            '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
            f'<application>{services}</application></manifest>', encoding="utf-8")

    def test_complete_synthetic_tree_only_requires_review(self):
        result = module.audit(self.root)
        self.assertEqual("REVIEW_REQUIRED", result["status"])
        self.assertEqual([], result["findings"])
        self.assertEqual("PENDING", result["independent_security_review"])
        self.assertEqual(3, module.main(["--root", str(self.root)]))

    def test_missing_components_fail_closed(self):
        (self.root / module.COMPONENTS["provisioning"]).unlink()
        result = module.audit(self.root)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("provisioning", result["missing_components"])
        self.assertEqual(2, module.main(["--root", str(self.root)]))

    def test_exported_service_rejected(self):
        self.set_manifest('<service android:name=".MemoryVaultService" '
                          'android:exported="true" android:enabled="false"/>')
        self.assertIn("memory_vault_service_exported", module.audit(self.root)["findings"])

    def test_enabled_service_rejected(self):
        self.set_manifest('<service android:name=".MemoryVaultService" '
                          'android:exported="false" android:enabled="true"/>')
        self.assertIn("memory_vault_service_not_disabled", module.audit(self.root)["findings"])

    def test_service_implicit_intent_rejected(self):
        self.set_manifest('<service android:name=".MemoryVaultService" '
                          'android:exported="false" android:enabled="false">'
                          '<intent-filter/></service>')
        self.assertIn("memory_vault_service_has_intent_filter", module.audit(self.root)["findings"])

    def test_duplicate_service_rejected(self):
        s = '<service android:name=".MemoryVaultService" android:exported="false" android:enabled="false"/>'
        self.set_manifest(s + s)
        self.assertIn("memory_vault_service_count_not_one", module.audit(self.root)["findings"])

    def test_missing_or_malformed_manifest_rejected(self):
        self.manifest.write_text("<broken", encoding="utf-8")
        self.assertIn("invalid_manifest_xml", module.audit(self.root)["findings"])
        self.manifest.unlink()
        self.assertIn("missing_manifest", module.audit(self.root)["findings"])

    def test_alias_drift_rejected_in_each_source(self):
        for name in module.ALIAS_SOURCES:
            path = self.root / module.COMPONENTS[name]
            original = path.read_text(encoding="utf-8")
            path.write_text(original.replace(module.KEY_ALIAS, "wrong_alias"), encoding="utf-8")
            self.assertIn(f"key_alias_mismatch:{name}", module.audit(self.root)["findings"])
            path.write_text(original, encoding="utf-8")

    def test_service_start_and_bind_contract_rejected_when_missing(self):
        p = self.root / module.COMPONENTS["service"]
        p.write_text("onBind(intent: Intent?): IBinder? = null\n", encoding="utf-8")
        self.assertIn("service_dormant_source_contract_missing", module.audit(self.root)["findings"])

    def test_consent_side_effect_api_rejected(self):
        p = self.root / module.COMPONENTS["consent"]
        p.write_text(p.read_text(encoding="utf-8") + "\nCipher.getInstance(\n", encoding="utf-8")
        self.assertIn("consent_unexpected_side_effect_api", module.audit(self.root)["findings"])

    def test_no_crypto_proof_boundary_rejected(self):
        p = self.root / module.COMPONENTS["consent"]
        p.write_text(p.read_text(encoding="utf-8").replace("AWAITING_CRYPTOOBJECT_PROOF", "GRANTED"), encoding="utf-8")
        self.assertIn("consent_proof_boundary_missing", module.audit(self.root)["findings"])


if __name__ == "__main__":
    unittest.main()
