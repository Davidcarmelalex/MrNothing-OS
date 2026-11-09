"""Synthetic JUnit XML regression tests for the installed MemoryVault gate."""
from pathlib import Path
import tempfile
import unittest
from xml.sax.saxutils import escape

from scripts.qa023b1a_instrumentation_evidence import EvidenceError, verify_reports


CLASS = "tech.mrnothing.os.MemoryVaultManifestBoundaryTest"
A = "testInstalledVaultServiceIsDisabledAndPrivate"
B = "testNoImplicitVaultIntentCanResolve"


def suite(cases, *, name=CLASS):
    return '<testsuite name="' + escape(name) + '">' + "".join(cases) + "</testsuite>"


def case(name, *, classname=CLASS, outcome=""):
    return f'<testcase classname="{classname}" name="{name}">{outcome}</testcase>'


class MemoryVaultInstrumentationEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, data, filename="TEST-vault.xml"):
        (self.root / filename).write_text(data, encoding="utf-8")

    def test_accepts_both_expected_executed_cases(self):
        self.write(suite([case(A), case(B)]))
        result = verify_reports(self.root)
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["verified_methods"], sorted((A, B)))

    def test_rejects_missing_report_directory(self):
        with self.assertRaises(EvidenceError):
            verify_reports(self.root / "missing")

    def test_rejects_no_reports(self):
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_unrelated_tests_only(self):
        self.write(suite([case("testOther", classname="other.Class")]))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_one_missing_case(self):
        self.write(suite([case(A)]))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_duplicate_case_across_reports(self):
        self.write(suite([case(A), case(B)]))
        self.write(suite([case(A)]), "TEST-duplicate.xml")
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_failed_case(self):
        self.write(suite([case(A, outcome="<failure/>"), case(B)]))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_skipped_case(self):
        self.write(suite([case(A), case(B, outcome="<skipped/>")]))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_extra_target_case(self):
        self.write(suite([case(A), case(B), case("testUnexpected")]))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_malformed_xml(self):
        self.write("<testsuite><testcase")
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_empty_suite(self):
        self.write(suite([]))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_accepts_suite_class_fallback(self):
        self.write(suite([
            '<testcase name="' + A + '"/>',
            '<testcase name="' + B + '"/>',
        ]))
        self.assertEqual(verify_reports(self.root)["result"], "pass")


if __name__ == "__main__":
    unittest.main()
