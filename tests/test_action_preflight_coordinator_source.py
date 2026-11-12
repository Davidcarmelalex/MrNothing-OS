"""AGENT-005N source-boundary checks for the non-executing preflight coordinator."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android/app/src/main/java/tech/mrnothing/os"
COORDINATOR = (SRC / "ActionPreflightCoordinator.kt").read_text(encoding="utf-8")


class ActionPreflightCoordinatorSourceTests(unittest.TestCase):
    def test_composes_existing_safety_and_action_specific_gates(self):
        self.assertIn("ScreenActionPreflight.evaluate(action, signals)", COORDINATOR)
        self.assertIn("permissionGate.evaluate(action, arguments)", COORDINATOR)
        self.assertLess(
            COORDINATOR.index("ScreenActionPreflight.evaluate(action, signals)"),
            COORDINATOR.index("permissionGate.evaluate(action, arguments)"),
        )

    def test_default_provider_is_explicitly_deny_all(self):
        self.assertIn("DenyAllScreenSafetySignalProvider", COORDINATOR)
        self.assertIn("private val safetySignals: ScreenSafetySignalProvider =", COORDINATOR)
        self.assertIn("trustedOwnerSession = false", COORDINATOR)
        self.assertIn("sessionRevoked = true", COORDINATOR)

    def test_malformed_arguments_are_rejected_before_state_reads(self):
        self.assertLess(
            COORDINATOR.index("canonicalJson(action, arguments)"),
            COORDINATOR.index("safetySignals.currentSignals()"),
        )

    def test_missing_or_throwing_safety_provider_fails_closed(self):
        self.assertIn("SAFETY_STATE_UNAVAILABLE", COORDINATOR)
        self.assertIn("catch (_: SecurityException)", COORDINATOR)
        self.assertIn("catch (_: RuntimeException)", COORDINATOR)
        self.assertIn("?: return ActionPreflightDecision.Blocked", COORDINATOR)

    def test_positive_result_is_not_authorization(self):
        self.assertIn("ReadyForIndependentAuthorization", COORDINATOR)
        self.assertIn("not owner consent, verified transport, authorization, or dispatch", COORDINATOR)

    def test_provider_contract_excludes_model_and_remote_input(self):
        self.assertIn("must not read model/LLM output, remote request fields", COORDINATOR)

    def test_coordinator_has_no_dispatch_or_platform_side_effect(self):
        for forbidden in (
            "CommandRouter(", "claim_dispatch(", "DISPATCH_STARTED",
            "startActivity(", "requestPermissions(", "createScreenCaptureIntent(",
            "getMediaProjection(", "performGlobalAction(", "dispatchGesture(",
            "ProcessBuilder(", "Runtime.getRuntime("
        ):
            self.assertNotIn(forbidden, COORDINATOR)


if __name__ == "__main__":
    unittest.main()
