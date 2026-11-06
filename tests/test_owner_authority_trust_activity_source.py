"""SEC-020B3/B4 source gates; not physical-device or StrongBox tests."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"
A = "{http://schemas.android.com/apk/res/android}"


class OwnerAuthorityTrustActivitySourceTests(unittest.TestCase):
    def test_activity_is_private_and_has_no_intent_filter(self):
        app = ET.parse(MANIFEST).getroot().find("application")
        matches = [item for item in app.findall("activity")
                   if item.get(A + "name") == ".OwnerAuthorityTrustActivity"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get(A + "exported"), "false")
        self.assertFalse(matches[0].findall("intent-filter"))

    def test_explicit_launcher_entry_exists(self):
        main = (SRC / "MainActivity.kt").read_text()
        self.assertIn('addAction(root, "Offline authority trust"', main)

    def test_device_credential_only_prompt_and_safety_recheck(self):
        code = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        factory = (SRC / "OwnerCredentialPromptFactory.kt").read_text()
        self.assertIn("OwnerCredentialPromptFactory.create(", code)
        self.assertIn("BiometricPrompt.Builder(activity)", factory)
        self.assertIn(".setAllowedAuthenticators(", factory)
        self.assertIn("BiometricManager.Authenticators.DEVICE_CREDENTIAL", factory)
        self.assertNotIn("BIOMETRIC_STRONG", code)
        self.assertNotIn("BIOMETRIC_WEAK", code)
        self.assertIn(
            "canAuthenticate(\n                BiometricManager.Authenticators.DEVICE_CREDENTIAL",
            code,
        )
        self.assertIn("OwnerCredentialAuthenticationPolicy.acceptsDeviceCredential", code)
        self.assertNotIn("createConfirmDeviceCredentialIntent", code)
        self.assertNotIn("startActivityForResult(", code)
        self.assertNotIn("onActivityResult(", code)
        self.assertGreaterEqual(code.count("OwnerCredentialSafetyGate.isSafe(this)"), 2)
        self.assertIn("OwnerCredentialSafetyGate.isSafe(appContext)", code)
        self.assertIn("confirmation.finish(expectedBinding, credentialResultAccepted)", code)

    def test_cancellation_invalidates_operation_before_signal_callback(self):
        code = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        cancel = code.index("private fun cancelPending(clearImport: Boolean)")
        clear_binding = code.index("pendingBinding = null", cancel)
        cancel_signal = code.index("activeCancellation?.cancel()", cancel)
        self.assertLess(clear_binding, cancel_signal)
        self.assertIn("operationGate.cancel(token)", code[cancel:])
        self.assertIn("operationGate.destroy()", code[code.index("override fun onDestroy()"):])

    def test_store_commit_follows_credential_and_state_revalidation(self):
        code = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        finish = code.index("confirmation.finish(expectedBinding, credentialResultAccepted)")
        inspect = code.index("trustStore.inspect()", finish)
        claim = code.index("operationGate.claimCommit(token)", inspect)
        commit = code.index("trustStore.commit(decision)", claim)
        self.assertLess(finish, inspect)
        self.assertLess(inspect, claim)
        self.assertLess(claim, commit)

    def test_store_io_is_serialized_off_main_thread(self):
        code = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        coordinator = (SRC / "OwnerAuthorityIoCoordinator.kt").read_text()
        self.assertIn("Executors.newSingleThreadExecutor", coordinator)
        self.assertEqual(code.count("createTrustStore(appContext)"), 3)
        self.assertIn("internal open fun createTrustStore(context: Context)", code)
        self.assertIn("AndroidOwnerAuthorityTrustStore(context)", code)
        self.assertNotIn("private val store by lazy", code)
        self.assertIn("executor.execute { task() }", coordinator)
        self.assertIn("OwnerAuthorityIoCoordinator.execute", code)
        self.assertNotIn("store.inspect()", code)
        self.assertNotIn("store.commit(", code)
        self.assertIn("operationGate.isActive(token)", code)
        self.assertIn("operationGate.claimCommit(token)", code)

    def test_out_of_band_fingerprint_attestation_is_required(self):
        code = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("independentFingerprintConfirmed.isChecked", code)
        self.assertIn("separate trusted channel", code)
        self.assertIn("FINGERPRINT_MISMATCH", (SRC / "AuthorityTrustImport.kt").read_text())

    def test_sensitive_ui_is_obscured_touch_and_screenshot_hardened(self):
        code = (SRC / "OwnerAuthorityTrustActivity.kt").read_text()
        self.assertIn("FLAG_SECURE", code)
        self.assertIn("filterTouchesWhenObscured = true", code)
        self.assertIn("OwnerConsentTouchGate.isUnobscured", code)

    def test_no_permissions_network_or_agent_execution(self):
        for name in ("OwnerAuthorityTrustActivity.kt", "AuthorityTrustImport.kt"):
            code = (SRC / name).read_text()
            for forbidden in (
                "requestPermissions(", "CommandRouter(", "startForegroundService(",
                "MediaProjectionManager", "AccessibilityService", "ProcessBuilder(",
                "Runtime.getRuntime(", "HttpURLConnection", "Socket("
            ):
                self.assertNotIn(forbidden, code)

    def test_manifest_has_no_new_permissions(self):
        root = ET.parse(MANIFEST).getroot()
        permissions = [node.get(A + "name") for node in root.findall("uses-permission")]
        self.assertEqual(permissions, ["android.permission.USE_BIOMETRIC"])


    def test_trust_path_has_no_sensitive_platform_or_execution_capabilities(self):
        names = (
            "OwnerAuthorityTrustActivity.kt",
            "AuthorityTrustImport.kt",
            "AndroidAuthorityTrustBackend.kt",
            "OwnerAuthorityTrustStore.kt",
            "OwnerAuthorityIoCoordinator.kt",
        )
        forbidden = (
            "CommandRouter", "TrustedCommand", "AgentPolicy", "AgentAction",
            "CommandExecutor", "AgentExecutor",
            "requestPermissions(", "grantRuntimePermission(",
            "startForegroundService(", "PackageInstaller",
            "MediaProjectionManager", "MediaProjection",
            "AccessibilityService", "AccessibilityNodeInfo",
            "NotificationListenerService", "VpnService", "DevicePolicyManager",
            "SmsManager", "TelephonyManager", "AudioRecord", "MediaRecorder",
            "CameraManager", "ProcessBuilder(", "Runtime.getRuntime(",
            "HttpURLConnection", "HttpsURLConnection", "ServerSocket(",
            "Socket(", "DatagramSocket(", "OkHttpClient", "WebSocket",
        )
        for name in names:
            code = (SRC / name).read_text()
            for marker in forbidden:
                with self.subTest(file=name, forbidden=marker):
                    self.assertNotIn(marker, code)

    def test_fake_trust_store_host_is_debug_only_and_non_exported(self):
        main_app = ET.parse(MANIFEST).getroot().find("application")
        debug_app = ET.parse(ROOT / "android/app/src/debug/AndroidManifest.xml").getroot().find("application")
        self.assertNotIn(
            ".OwnerAuthorityTrustActivityTestHost",
            [node.get(A + "name") for node in main_app.findall("activity")],
        )
        hosts = [node for node in debug_app.findall("activity")
                 if node.get(A + "name") == ".OwnerAuthorityTrustActivityTestHost"]
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0].get(A + "exported"), "false")
        self.assertIsNone(hosts[0].get(A + "permission"))

    def test_debug_credential_probe_is_dump_protected_and_debug_only(self):
        debug_manifest = ROOT / "android/app/src/debug/AndroidManifest.xml"
        main_root = ET.parse(MANIFEST).getroot()
        debug_root = ET.parse(debug_manifest).getroot()
        main_app = main_root.find("application")
        debug_app = debug_root.find("application")
        self.assertIsNotNone(main_app)
        self.assertIsNotNone(debug_app)

        probe_names = {
            ".OwnerCredentialPromptProbeActivity",
            ".OwnerCredentialPromptProbeCancelReceiver",
            ".OwnerAuthorityTrustActivityTestHost",
        }
        main_names = {
            node.get(A + "name")
            for tag in ("activity", "activity-alias", "service", "receiver", "provider")
            for node in main_app.findall(tag)
        }
        self.assertTrue(probe_names.isdisjoint(main_names))

        actual = []
        for tag in ("activity", "activity-alias", "service", "receiver", "provider"):
            for node in debug_app.findall(tag):
                name = node.get(A + "name")
                actual.append((tag, name))
                if name == ".OwnerAuthorityTrustActivityTestHost":
                    self.assertEqual(tag, "activity")
                    self.assertEqual(node.get(A + "exported"), "false")
                    self.assertIsNone(node.get(A + "permission"))
                    self.assertEqual(node.get(A + "excludeFromRecents"), "true")
                else:
                    self.assertEqual(node.get(A + "exported"), "true")
                    self.assertEqual(node.get(A + "permission"), "android.permission.DUMP")
        self.assertEqual(
            set(actual),
            {
                ("activity", ".OwnerCredentialPromptProbeActivity"),
                ("receiver", ".OwnerCredentialPromptProbeCancelReceiver"),
                ("activity", ".OwnerAuthorityTrustActivityTestHost"),
            },
        )


if __name__ == "__main__":
    unittest.main()
