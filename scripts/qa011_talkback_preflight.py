"""QA-011 read-only TalkBack readiness audit. Not spoken accessibility validation."""
import argparse
import json
from pathlib import Path

PACKAGE = "com.google.android.marvin.talkback"


def evaluate(packages: str, accessibility: str, services: str) -> dict:
    installed = f"package:{PACKAGE}" in {line.strip() for line in packages.splitlines()}
    flag = accessibility.strip()
    if flag not in {"0", "1"}:
        raise ValueError("Accessibility setting unavailable or malformed")
    entries = [entry.strip() for entry in services.strip().split(":") if entry.strip()]
    service = any(e.startswith(PACKAGE + "/") and len(e) > len(PACKAGE) + 1 for e in entries)
    enabled = flag == "1"
    status = ("blocked_package_missing" if not installed else
              "blocked_service_disabled" if not enabled or not service else
              "ready_for_manual_validation")
    return {"check": "QA-011 TalkBack preflight", "status": status,
            "package_present": installed, "accessibility_enabled": enabled,
            "talkback_service_enabled": service, "spoken_navigation_verified": False,
            "acceptance_passed": False,
            "note": "Read-only prerequisites only; spoken navigation and recovery require consented validation."}


def main():
    parser = argparse.ArgumentParser()
    for name in ("packages", "accessibility", "services", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    report = evaluate(args.packages.read_text(), args.accessibility.read_text(),
                      args.services.read_text())
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("QA-011 preflight: " + report["status"] + " (NOT TalkBack acceptance)")


if __name__ == "__main__":
    main()
