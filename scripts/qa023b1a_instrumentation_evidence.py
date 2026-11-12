#!/usr/bin/env python3
"""Fail closed if the disabled MemoryVault installed-manifest tests did not execute.

This verifies Gradle connected AndroidTest JUnit XML, not just APK compilation or
a successful emulator workflow. It does not prove Pixel hardware behavior.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

EXPECTED_CLASS = "tech.mrnothing.os.MemoryVaultManifestBoundaryTest"
EXPECTED_METHODS = frozenset({
    "testInstalledVaultServiceIsDisabledAndPrivate",
    "testNoImplicitVaultIntentCanResolve",
})


class EvidenceError(ValueError):
    pass


def verify_reports(directory: Path) -> dict:
    if not directory.is_dir():
        raise EvidenceError(f"instrumentation XML directory missing: {directory}")
    reports = sorted(directory.rglob("TEST-*.xml"))
    if not reports:
        raise EvidenceError(f"no Gradle TEST-*.xml reports in {directory}")

    observed: list[str] = []
    all_cases = 0
    for report in reports:
        try:
            root = ET.parse(report).getroot()
        except (ET.ParseError, OSError) as exc:
            raise EvidenceError(f"unreadable JUnit XML {report}: {exc}") from exc
        if root.tag not in {"testsuite", "testsuites"}:
            raise EvidenceError(f"unexpected JUnit root {root.tag!r}: {report}")

        def walk(node: ET.Element, suite: str = "") -> None:
            nonlocal all_cases
            if node.tag in {"testsuite", "testsuites"}:
                # JUnit producers may report aggregate failures without child
                # <failure> nodes. Treat contradictory or malformed counters as
                # untrustworthy evidence rather than accepting a green summary.
                for key in ("tests", "failures", "errors", "skipped"):
                    raw = node.get(key)
                    if raw is None:
                        continue
                    if not raw.isascii() or not raw.isdecimal() or len(raw) > 9:
                        raise EvidenceError(
                            f"invalid JUnit {key} counter in {report}: {raw!r}"
                        )
                    value = int(raw)
                    if key == "tests":
                        actual = sum(1 for _ in node.iter("testcase"))
                        if value != actual:
                            raise EvidenceError(
                                f"JUnit tests counter mismatch in {report}: "
                                f"declared={value} actual={actual}"
                            )
                    elif value != 0:
                        raise EvidenceError(
                            f"JUnit reports {value} {key} in {report}"
                        )
            if node.tag == "testsuite":
                suite = node.get("name", suite)
            if node.tag in {"failure", "error", "skipped"}:
                raise EvidenceError(f"JUnit {node.tag} outside testcase in {report}")
            if node.tag == "testcase":
                all_cases += 1
                classname = node.get("classname") or suite
                method = node.get("name")
                if not method:
                    raise EvidenceError(f"testcase without name in {report}")
                if any(child.tag in {"failure", "error", "skipped"} for child in node):
                    raise EvidenceError(f"failed/skipped instrumentation case {classname}.{method}")
                if classname == EXPECTED_CLASS or classname == EXPECTED_CLASS.rsplit(".", 1)[-1]:
                    observed.append(method)
            for child in node:
                walk(child, suite)

        walk(root)

    if all_cases == 0:
        raise EvidenceError("JUnit XML contains no executed instrumentation testcases")
    if len(observed) != len(EXPECTED_METHODS) or set(observed) != EXPECTED_METHODS:
        raise EvidenceError(
            f"MemoryVault instrumentation cases mismatch: observed={sorted(observed)!r}; "
            f"expected={sorted(EXPECTED_METHODS)!r}"
        )
    return {
        "gate": "SEC-023B1A-QA",
        "result": "pass",
        "verified_class": EXPECTED_CLASS,
        "verified_methods": sorted(observed),
        "instrumentation_cases_in_reports": all_cases,
        "report_files": len(reports),
        "scope": "disposable Android emulator only; not physical Pixel acceptance",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    try:
        result = verify_reports(args.directory)
    except EvidenceError as exc:
        print(f"SEC-023B1A-QA FAIL: {exc}", file=sys.stderr)
        return 1
    if args.summary is not None:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
