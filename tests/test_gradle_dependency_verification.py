"""Static integrity gates for Gradle dependency verification metadata and CI use."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "android/gradle/verification-metadata.xml"
WORKFLOWS = [
    ROOT / ".github/workflows/phase1-checks.yml",
    ROOT / ".github/workflows/ci003-reproducibility.yml",
    ROOT / ".github/workflows/qa005-emulator.yml",
]
NEGATIVE_TEST = ROOT / "scripts/ci005_dependency_verification_negative.py"
NS = {"g": "https://schema.gradle.org/dependency-verification"}


class GradleDependencyVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(METADATA).getroot()
        cls.components = cls.root.findall("./g:components/g:component", NS)

    def test_metadata_is_strict_and_checksum_only(self):
        config = self.root.find("g:configuration", NS)
        self.assertIsNotNone(config)
        self.assertEqual(config.findtext("g:verify-metadata", namespaces=NS), "true")
        self.assertEqual(config.findtext("g:verify-signatures", namespaces=NS), "false")
        self.assertIsNone(self.root.find("g:components/g:ignored-dependencies", NS))
        self.assertIsNone(self.root.find("g:components/g:trusted-artifacts", NS))

    def test_every_component_artifact_has_a_sha256(self):
        self.assertGreaterEqual(len(self.components), 200)
        coordinates = set()
        artifact_count = 0
        for component in self.components:
            coordinate = (component.get("group"), component.get("name"), component.get("version"))
            self.assertNotIn(coordinate, coordinates)
            coordinates.add(coordinate)
            self.assertTrue(all(coordinate), f"invalid component coordinate: {coordinate}")
            self.assertNotRegex(component.get("version", ""), r"(?:\+|SNAPSHOT|latest\.)")
            artifacts = component.findall("g:artifact", NS)
            self.assertTrue(artifacts, f"component has no artifacts: {coordinate}")
            for artifact in artifacts:
                artifact_count += 1
                checksums = artifact.findall("g:sha256", NS)
                self.assertTrue(checksums, f"artifact has no SHA-256: {coordinate}/{artifact.get('name')}")
                for checksum in checksums:
                    self.assertRegex(checksum.get("value", ""), r"^[0-9a-f]{64}$")
        self.assertGreaterEqual(artifact_count, 400)

    def test_core_plugin_and_test_dependencies_are_pinned(self):
        coordinates = {
            (component.get("group"), component.get("name"), component.get("version"))
            for component in self.components
        }
        self.assertIn(("com.android.application", "com.android.application.gradle.plugin", "8.7.3"), coordinates)
        self.assertIn(("org.jetbrains.kotlin.android", "org.jetbrains.kotlin.android.gradle.plugin", "2.0.21"), coordinates)
        self.assertIn(("junit", "junit", "4.13.2"), coordinates)

    def test_all_android_workflows_enable_strict_dependency_verification(self):
        for path in WORKFLOWS:
            content = path.read_text(encoding="utf-8")
            invocations = [
                line for line in content.splitlines()
                if "gradle-8.9/bin/gradle" in line and "--no-daemon" in line
            ]
            self.assertTrue(invocations, f"{path} has no pinned Gradle invocation")
            for invocation in invocations:
                self.assertIn("--dependency-verification=strict", invocation, f"{path}: {invocation}")
            self.assertIn("ci005_dependency_verification_negative.py", content, f"{path} lacks negative control")

    def test_negative_control_has_positive_and_tampered_cases(self):
        content = NEGATIVE_TEST.read_text(encoding="utf-8")
        self.assertIn("verifyValidDependency", content)
        self.assertIn("verifyTamperedDependency", content)
        self.assertIn("--dependency-verification=strict", content)
        self.assertIn("--offline", content)
        self.assertIn("tampered-1.0.jar", content)
        self.assertIn("strict verification accepted a modified dependency artifact", content)

    def test_bootstrap_workflow_is_not_left_enabled(self):
        self.assertFalse((ROOT / ".github/workflows/ci005-bootstrap.yml").exists())


if __name__ == "__main__":
    unittest.main()
