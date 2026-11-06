import json
import tempfile
import unittest
from pathlib import Path

from scripts.apk_manifest_gate import compare_manifests

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PACKAGE = "tech.mrnothing.os"
VARIANT_METADATA = {
    "schema": "mrnothing-gradle-release-variant-v1",
    "applicationId": EXPECTED_PACKAGE,
    "variantName": "release",
    "buildType": "release",
}
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
        metadata = root / "release-variant-metadata.json"
        metadata.write_text(json.dumps(VARIANT_METADATA, sort_keys=True) + "\n", encoding="utf-8")
        return root, merged_root, merged, packaged, metadata

    def run_gate(self, merged_xml=BASE, packaged_xml=BASE, variant_metadata=None):
        root, merged_root, merged, packaged, metadata = self.write_pair(merged_xml, packaged_xml)
        if variant_metadata is not None:
            metadata.write_text(json.dumps(variant_metadata, sort_keys=True) + "\n", encoding="utf-8")
        return compare_manifests(
            merged, packaged, metadata, "test-cmdline-tools", merged_root
        )

    def test_identical_manifests_pass(self):
        report = self.run_gate()
        self.assertEqual(report["result"], "PASS")
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["mismatched_sections"], [])
        self.assertEqual(report["gradle_release_variant"]["application_id"], EXPECTED_PACKAGE)
        self.assertEqual(report["gradle_release_variant"]["variant_name"], "release")

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
        root, merged_root, merged, packaged, metadata = self.write_pair(packaged_xml="<manifest")
        with self.assertRaises(ValueError):
            compare_manifests(
                merged, packaged, metadata, "test-cmdline-tools", merged_root
            )

    def test_application_id_is_derived_from_gradle_metadata(self):
        variant = dict(VARIANT_METADATA, applicationId="tech.mrnothing.attacker")
        report = self.run_gate(variant_metadata=variant)
        self.assertEqual(report["expected_package"], "tech.mrnothing.attacker")
        self.assertEqual(report["result"], "FAIL")
        self.assertFalse(report["checks"]["merged_package_matches_gradle_variant"])
        self.assertFalse(report["checks"]["packaged_package_matches_gradle_variant"])

    def test_non_release_variant_metadata_is_rejected(self):
        variant = dict(VARIANT_METADATA, variantName="debug", buildType="debug")
        with self.assertRaisesRegex(ValueError, "variant name must be release"):
            self.run_gate(variant_metadata=variant)

    def test_invalid_application_id_metadata_is_rejected(self):
        variant = dict(VARIANT_METADATA, applicationId="tech..attacker")
        with self.assertRaisesRegex(ValueError, "applicationId is invalid"):
            self.run_gate(variant_metadata=variant)

    def test_duplicate_variant_metadata_json_key_is_rejected(self):
        root, merged_root, merged, packaged, metadata = self.write_pair()
        metadata.write_text(
            '{"schema":"mrnothing-gradle-release-variant-v1","applicationId":"tech.mrnothing.os",'
            '"applicationId":"tech.mrnothing.attacker","variantName":"release","buildType":"release"}\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            compare_manifests(merged, packaged, metadata, "test-cmdline-tools", merged_root)

    def test_manifest_report_is_deterministic(self):
        first = self.run_gate()
        second = self.run_gate()
        self.assertEqual(first, second)


class PackagedApkManifestWorkflowTests(unittest.TestCase):
    def test_ci003_decodes_and_compares_packaged_manifest_after_release_build(self):
        workflow = (ROOT / ".github/workflows/ci003-reproducibility.yml").read_text(encoding="utf-8")
        build = workflow.index(":app:testReleaseUnitTest :app:assembleRelease :app:writeReleaseRuntimeInventory :app:writeReleaseVariantMetadata")
        merged_gate = workflow.index("release_manifest_gate.py")
        decode = workflow.index('"$APKANALYZER" manifest print "$APK"')
        packaged_gate = workflow.index("apk_manifest_gate.py")
        verify = workflow.index(
            "cmp runner-a/release-packaged-manifest-security.json runner-b/release-packaged-manifest-security.json"
        )
        self.assertLess(build, merged_gate)
        self.assertLess(merged_gate, decode)
        self.assertLess(decode, packaged_gate)
        self.assertLess(packaged_gate, verify)
        self.assertIn("cmdline-tools/latest/bin/apkanalyzer", workflow)
        self.assertIn('"$APKANALYZER" manifest print "$APK"', workflow)
        self.assertIn("--variant-metadata \"$VARIANT_METADATA\"", workflow)
        self.assertNotIn("--expected-package tech.mrnothing.os", workflow)
        self.assertIn("--release-variant-metadata \"$VARIANT_METADATA\"", workflow)
        provenance_step = workflow[workflow.index("Generate deterministic SPDX runtime SBOM and build provenance"):]
        self.assertIn('VARIANT_METADATA="app/build/reports/ci003/release-variant-metadata.json"', provenance_step)
        self.assertIn("release-variant-metadata.json", workflow)
        self.assertIn("cmp runner-a/release-variant-metadata.json runner-b/release-variant-metadata.json", workflow)
        self.assertIn("release-packaged-manifest-security.json", workflow)

    def test_gradle_variant_identity_is_derived_from_release_variant_api(self):
        gradle = (ROOT / "android/app/build.gradle.kts").read_text(encoding="utf-8")
        self.assertIn("androidComponents", gradle)
        self.assertIn("variant.applicationId", gradle)
        self.assertIn("writeReleaseVariantMetadata", gradle)
        self.assertIn("exactly one release variant", gradle)


if __name__ == "__main__":
    unittest.main()
