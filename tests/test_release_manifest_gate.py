import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from scripts.release_manifest_gate import find_release_manifest, inspect_manifest

ROOT = Path(__file__).resolve().parents[1]

BASE = """<manifest xmlns:android="http://schemas.android.com/apk/res/android">
<uses-permission android:name="android.permission.USE_BIOMETRIC"/>
<application android:allowBackup="false" android:usesCleartextTraffic="false">
<activity android:name=".MainActivity" android:exported="true">
<intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter>
<intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.HOME"/><category android:name="android.intent.category.DEFAULT"/></intent-filter>
</activity>
<activity android:name=".OwnerAuthorityTrustActivity" android:exported="false"/>
</application>
</manifest>"""


def problems(xml):
    return inspect_manifest(ET.fromstring(xml))


class ReleaseManifestGateTests(unittest.TestCase):
    def test_baseline_release_manifest_passes(self):
        self.assertEqual(problems(BASE), [])

    def test_debug_credential_probe_leak_is_rejected(self):
        xml = BASE.replace(
            "</application>",
            '<activity android:name=".OwnerCredentialPromptProbeActivity" android:exported="true" android:permission="android.permission.DUMP"/></application>'
        )
        self.assertTrue(any("debug credential probe" in item for item in problems(xml)))

    def test_unreviewed_permission_is_rejected(self):
        xml = BASE.replace(
            "<application",
            '<uses-permission android:name="android.permission.CAMERA"/><application'
        )
        self.assertTrue(any("unreviewed release permission" in item for item in problems(xml)))

    def test_duplicate_permission_is_rejected(self):
        xml = BASE.replace(
            "<application",
            '<uses-permission android:name="android.permission.USE_BIOMETRIC"/><application'
        )
        self.assertTrue(any("duplicate release permission" in item for item in problems(xml)))

    def test_exported_non_home_component_is_rejected(self):
        xml = BASE.replace(
            "</application>",
            '<receiver android:name=".UnexpectedReceiver" android:exported="true"/></application>'
        )
        self.assertTrue(any("non-Home component" in item for item in problems(xml)))

    def test_missing_exported_attribute_is_rejected(self):
        xml = BASE.replace(
            'android:name=".OwnerAuthorityTrustActivity" android:exported="false"',
            'android:name=".OwnerAuthorityTrustActivity"'
        )
        self.assertTrue(any("non-Home component" in item for item in problems(xml)))

    def test_non_home_intent_filter_is_rejected(self):
        xml = BASE.replace(
            'android:name=".OwnerAuthorityTrustActivity" android:exported="false"/>',
            'android:name=".OwnerAuthorityTrustActivity" android:exported="false"><intent-filter><action android:name="x"/></intent-filter></activity>'
        )
        self.assertTrue(any("must not declare an intent-filter" in item for item in problems(xml)))

    def test_home_filter_is_required(self):
        xml = BASE.replace("android.intent.category.HOME", "android.intent.category.BROWSABLE")
        self.assertTrue(any("HOME/DEFAULT" in item for item in problems(xml)))

    def test_launcher_filter_is_required(self):
        xml = BASE.replace("android.intent.category.LAUNCHER", "android.intent.category.BROWSABLE")
        self.assertTrue(any("LAUNCHER" in item for item in problems(xml)))

    def test_backup_must_be_disabled(self):
        self.assertTrue(any("allowBackup" in item for item in problems(
            BASE.replace('android:allowBackup="false"', 'android:allowBackup="true"')
        )))

    def test_cleartext_must_be_disabled(self):
        self.assertTrue(any("usesCleartextTraffic" in item for item in problems(
            BASE.replace('android:usesCleartextTraffic="false"', 'android:usesCleartextTraffic="true"')
        )))

    def test_debuggable_and_test_only_are_rejected(self):
        for attribute in ("debuggable", "testOnly"):
            xml = BASE.replace(
                '<application ', f'<application android:{attribute}="true" '
            )
            self.assertTrue(any(attribute in item for item in problems(xml)))

    def test_shared_user_id_and_instrumentation_are_rejected(self):
        shared = BASE.replace("<manifest ", '<manifest android:sharedUserId="system" ')
        instrumented = BASE.replace("</manifest>", '<instrumentation android:name=".Test"/></manifest>')
        self.assertTrue(any("sharedUserId" in item for item in problems(shared)))
        self.assertTrue(any("instrumentation" in item for item in problems(instrumented)))

    def test_exactly_one_release_manifest_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nested = root / "merged_manifest" / "release" / "processReleaseMainManifest"
            nested.mkdir(parents=True)
            manifest = nested / "AndroidManifest.xml"
            manifest.write_text(BASE, encoding="utf-8")
            self.assertEqual(find_release_manifest(root), manifest)
            duplicate = root / "merged_manifest" / "release" / "other" / "processReleaseMainManifest"
            duplicate.mkdir(parents=True)
            (duplicate / "AndroidManifest.xml").write_text(BASE, encoding="utf-8")
            with self.assertRaises(ValueError):
                find_release_manifest(root)

    def test_missing_release_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                find_release_manifest(Path(temp))


class ReleaseManifestWorkflowTests(unittest.TestCase):
    def test_ci003_runs_gate_after_release_build_and_compares_reports(self):
        workflow = (ROOT / ".github/workflows/ci003-reproducibility.yml").read_text(encoding="utf-8")
        gate = workflow.index("release_manifest_gate.py")
        build = workflow.index(":app:testReleaseUnitTest :app:assembleRelease")
        verify = workflow.index("cmp runner-a/release-manifest-security.json runner-b/release-manifest-security.json")
        self.assertLess(build, gate)
        self.assertLess(gate, verify)
        self.assertIn("--manifest-root app/build/intermediates", workflow)
        self.assertIn("release-manifest-security.json", workflow)


if __name__ == "__main__":
    unittest.main()
