"""Synthetic negative controls for the Gradle JVM MemoryVault evidence gate."""
from pathlib import Path
import tempfile
import unittest
from xml.sax.saxutils import escape

from scripts.qa023b1b2d3_unit_evidence import EvidenceError, REQUIRED, verify_reports


def case(cls, method, outcome=""):
    return (
        '<testcase classname="tech.mrnothing.os.' + escape(cls) +
        '" name="' + escape(method) + '">' + outcome + '</testcase>'
    )


def suite(cls, methods, *, attrs="", outcome=""):
    cases = "".join(case(cls, method) for method in methods)
    return f'<testsuite name="tech.mrnothing.os.{cls}" {attrs}>' + cases + outcome + "</testsuite>"


class UnitEvidenceGateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, text, name="TEST-memoryvault.xml"):
        (self.root / name).write_text(text, encoding="utf-8")

    def valid_xml(self):
        return "<testsuites>" + "".join(
            suite(cls, sorted(methods), attrs=f'tests="{len(methods)}" failures="0" errors="0" skipped="0"')
            for cls, methods in REQUIRED.items()
        ) + "</testsuites>"

    def test_accepts_complete_execution(self):
        self.write(self.valid_xml())
        result = verify_reports(self.root)
        self.assertEqual(result["required_methods_verified"], 15)
        self.assertEqual(result["all_jvm_cases"], 15)

    def test_accepts_unrelated_successful_tests(self):
        self.write(self.valid_xml()[:-13] + suite("OtherTest", ["works"]) + "</testsuites>")
        self.assertEqual(verify_reports(self.root)["all_jvm_cases"], 16)

    def test_rejects_missing_directory(self):
        with self.assertRaises(EvidenceError):
            verify_reports(self.root / "missing")

    def test_rejects_no_reports(self):
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_malformed_xml(self):
        self.write("<testsuite")
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_wrong_root(self):
        self.write("<other/>")
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_missing_required_method(self):
        cls = "MemoryVaultCompletionCancellationFenceTest"
        xml = self.valid_xml().replace(case(cls, "cannotFinishWithoutBeginning"), "")
        self.write(xml)
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_duplicate_required_method_across_reports(self):
        self.write(self.valid_xml())
        self.write(suite("MemoryVaultCipherProbePolicyTest", ["shortTagBlocks"]), "TEST-duplicate.xml")
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_failed_case(self):
        self.write(self.valid_xml().replace("</testsuites>", '<testsuite><testcase classname="x" name="fail"><failure/></testcase></testsuite></testsuites>'))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_skipped_case(self):
        self.write(self.valid_xml().replace("</testsuites>", '<testsuite><testcase classname="x" name="skip"><skipped/></testcase></testsuite></testsuites>'))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_aggregate_failure_counter(self):
        self.write(self.valid_xml().replace('failures="0"', 'failures="1"', 1))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_aggregate_skipped_counter(self):
        self.write(self.valid_xml().replace('skipped="0"', 'skipped="1"', 1))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_invalid_counter(self):
        self.write(self.valid_xml().replace('tests="8"', 'tests="NaN"', 1))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_inconsistent_test_count(self):
        self.write(self.valid_xml().replace('tests="8"', 'tests="9"', 1))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_suite_level_error(self):
        self.write(self.valid_xml().replace("</testsuites>", "<error/></testsuites>"))
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_missing_classname(self):
        self.write('<testsuite><testcase name="testOnly"/></testsuite>')
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_missing_method(self):
        self.write('<testsuite><testcase classname="x"/></testsuite>')
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)

    def test_rejects_empty_suite(self):
        self.write('<testsuite tests="0"/>')
        with self.assertRaises(EvidenceError):
            verify_reports(self.root)


if __name__ == "__main__":
    unittest.main()
