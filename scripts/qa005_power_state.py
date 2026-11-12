#!/usr/bin/env python3
"""Fail-closed parser for the Android 15 QA-005 emulator wake precondition."""
from __future__ import annotations

import argparse
import re
import sys


def _single_line_value(snapshot: str, field: str) -> str | None:
    values = re.findall(rf"(?m)^\s*{re.escape(field)}=([^\s]+)\s*$", snapshot)
    return values[0] if len(values) == 1 else None


def inspect_power_state(
    snapshot: str, minimum_wake_age_ms: int = 1500
) -> tuple[bool, int | None, str]:
    """Return (settled, wake_age_ms, reason); malformed/ambiguous state fails closed."""
    if minimum_wake_age_ms < 0:
        return False, None, "minimum wake age must not be negative"

    expected = (
        ("mWakefulness", "Awake"),
        ("mWakefulnessChanging", "false"),
        ("mHalInteractiveModeEnabled", "true"),
    )
    for field, wanted in expected:
        actual = _single_line_value(snapshot, field)
        if actual is None:
            return False, None, f"{field} is missing or ambiguous"
        if actual != wanted:
            return False, None, f"{field}={actual}; expected {wanted}"

    ages = re.findall(
        r"(?m)^\s*mLastWakeTime=\d+\s+\((\d+) ms ago\)\s*$", snapshot
    )
    if len(ages) != 1:
        return False, None, "mLastWakeTime age is missing, malformed or ambiguous"

    age_ms = int(ages[0])
    if age_ms < minimum_wake_age_ms:
        return (
            False,
            age_ms,
            f"last wake age {age_ms} ms is below {minimum_wake_age_ms} ms",
        )
    return True, age_ms, "PowerManager wake state is settled"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-wake-age-ms", type=int, default=1500)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    snapshot = sys.stdin.read()
    settled, age_ms, reason = inspect_power_state(
        snapshot, minimum_wake_age_ms=args.min_wake_age_ms
    )
    if not settled:
        print(reason, file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"{reason}; last wake age={age_ms} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
