from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "android/app/src/main/java/tech/mrnothing/os/CommandRouter.kt"
POLICY = ROOT / "android/app/src/main/java/tech/mrnothing/os/AgentPolicy.kt"
MAIN_SOURCE = ROOT / "android/app/src/main/java"


class CommandRouterSourceTests(unittest.TestCase):
    def test_router_has_no_caller_supplied_authentication_boolean(self):
        source = ROUTER.read_text(encoding="utf-8")
        self.assertNotIn("authenticatedByTransport", source)
        self.assertNotRegex(source, r"\bBoolean\b")
        self.assertIn("UntrustedCommandRequest", source)
        self.assertIn("VERIFIED_TRANSPORT_SESSION_REQUIRED", source)

    def test_router_contains_no_device_action_dispatch(self):
        source = ROUTER.read_text(encoding="utf-8")
        for forbidden in (
            "DeviceDiagnostics.snapshot",
            "AppCatalog.launch",
            "ProcessBuilder",
            "Runtime.getRuntime",
            "OwnerConsentSigner",
            "startActivity",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_policy_classifies_risk_without_authentication_or_contact_boolean(self):
        source = POLICY.read_text(encoding="utf-8")
        self.assertIn("fun classify", source)
        self.assertNotRegex(source, r"authenticated\s*:\s*Boolean")
        self.assertNotIn("contactApproved", source)
        self.assertNotIn("authenticatedByTransport", source)

    def test_no_main_source_calls_router_before_typed_gate_is_integrated(self):
        call_sites = []
        for path in MAIN_SOURCE.rglob("*.kt"):
            if path == ROUTER:
                continue
            if "CommandRouter" in path.read_text(encoding="utf-8"):
                call_sites.append(str(path.relative_to(ROOT)))
        self.assertEqual([], call_sites)


if __name__ == "__main__":
    unittest.main()
