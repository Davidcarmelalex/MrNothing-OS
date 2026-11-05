#!/usr/bin/env python3
"""Fail-closed policy gate for the Gradle-merged Android release manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ANDROID = "{http://schemas.android.com/apk/res/android}"
MAIN = "android.intent.action.MAIN"
HOME = "android.intent.category.HOME"
DEFAULT = "android.intent.category.DEFAULT"
LAUNCHER = "android.intent.category.LAUNCHER"
ALLOWED_PERMISSIONS = frozenset({"android.permission.USE_BIOMETRIC"})
MAIN_ACTIVITY_NAMES = frozenset({".MainActivity", "tech.mrnothing.os.MainActivity"})
DEBUG_PROBE_SUFFIXES = frozenset({
    "OwnerCredentialPromptProbeActivity",
    "OwnerCredentialPromptProbeCancelReceiver",
})
COMPONENT_TYPES = ("activity", "activity-alias", "service", "receiver", "provider")
SCHEMA = "mrnothing-release-manifest-security-v1"


def inspect_manifest(root: ET.Element) -> list[str]:
    problems: list[str] = []
    if root.tag != "manifest":
        return ["root must be manifest"]
    if root.get(ANDROID + "sharedUserId") is not None:
        problems.append("sharedUserId is forbidden")

    applications = root.findall("application")
    if len(applications) != 1:
        return problems + ["exactly one application is required"]
    app = applications[0]
    if app.get(ANDROID + "allowBackup") != "false":
        problems.append("allowBackup must be false")
    if app.get(ANDROID + "usesCleartextTraffic") != "false":
        problems.append("usesCleartextTraffic must be false")
    for attribute in ("debuggable", "testOnly", "requestLegacyExternalStorage"):
        if app.get(ANDROID + attribute) == "true":
            problems.append(attribute + " must not be true")

    seen_permissions: set[str] = set()
    for tag in ("uses-permission", "uses-permission-sdk-23"):
        for node in root.findall(tag):
            name = node.get(ANDROID + "name")
            if not name:
                problems.append("permission missing android:name")
            elif name not in ALLOWED_PERMISSIONS:
                problems.append("unreviewed release permission: " + name)
            elif name in seen_permissions:
                problems.append("duplicate release permission: " + name)
            seen_permissions.add(name)

    if root.findall("instrumentation"):
        problems.append("instrumentation components are forbidden in release")

    found_home = False
    found_launcher = False
    main_count = 0
    for component_type in COMPONENT_TYPES:
        for component in app.findall(component_type):
            name = component.get(ANDROID + "name", "")
            exported = component.get(ANDROID + "exported")
            suffix = name.rsplit(".", 1)[-1]
            if suffix in DEBUG_PROBE_SUFFIXES:
                problems.append("debug credential probe leaked into release: " + name)

            is_main = component_type == "activity" and name in MAIN_ACTIVITY_NAMES
            if is_main:
                main_count += 1
                if exported != "true":
                    problems.append("MainActivity must be explicitly exported for HOME/LAUNCHER")
                for intent in component.findall("intent-filter"):
                    actions = {item.get(ANDROID + "name") for item in intent.findall("action")}
                    categories = {item.get(ANDROID + "name") for item in intent.findall("category")}
                    if MAIN in actions and {HOME, DEFAULT}.issubset(categories):
                        found_home = True
                    if MAIN in actions and LAUNCHER in categories:
                        found_launcher = True
            else:
                if exported != "false":
                    problems.append("non-Home component must explicitly be non-exported: " + name)
                if component.findall("intent-filter"):
                    problems.append("non-Home component must not declare an intent-filter: " + name)
            if not name:
                problems.append("component missing android:name")

    if main_count != 1:
        problems.append("exactly one MainActivity HOME/LAUNCHER component is required")
    if not found_home:
        problems.append("MAIN/HOME/DEFAULT intent filter required")
    if not found_launcher:
        problems.append("MAIN/LAUNCHER intent filter required")
    return problems


def find_release_manifest(root: Path) -> Path:
    if not root.is_dir():
        raise ValueError("merged-manifest root is missing or not a directory")
    candidates = sorted(
        path for path in root.rglob("AndroidManifest.xml")
        if path.is_file()
        and not path.is_symlink()
        and "release" in path.parts
        and any(part in {"merged_manifest", "merged_manifests"} for part in path.parts)
    )
    preferred = [path for path in candidates if "processReleaseMainManifest" in path.parts]
    if preferred:
        if len(preferred) != 1:
            raise ValueError(
                "expected exactly one processReleaseMainManifest output; found "
                + str(len(preferred))
            )
        return preferred[0]
    if len(candidates) != 1:
        raise ValueError(
            "expected exactly one release merged AndroidManifest.xml; found "
            + str(len(candidates))
        )
    return candidates[0]


def inspect_file(path: Path, relative_to: Path) -> dict:
    try:
        raw = path.read_bytes()
        root = ET.fromstring(raw)
    except (OSError, ET.ParseError) as exc:
        raise ValueError("release merged manifest unavailable or invalid") from exc
    problems = inspect_manifest(root)
    return {
        "schema": SCHEMA,
        "result": "PASS" if not problems else "FAIL",
        "manifest_path": path.relative_to(relative_to).as_posix(),
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "checks": {
            "backup_disabled": not any("allowBackup" in item for item in problems),
            "cleartext_disabled": not any("usesCleartextTraffic" in item for item in problems),
            "permissions_reviewed": not any("permission" in item for item in problems),
            "components_private": not any(
                "non-Home component" in item or "MainActivity must" in item or "component missing" in item
                for item in problems
            ),
            "debug_probe_absent": not any("debug credential probe" in item for item in problems),
            "home_and_launcher_present": not any(
                "HOME/DEFAULT" in item or "LAUNCHER intent" in item or "exactly one MainActivity" in item
                for item in problems
            ),
        },
        "problems": problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = find_release_manifest(args.manifest_root)
        report = inspect_file(manifest, args.manifest_root)
    except ValueError as exc:
        report = {"schema": SCHEMA, "result": "FAIL", "problems": [str(exc)]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    if report["result"] != "PASS":
        for problem in report.get("problems", []):
            print("RELEASE MANIFEST SECURITY ERROR: " + problem, file=sys.stderr)
        return 1
    print("Gradle-merged release manifest security gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
