"""Structural completeness checks for the M1 security threat model.

These checks guard the presence of required review sections and evidence caveats.
They do not constitute a security review or prove that mitigations are effective.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "docs" / "THREAT-MODEL.md"


class ThreatModelDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = MODEL.read_text(encoding="utf-8")

    def test_required_sections_are_present(self):
        for heading in (
            "## 1. Purpose, scope and system reality",
            "## 2. Security objectives",
            "## 3. Assets and security properties",
            "## 4. System components and trust boundaries",
            "## 5. Threat actors and assumptions",
            "## 6. Security invariants",
            "## 7. STRIDE threat register",
            "## 8. Data handling and retention requirements",
            "## 9. Verified implementation and test evidence",
            "## 10. Residual risks and required owners",
            "## 11. Milestone gates",
            "## 12. M1 acceptance criteria and review checklist",
            "## 13. Change triggers",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, self.text)

    def test_all_stride_categories_are_explicit(self):
        for category in (
            "Spoofing", "Tampering", "Repudiation",
            "Information disclosure", "Denial of service",
            "Elevation of privilege",
        ):
            with self.subTest(category=category):
                self.assertIn(category, self.text)

    def test_threat_register_has_unique_ids(self):
        for threat_id in (f"TM-{i:02d}" for i in range(1, 17)):
            with self.subTest(threat_id=threat_id):
                self.assertEqual(self.text.count(threat_id), 1)

    def test_all_eight_milestones_have_explicit_status(self):
        for milestone in (f"M{i}" for i in range(1, 9)):
            with self.subTest(milestone=milestone):
                self.assertIn(milestone, self.text)
        self.assertIn("No milestone is COMPLETE.", self.text)

    def test_unverified_accessibility_and_release_claims_stay_explicit(self):
        self.assertIn("spoken_navigation_verified=false", self.text)
        self.assertIn("acceptance_passed=false", self.text)
        self.assertIn("release_ready=false", self.text)
        self.assertIn("no physical-device validation is claimed", self.text)

    def test_legacy_shell_and_executor_boundaries_are_documented(self):
        self.assertIn("subprocess shell execution", self.text)
        self.assertIn("production autonomous executor", self.text)
        self.assertIn("rejects every request", self.text)

    def test_paperclip_model_download_risk_is_documented(self):
        self.assertIn("TM-15", self.text)
        self.assertIn("model-hub fallback", self.text)
        self.assertIn("local GGUF", self.text)

    def test_network_diagnostics_boundary_is_documented(self):
        self.assertIn("MRNOTHING_NETWORK_ALLOWED_TARGETS", self.text)
        self.assertIn("api.ipify.org", self.text)
        self.assertIn("provider-selected speed tests", self.text)
        self.assertIn("process-local", self.text)

    def test_independent_review_is_required(self):
        self.assertIn("The document author cannot self-approve.", self.text)
        self.assertIn("remains DRAFT", self.text)


if __name__ == "__main__":
    unittest.main()
