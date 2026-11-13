#!/usr/bin/env python3
"""Fail-closed Gradle JVM JUnit XML gate for dormant MemoryVault security tests.

This proves only that named JVM tests executed in the checked CI checkout.
It does not establish Android instrumentation, StrongBox, consent or Pixel proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

PACKAGE = "tech.mrnothing.os"
REQUIRED = {
    "MemoryVaultCompletionCancellationFenceTest": frozenset({
        "cannotFinishWithoutBeginning",
        "exactlyOneBeginAndFinish",
        "cancellationBeforeBeginIsTerminal",
        "cancellationDuringCryptoWorkBlocksCompletion",
        "repeatedCancellationCannotRearm",
        "aNewProcessCannotInheritPriorInFlightWork",
        "cancellationCanWinWhileCryptoWorkerIsBlocked",
        "finishFirstCannotBeRetroactivelyReclassified",
    }),
    "MemoryVaultGenerationCanaryVerifierTest": frozenset({
        "matchingKeyReferenceIsDiagnosticOnly",
        "replacedSamePolicyKeyIsRejected",
        "modifiedCiphertextIsRejected",
        "modifiedGenerationIdIsRejected",
        "modifiedConsentDigestIsRejected",
        "wrongNonceIsRejected",
        "missingReferenceIsRejected",
        "truncatedTagIsRejected",
        "arbitraryPlaintextIsRejected",
    }),
    "MemoryVaultCipherProbePolicyTest": frozenset({
        "positiveResultStillDoesNotAuthorizePersistence",
        "callbackMismatchBlocks",
        "missingKeyBlocks",
        "shortTagBlocks",
        "longTagBlocks",
        "emptyTagBlocks",
        "negativeTagLengthBlocks",
        "postOperationReadinessFailureBlocks",
    }),
}


class EvidenceError(ValueError):
    pass


def _counter(node: ET.Element, name: str, report: Path) -> int | None:
    raw = node.get(name)
    if raw is None:
        return None
    if len(raw) > 9 or not raw.isascii() or not raw.isdecimal():
        raise EvidenceError(f"invalid {name} counter in {report.name}: {raw!r}")
    return int(raw)


def verify_reports(directory: Path) -> dict:
    if not directory.is_dir():
        raise EvidenceError(f"JUnit report directory missing: {directory}")
    reports = sorted(directory.rglob("TEST-*.xml"))
    if not reports:
        raise EvidenceError("no Gradle TEST-*.xml reports")
    observed: dict[str, set[str]] = {name: set() for name in REQUIRED}
    all_cases = 0
    for report in reports:
        try:
            root = ET.parse(report).getroot()
        except (OSError, ET.ParseError) as exc:
            raise EvidenceError(f"unreadable JUnit XML {report.name}: {exc}") from exc
        if root.tag not in {"testsuite", "testsuites"}:
            raise EvidenceError(f"invalid JUnit root in {report.name}: {root.tag}")
        for suite in root.iter():
            if suite.tag not in {"testsuite", "testsuites"}:
                continue
            cases = list(suite.iter("testcase"))
            declared = _counter(suite, "tests", report)
            if declared is not None and declared != len(cases):
                raise EvidenceError(f"JUnit tests counter mismatch in {report.name}")
            for name in ("failures", "errors", "skipped"):
                count = _counter(suite, name, report)
                if count is not None and count != 0:
                    raise EvidenceError(f"JUnit {name}={count} in {report.name}")
        if any(node.tag in {"failure", "error", "skipped"} for node in root.iter()):
            raise EvidenceError(f"JUnit failure/error/skip element in {report.name}")
        for case in root.iter("testcase"):
            all_cases += 1
            classname = case.get("classname") or root.get("name", "")
            method = case.get("name")
            if not classname or not method:
                raise EvidenceError(f"testcase missing classname/name in {report.name}")
            short_class = classname.removeprefix(PACKAGE + ".")
            if short_class in REQUIRED:
                if classname not in {short_class, PACKAGE + "." + short_class}:
                    raise EvidenceError(f"ambiguous target class in {report.name}")
                if method in observed[short_class]:
                    raise EvidenceError(f"duplicate target test {short_class}.{method}")
                observed[short_class].add(method)
    if all_cases == 0:
        raise EvidenceError("no executed JUnit cases")
    for classname, required in REQUIRED.items():
        missing = required - observed[classname]
        if missing:
            raise EvidenceError(f"missing {classname} methods: {sorted(missing)}")
    return {
        "gate": "QA-023B1B2D3-JUNIT",
        "result": "pass",
        "report_files": len(reports),
        "all_jvm_cases": all_cases,
        "required_methods_verified": sum(len(methods) for methods in REQUIRED.values()),
        "verified": {name: sorted(methods) for name, methods in observed.items()},
        "scope": "Gradle JVM unit tests only; no Android emulator or Pixel hardware proof",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    try:
        result = verify_reports(args.directory)
    except EvidenceError as exc:
        print(f"QA-023B1B2D3-JUNIT BLOCKED: {exc}", file=sys.stderr)
        return 1
    if args.summary is not None:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
