#!/usr/bin/env python3
"""QA-STACK-011: fail-closed evidence gate for BOTH emulator instrumentation suites.

Consumes Gradle connectedDebugAndroidTest TEST-*.xml from the pre-PIN and
credentialed runs. It cannot establish physical Pixel, TalkBack, or security
approval. No emulator/device operations are performed by this parser.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

PACKAGE = "tech.mrnothing.os."
UNLOCKED_CLASSES = frozenset({
    "AccessibilityDisclosureActivityTest",
    "MemoryVaultManifestBoundaryTest",
    "AgentPlanPreviewActivityTest",
    "AndroidAtomicAuthorityRecordPersistenceTest",
    "AndroidAuthorityTrustCryptoFailureModeTest",
    "OwnerAuthorityTrustActivityLifecycleTest",
    "MemoryVaultKeySpecContractTest",
})
CREDENTIAL_CLASSES = frozenset({"OwnerAuthorityTrustActivityCommitLifecycleTest"})
REQUIRED_METHODS = {
    "AgentPlanPreviewActivityTest": frozenset({
        "testSampleReviewProgressionTerminalDenialAndCancellation",
        "testSwitchingPreviewModesInvalidatesAcknowledgedRehearsal",
        "testOnStopClearsActiveRehearsalWithoutGrant",
    }),
    "MemoryVaultManifestBoundaryTest": frozenset({
        "testInstalledVaultServiceIsDisabledAndPrivate",
        "testNoImplicitVaultIntentCanResolve",
    }),
    "OwnerAuthorityTrustActivityCommitLifecycleTest": frozenset({
        "testDestroyBeforeCommitClaimPreventsFakeStoreMutation",
        "testDestroyAfterCommitClaimAllowsAtomicFakeCommitButSuppressesUiDelivery",
    }),
}
MINIMUM_CASES = {"uncredentialed": 37, "credentialed": 2}


class EvidenceError(ValueError):
    pass


def _counter(node: ET.Element, key: str, report: Path) -> int | None:
    value = node.get(key)
    if value is None:
        return None
    if len(value) > 9 or not value.isascii() or not value.isdecimal():
        raise EvidenceError(f"invalid {key} counter in {report.name}")
    return int(value)


def _read_suite(directory: Path, allowed: frozenset[str], phase: str) -> dict:
    if not directory.is_dir() or directory.is_symlink():
        raise EvidenceError(f"{phase} report directory absent or unsafe")
    reports = sorted(directory.rglob("TEST-*.xml"))
    if not reports or len(reports) > 64:
        raise EvidenceError(f"{phase}: missing or excessive JUnit reports")
    cases: set[tuple[str, str]] = set()
    counts: Counter[str] = Counter()
    for report in reports:
        if report.is_symlink() or not report.is_file() or report.stat().st_size > 2_000_000:
            raise EvidenceError(f"{phase}: unsafe JUnit report {report.name}")
        try:
            root = ET.parse(report).getroot()
        except (ET.ParseError, OSError) as exc:
            raise EvidenceError(f"{phase}: unreadable JUnit report {report.name}") from exc
        if root.tag not in {"testsuite", "testsuites"}:
            raise EvidenceError(f"{phase}: unexpected JUnit root in {report.name}")
        for node in root.iter():
            if node.tag in {"failure", "error", "skipped"}:
                raise EvidenceError(f"{phase}: failed or skipped JUnit element in {report.name}")
            if node.tag in {"testsuite", "testsuites"}:
                actual = sum(1 for _ in node.iter("testcase"))
                declared = _counter(node, "tests", report)
                if declared is not None and declared != actual:
                    raise EvidenceError(f"{phase}: inconsistent JUnit test count in {report.name}")
                for key in ("failures", "errors", "skipped"):
                    value = _counter(node, key, report)
                    if value not in (None, 0):
                        raise EvidenceError(f"{phase}: nonzero JUnit {key} in {report.name}")
        parents = {child: parent for parent in root.iter() for child in parent}
        for case in root.iter("testcase"):
            raw_class = case.get("classname")
            if not raw_class:
                parent = parents.get(case)
                while parent is not None and parent.tag != "testsuite":
                    parent = parents.get(parent)
                raw_class = parent.get("name") if parent is not None else None
            if not raw_class or (("." in raw_class) and not raw_class.startswith(PACKAGE)):
                raise EvidenceError(f"{phase}: missing or unexpected testcase package")
            cls = raw_class.removeprefix(PACKAGE)
            method = case.get("name")
            if cls not in allowed or not method:
                raise EvidenceError(f"{phase}: unexpected class or missing method: {cls}")
            key = (cls, method)
            if key in cases:
                raise EvidenceError(f"{phase}: duplicate executed testcase: {cls}.{method}")
            cases.add(key)
            counts[cls] += 1
    if set(counts) != allowed:
        raise EvidenceError(f"{phase}: class inventory mismatch; missing={sorted(allowed - set(counts))}")
    if len(cases) < MINIMUM_CASES[phase]:
        raise EvidenceError(f"{phase}: only {len(cases)} cases, expected at least {MINIMUM_CASES[phase]}")
    for cls in allowed:
        required = REQUIRED_METHODS.get(cls, frozenset())
        observed = {method for classname, method in cases if classname == cls}
        if not required.issubset(observed):
            raise EvidenceError(f"{phase}: required regression absent from {cls}")
    return {"cases": len(cases), "classes": dict(sorted(counts.items())), "reports": len(reports)}


def verify_reports(uncredentialed: Path, credentialed: Path) -> dict:
    if uncredentialed.resolve() == credentialed.resolve():
        raise EvidenceError("credentialed and uncredentialed report roots must differ")
    first = _read_suite(uncredentialed, UNLOCKED_CLASSES, "uncredentialed")
    second = _read_suite(credentialed, CREDENTIAL_CLASSES, "credentialed")
    return {
        "gate": "QA-STACK-011",
        "result": "pass",
        "uncredentialed": first,
        "credentialed": second,
        "total_cases": first["cases"] + second["cases"],
        "scope": "disposable Android emulator; no physical Pixel, TalkBack, or human approval",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("uncredentialed", type=Path)
    parser.add_argument("credentialed", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    try:
        result = verify_reports(args.uncredentialed, args.credentialed)
    except EvidenceError as exc:
        print(f"QA-STACK-011 FAIL: {exc}", file=sys.stderr)
        return 1
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
