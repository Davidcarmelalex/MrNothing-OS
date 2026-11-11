"""Synthetic JUnit regression coverage for the split emulator evidence gate."""
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from scripts.qa_stack011_instrumentation_evidence import (
    CREDENTIAL_CLASSES, EvidenceError, REQUIRED_METHODS, UNLOCKED_CLASSES, verify_reports,
)


class SplitInstrumentationEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.unlocked = self.root / "unlocked"
        self.credentialed = self.root / "credentialed"
        self.unlocked.mkdir()
        self.credentialed.mkdir()
        self.populate(self.unlocked, UNLOCKED_CLASSES, 37)
        self.populate(self.credentialed, CREDENTIAL_CLASSES, 2)

    def populate(self, root, classes, total):
        methods = {cls: list(sorted(REQUIRED_METHODS.get(cls, ()))) or ["testBaseline"] for cls in sorted(classes)}
        while sum(map(len, methods.values())) < total:
            methods[sorted(classes)[0]].append(f"testExtra{sum(map(len, methods.values()))}")
        for cls, names in methods.items():
            suite = ET.Element("testsuite", name=f"tech.mrnothing.os.{cls}",
                               tests=str(len(names)), failures="0", errors="0", skipped="0")
            for name in names:
                ET.SubElement(suite, "testcase", classname=f"tech.mrnothing.os.{cls}", name=name)
            ET.ElementTree(suite).write(root / f"TEST-{cls}.xml", encoding="utf-8")

    def test_accepts_all_39_split_cases(self):
        result = verify_reports(self.unlocked, self.credentialed)
        self.assertEqual(result["total_cases"], 39)
        self.assertEqual(len(result["uncredentialed"]["classes"]), 7)
        self.assertEqual(len(result["credentialed"]["classes"]), 1)

    def test_rejects_missing_uncredentialed_class(self):
        (self.unlocked / "TEST-AgentPlanPreviewActivityTest.xml").unlink()
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.credentialed)

    def test_rejects_missing_critical_regression_even_with_same_count(self):
        p = self.unlocked / "TEST-AgentPlanPreviewActivityTest.xml"
        tree = ET.parse(p)
        for case in tree.getroot().iter("testcase"):
            if case.get("name") == "testSwitchingPreviewModesInvalidatesAcknowledgedRehearsal":
                case.set("name", "testReplacedWithoutRegression")
        tree.write(p)
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.credentialed)

    def test_rejects_cross_suite_class_contamination(self):
        self.populate(self.credentialed, UNLOCKED_CLASSES, 37)
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.credentialed)

    def test_rejects_missing_credentialed_suite(self):
        for p in self.credentialed.iterdir():
            p.unlink()
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.credentialed)

    def test_rejects_failed_case(self):
        p = self.credentialed / "TEST-OwnerAuthorityTrustActivityCommitLifecycleTest.xml"
        tree = ET.parse(p)
        ET.SubElement(next(tree.getroot().iter("testcase")), "failure")
        tree.write(p)
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.credentialed)

    def test_rejects_skipped_aggregate_without_child(self):
        p = self.credentialed / "TEST-OwnerAuthorityTrustActivityCommitLifecycleTest.xml"
        tree = ET.parse(p)
        tree.getroot().set("skipped", "1")
        tree.write(p)
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.credentialed)

    def test_rejects_inconsistent_declared_count(self):
        p = self.credentialed / "TEST-OwnerAuthorityTrustActivityCommitLifecycleTest.xml"
        tree = ET.parse(p)
        tree.getroot().set("tests", "3")
        tree.write(p)
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.credentialed)

    def test_rejects_duplicate_testcase(self):
        p = self.credentialed / "TEST-OwnerAuthorityTrustActivityCommitLifecycleTest.xml"
        tree = ET.parse(p)
        tree.getroot().append(next(tree.getroot().iter("testcase")))
        tree.getroot().set("tests", "3")
        tree.write(p)
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.credentialed)

    def test_rejects_truncated_suite(self):
        p = self.credentialed / "TEST-OwnerAuthorityTrustActivityCommitLifecycleTest.xml"
        p.write_text("<testsuite", encoding="utf-8")
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.credentialed)

    def test_rejects_same_report_directory(self):
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.unlocked)

    def test_rejects_too_few_cases(self):
        p = self.unlocked / "TEST-AccessibilityDisclosureActivityTest.xml"
        tree = ET.parse(p)
        for case in list(tree.getroot())[-1:]:
            tree.getroot().remove(case)
        tree.getroot().set("tests", str(len(tree.getroot())))
        tree.write(p)
        with self.assertRaises(EvidenceError):
            verify_reports(self.unlocked, self.credentialed)


if __name__ == "__main__":
    unittest.main()
