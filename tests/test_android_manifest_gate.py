import unittest
import xml.etree.ElementTree as ET

from scripts.android_manifest_gate import inspect_manifest, check_file

BASE = """<manifest xmlns:android="http://schemas.android.com/apk/res/android">
<application android:allowBackup="false" android:usesCleartextTraffic="false">
<activity android:name=".MainActivity" android:exported="true">
<intent-filter>
<action android:name="android.intent.action.MAIN"/>
<category android:name="android.intent.category.HOME"/>
<category android:name="android.intent.category.DEFAULT"/>
</intent-filter>
</activity>
</application>
</manifest>"""


def problems(xml: str):
    return inspect_manifest(ET.fromstring(xml))


class AndroidManifestGateTests(unittest.TestCase):
    def test_baseline_passes(self):
        self.assertEqual(problems(BASE), [])

    def test_real_manifest_passes(self):
        self.assertEqual(check_file("android/app/src/main/AndroidManifest.xml"), [])

    def test_backup_must_be_disabled(self):
        self.assertTrue(problems(BASE.replace('android:allowBackup="false"', 'android:allowBackup="true"')))

    def test_cleartext_must_be_disabled(self):
        self.assertTrue(problems(BASE.replace('android:usesCleartextTraffic="false"', 'android:usesCleartextTraffic="true"')))

    def test_new_permission_requires_review(self):
        self.assertTrue(problems(BASE.replace("<application", '<uses-permission android:name="android.permission.CAMERA"/><application')))

    def test_extra_exported_service_rejected(self):
        self.assertTrue(problems(BASE.replace("</application>", '<service android:name=".Backdoor" android:exported="true"/></application>')))

    def test_missing_home_role_rejected(self):
        self.assertTrue(problems(BASE.replace("android.intent.category.HOME", "android.intent.category.BROWSABLE")))

    def test_non_home_component_must_be_explicitly_private(self):
        self.assertTrue(problems(BASE.replace("</application>", '<service android:name=".Agent"/></application>')))

    def test_shared_user_id_rejected(self):
        self.assertTrue(problems(BASE.replace("<manifest ", '<manifest android:sharedUserId="system" ')))

    def test_invalid_manifest_file_fails_closed(self):
        self.assertTrue(check_file("/not/a/real/manifest.xml"))


if __name__ == "__main__":
    unittest.main()
