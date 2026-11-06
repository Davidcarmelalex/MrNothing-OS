#!/usr/bin/env python3
"""Compare security-relevant Gradle and packaged APK manifest semantics."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    from .release_manifest_gate import find_release_manifest, inspect_manifest
except ImportError:  # Direct execution from android/ in CI.
    from release_manifest_gate import find_release_manifest, inspect_manifest

ANDROID = "{http://schemas.android.com/apk/res/android}"
SCHEMA = "mrnothing-packaged-apk-manifest-security-v1"
PRESENTATION_ATTRIBUTES = frozenset({
    "label", "icon", "roundIcon", "logo", "banner", "description", "theme",
})
ROOT_SECURITY_ATTRIBUTES = (
    "sharedUserId", "sharedUserLabel", "installLocation", "targetSandboxVersion",
    "coreApp", "isFeatureSplit", "configForSplit", "requiredSplitTypes",
    "splitTypes", "isSplitRequired",
)
SDK_SECURITY_ATTRIBUTES = ("minSdkVersion", "targetSdkVersion", "maxSdkVersion")
APPLICATION_SECURITY_ATTRIBUTES = (
    "allowBackup", "fullBackupContent", "dataExtractionRules",
    "usesCleartextTraffic", "networkSecurityConfig", "debuggable", "testOnly",
    "requestLegacyExternalStorage", "permission", "process", "persistent",
    "directBootAware", "enabled", "backupAgent", "restoreAnyVersion",
    "killAfterRestore", "manageSpaceActivity", "allowClearUserData",
    "extractNativeLibs", "forceQueryable",
)
COMPONENT_SECURITY_ATTRIBUTES = (
    "name", "exported", "permission", "enabled", "process", "authorities",
    "readPermission", "writePermission", "grantUriPermissions", "directBootAware",
    "isolatedProcess", "foregroundServiceType", "targetActivity",
    "parentActivityName", "taskAffinity", "launchMode", "documentLaunchMode",
    "allowTaskReparenting", "excludeFromRecents", "noHistory",
    "clearTaskOnLaunch", "finishOnTaskLaunch", "singleUser", "stopWithTask",
    "externalService", "visibleToInstantApps", "showForAllUsers",
    "requireDeviceUnlock", "lockTaskMode",
)
COMPONENT_TYPES = ("activity", "activity-alias", "service", "receiver", "provider")
CUSTOM_PERMISSION_TYPES = ("permission", "permission-group", "permission-tree")
ACCESS_RULE_TYPES = frozenset({"path-permission", "grant-uri-permission"})


def _selected_attributes(node: ET.Element, names: tuple[str, ...]) -> dict[str, str]:
    return {
        name: node.get(ANDROID + name)
        for name in names
        if node.get(ANDROID + name) is not None
    }


def _all_android_attributes(node: ET.Element) -> dict[str, str]:
    return {
        key[len(ANDROID):]: value
        for key, value in sorted(node.attrib.items())
        if key.startswith(ANDROID)
    }


def _normalize_class_name(name: str, package: str) -> str:
    if name.startswith("."):
        return package + name
    if "." not in name:
        return package + "." + name
    return name


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _generic_projection(node: ET.Element) -> dict:
    attributes = {
        key[len(ANDROID):]: value
        for key, value in sorted(node.attrib.items())
        if key.startswith(ANDROID)
        and key[len(ANDROID):] not in PRESENTATION_ATTRIBUTES
    }
    children = [_generic_projection(child) for child in list(node)]
    children.sort(key=_canonical)
    return {"tag": node.tag, "attributes": attributes, "children": children}


def _component_projection(node: ET.Element, package: str) -> dict:
    attributes = _selected_attributes(node, COMPONENT_SECURITY_ATTRIBUTES)
    for key in ("name", "targetActivity", "parentActivityName"):
        value = attributes.get(key)
        if value:
            attributes[key] = _normalize_class_name(value, package)

    filters = [_generic_projection(child) for child in node.findall("intent-filter")]
    filters.sort(key=_canonical)
    access_rules = [
        _generic_projection(child)
        for child in list(node)
        if child.tag in ACCESS_RULE_TYPES
    ]
    access_rules.sort(key=_canonical)
    return {
        "type": node.tag,
        "attributes": attributes,
        "intent_filters": filters,
        "access_rules": access_rules,
    }


def security_projection(root: ET.Element, expected_package: str) -> dict:
    """Return a deterministic projection of manifest properties affecting app access."""
    package = root.get("package") or expected_package
    applications = root.findall("application")
    app = applications[0] if len(applications) == 1 else None

    permissions = [
        {"tag": node.tag, "attributes": _all_android_attributes(node)}
        for node in list(root)
        if node.tag.startswith("uses-permission")
    ]
    permissions.sort(key=_canonical)

    custom_permissions = [
        {"tag": node.tag, "attributes": _all_android_attributes(node)}
        for tag in CUSTOM_PERMISSION_TYPES
        for node in root.findall(tag)
    ]
    custom_permissions.sort(key=_canonical)

    instrumentation = [_generic_projection(node) for node in root.findall("instrumentation")]
    instrumentation.sort(key=_canonical)

    sdk = [
        _selected_attributes(node, SDK_SECURITY_ATTRIBUTES)
        for node in root.findall("uses-sdk")
    ]
    sdk.sort(key=_canonical)

    components = []
    if app is not None:
        for tag in COMPONENT_TYPES:
            components.extend(_component_projection(node, package) for node in app.findall(tag))
    components.sort(key=_canonical)

    queries = [_generic_projection(node) for node in root.findall("queries")]
    queries.sort(key=_canonical)

    return {
        "package": package,
        "root_security_attributes": _selected_attributes(root, ROOT_SECURITY_ATTRIBUTES),
        "uses_sdk": sdk,
        "permissions": permissions,
        "custom_permissions": custom_permissions,
        "instrumentation": instrumentation,
        "queries": queries,
        "application_attributes": (
            _selected_attributes(app, APPLICATION_SECURITY_ATTRIBUTES) if app is not None else {}
        ),
        "components": components,
    }


def _load_manifest(path: Path, label: str) -> tuple[bytes, ET.Element]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(label + " manifest is missing, not a regular file, or a symlink")
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError(label + " manifest exceeds the 2 MiB safety limit")
    try:
        raw = path.read_bytes()
        root = ET.fromstring(raw)
    except (OSError, ET.ParseError) as exc:
        raise ValueError(label + " manifest is unavailable or invalid XML") from exc
    if root.tag != "manifest":
        raise ValueError(label + " manifest root must be manifest")
    return raw, root


def compare_manifests(
    merged_path: Path,
    packaged_path: Path,
    expected_package: str,
    decoder_revision: str,
    merged_root: Path,
) -> dict:
    if not expected_package or any(character.isspace() for character in expected_package):
        raise ValueError("expected application package must be a non-empty package identifier")

    merged_raw, merged_xml = _load_manifest(merged_path, "Gradle-merged")
    packaged_raw, packaged_xml = _load_manifest(packaged_path, "Packaged APK")

    problems: list[str] = []
    merged_package = merged_xml.get("package")
    packaged_package = packaged_xml.get("package")
    if merged_package and merged_package != expected_package:
        problems.append("Gradle-merged manifest package does not match expected applicationId")
    if not packaged_package:
        problems.append("packaged APK manifest has no package identifier")
    elif packaged_package != expected_package:
        problems.append("packaged APK manifest package does not match expected applicationId")

    merged_problems = inspect_manifest(merged_xml)
    packaged_problems = inspect_manifest(packaged_xml)
    problems.extend("merged manifest: " + item for item in merged_problems)
    problems.extend("packaged APK manifest: " + item for item in packaged_problems)

    merged_projection = security_projection(merged_xml, expected_package)
    packaged_projection = security_projection(packaged_xml, expected_package)
    mismatched_sections = sorted(
        key
        for key in merged_projection
        if merged_projection[key] != packaged_projection[key]
    )
    if mismatched_sections:
        problems.append(
            "packaged APK security projection differs from Gradle-merged manifest: "
            + ", ".join(mismatched_sections)
        )

    merged_policy = hashlib.sha256(_canonical(merged_projection).encode("utf-8")).hexdigest()
    packaged_policy = hashlib.sha256(_canonical(packaged_projection).encode("utf-8")).hexdigest()
    checks = {
        "merged_manifest_policy_pass": not merged_problems,
        "packaged_manifest_policy_pass": not packaged_problems,
        "packaged_package_matches_expected": packaged_package == expected_package,
        "security_projection_matches": not mismatched_sections,
    }
    return {
        "schema": SCHEMA,
        "result": "PASS" if not problems else "FAIL",
        "expected_package": expected_package,
        "decoder": {
            "tool": "apkanalyzer manifest print",
            "cmdline_tools_revision": decoder_revision,
        },
        "merged_manifest": {
            "path": merged_path.relative_to(merged_root).as_posix(),
            "sha256": hashlib.sha256(merged_raw).hexdigest(),
            "policy_sha256": merged_policy,
        },
        "packaged_manifest": {
            "path": packaged_path.name,
            "sha256": hashlib.sha256(packaged_raw).hexdigest(),
            "policy_sha256": packaged_policy,
        },
        "checks": checks,
        "mismatched_sections": mismatched_sections,
        "problems": problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merged-manifest-root", type=Path, required=True)
    parser.add_argument("--packaged-manifest", type=Path, required=True)
    parser.add_argument("--expected-package", required=True)
    parser.add_argument("--decoder-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        merged_path = find_release_manifest(args.merged_manifest_root)
        report = compare_manifests(
            merged_path,
            args.packaged_manifest,
            args.expected_package,
            args.decoder_revision,
            args.merged_manifest_root,
        )
    except (OSError, ValueError) as exc:
        report = {
            "schema": SCHEMA,
            "result": "FAIL",
            "decoder": {
                "tool": "apkanalyzer manifest print",
                "cmdline_tools_revision": args.decoder_revision,
            },
            "problems": [str(exc)],
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    if report["result"] != "PASS":
        for problem in report.get("problems", []):
            print("PACKAGED APK MANIFEST SECURITY ERROR: " + problem, file=sys.stderr)
        return 1
    print("Packaged APK manifest security gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
