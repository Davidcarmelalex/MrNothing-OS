import tempfile
import unittest
from pathlib import Path

from scripts.apk_manifest_gate import compare_manifests

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PACKAGE = "tech.mrnothing.os"
BASE = """<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="tech.mrnothing.os">
<uses-permission android:name="android.permission.USE_BIOMETRIC"/>
<uses-sdk android:minSdkVersion="29" android:targetSdkVersion="35"/>
<application android:label="Mr. Nothing OS" android:theme="@android:style/Theme.Material.NoActionBar" android:allowBackup="false" android:usesCleartextTraffic="false">
<activity android:name=".MainActivity" android:exported="true">
<intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter>
<intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.HOME"/><category android:name="android.intent.category.DEFAULT"/></intent-filter>
</activity>
<activity android:name=".OwnerAuthorityTrustActivity" android:exported="false"/>
</application>
</manifest>"""


class PackagedApkManifestGateTests(unittest.TestCase):
    def write_pair(self, merged_xml=BASE, packaged_xml=BASE):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        merged_root = root / "intermediates"
        merged = merged_root / "merged_manifest" / "release" / "processReleaseMainManifest" / "AndroidManifest.xml"
        merged.parent.mkdir(parents=True)
        merged.write_text(merged_xml, encoding="utf-8")
        packaged = root / "release-packaged-manifest.xml"
        packaged.write_text(packaged_xml, encoding="utf-8")
        return root, merged_root, merged, packaged

    def run_gate(self, merged_xml=BASE, packaged_xml=BASE):
        root, merged_root, merged, packaged = self.write_pair(merged_xml, packaged_xml)
        return compare_manifests(
            merged, packaged, EXPECTED_PACKAGE, "test-cmdline-tools", merged_root
        )

    def test_identical_manifests_pass(self):
        report = self.run_gate()
        self.assertEqual(report["result"], "PASS")
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["mismatched_sections"], [])

    def test_relative_and_fully_qualified_component_names_are_equivalent(self):
        packaged = BASE.replace(
            'android:name=".MainActivity"',
            'android:name="tech.mrnothing.os.MainActivity"',
        ).replace(
            'android:name=".OwnerAuthorityTrustActivity"',
            'android:name="tech.mrnothing.os.OwnerAuthorityTrustActivity"',
        )
        self.assertEqual(self.run_gate(packaged_xml=packaged)["result"], "PASS")

    def test_presentation_only_changes_do_not_change_security_projection(self):
        packaged = BASE.replace('android:label="Mr. Nothing OS"', 'android:label="Different title"')
        packaged = packaged.replace(
            'android:theme="@android:style/Theme.Material.NoActionBar"',
            'android:theme="@android:style/Theme.DeviceDefault"',
        )
        self.assertEqual(self.run_gate(packaged_xml=packaged)["result"], "PASS")

    def test_unreviewed_packaged_permission_is_rejected(self):
        packaged = BASE.replace(
            "<application",
            '<uses-permission android:name="android.permission.CAMERA"/><application',
        )
        report = self.run_gate(packaged_xml=packaged)
        self.assertEqual(report["result"], "FAIL")
        self.assertFalse(report["checks"]["packaged_manifest_policy_pass"])
        self.assertIn("permissions", report["mismatched_sections"])

    def test_exported_non_home_component_in_packaged_apk_is_rejected(self):
        packaged = BASE.replace(
            "</application>",
            '<receiver android:name=".UnexpectedReceiver" android:exported="true"/></application>',
        )
        report = self.run_gate(packaged_xml=packaged)
        self.assertEqual(report["result"], "FAIL")
        self.assertIn("components", report["mismatched_sections"])

    def test_changed_intent_filter_is_rejected(self):
        packaged = BASE.replace(
            "android.intent.category.LAUNCHER",
            "android.intent.category.BROWSABLE",
        )
        report = self.run_gate(packaged_xml=packaged)
        self.assertEqual(report["result"], "FAIL")
        self.assertIn("components", report["mismatched_sections"])

    def test_cleartext_policy_change_is_rejected(self):
        packaged = BASE.replace(
            'android:usesCleartextTraffic="false"',
            'android:usesCleartextTraffic="true"',
        )
        report = self.run_gate(packaged_xml=packaged)
        self.assertEqual(report["result"], "FAIL")
        self.assertIn("application_attributes", report["mismatched_sections"])

    def test_packaged_application_id_mismatch_is_rejected(self):
        packaged = BASE.replace(
            'package="tech.mrnothing.os"',
            'package="tech.mrnothing.attacker"',
        )
        report = self.run_gate(packaged_xml=packaged)
        self.assertEqual(report["result"], "FAIL")
        self.assertFalse(report["checks"]["packaged_package_matches_expected"])

    def test_packaged_manifest_requires_package_identifier(self):
        packaged = BASE.replace(' package="tech.mrnothing.os"', "")
        report = self.run_gate(packaged_xml=packaged)
        self.assertEqual(report["result"], "FAIL")
        self.assertFalse(report["checks"]["packaged_package_matches_expected"])

    def test_merged_package_mismatch_is_rejected(self):
        merged = BASE.replace(
            'package="tech.mrnothing.os"',
            'package="tech.mrnothing.other"',
        )
        self.assertEqual(self.run_gate(merged_xml=merged)["result"], "FAIL")

    def test_invalid_packaged_xml_fails_closed(self):
        root, merged_root, merged, packaged = self.write_pair(packaged_xml="<manifest")
        with self.assertRaises(ValueError):
            compare_manifests(
                merged, packaged, EXPECTED_PACKAGE, "test-cmdline-tools", merged_root
            )

    def test_manifest_report_is_deterministic(self):
        first = self.run_gate()
        second = self.run_gate()
        self.assertEqual(first, second)


class PackagedApkManifestWorkflowTests(unittest.TestCase):
    def test_ci003_decodes_and_compares_packaged_manifest_after_release_build(self):
        workflow = (ROOT / ".github/workflows/ci003-reproducibility.yml").read_text(encoding="utf-8")
        build = workflow.index(":app:testReleaseUnitTest :app:assembleRelease")
        merged_gate = workflow.index("release_manifest_gate.py")
        decode = workflow.index("apkanalyzer manifest print")
        packaged_gate = workflow.index("apk_manifest_gate.py")
        verify = workflow.index(
            "cmp runner-a/release-packaged-manifest-security.json runner-b/release-packaged-manifest-security.json"
        )
        self.assertLess(build, merged_gate)
        self.assertLess(merged_gate, decode)
        self.assertLess(decode, packaged_gate)
        self.assertLess(packaged_gate, verify)
        self.assertIn("cmdline-tools/latest/bin/apkanalyzer", workflow)
        self.assertIn("--expected-package tech.mrnothing.os", workflow)
        self.assertIn("release-packaged-manifest-security.json", workflow)


if __name__ == "__main__":
    unittest.main()
