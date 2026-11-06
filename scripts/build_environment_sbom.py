#!/usr/bin/env python3
"""Capture and verify the scoped CI-003 build-environment SPDX inventory."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import shlex
import tempfile
from urllib.parse import quote

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ACTION_RE = re.compile(r"^\s*-\s*uses:\s*([^\s#]+)", re.MULTILINE)
PLUGIN_RE = re.compile(r'id\("([^"]+)"\)\s+version\s+"([^"]+)"')
SDK_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+(?:;[A-Za-z0-9_.-]+)*$")
TOOL_NAME = "MrNothing CI-006 Build Environment SBOM Generator"
SCOPE = (
    "Inventories installed Debian/Ubuntu packages, installed Python packages, installed Android SDK packages, "
    "the verified Gradle distribution, direct Android/Kotlin Gradle plugin declarations, JDK/Python runtimes, "
    "and immutable GitHub Actions referenced by the CI-003 workflow. It does not enumerate every transitive "
    "Gradle plugin-resolution dependency, every GitHub runner toolcache file, or the complete hosted-runner image; "
    "therefore it is a scoped build-environment SBOM, not a claim of a complete host-image SBOM."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_regular(path: Path, limit: int = 64 * 1024 * 1024) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"input is missing, not a regular file, or is a symlink: {path}")
    if path.stat().st_size > limit:
        raise ValueError(f"input exceeds size limit: {path}")
    return path.read_text(encoding="utf-8")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict:
    try:
        value = json.loads(read_regular(path), object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _purl_segment(value: str) -> str:
    return quote(value, safe=".-_~")


def parse_os_release(text: str) -> dict:
    values = {}
    for line in text.splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key):
            continue
        try:
            parsed = shlex.split(raw, posix=True)
        except ValueError as exc:
            raise ValueError("malformed /etc/os-release value") from exc
        values[key] = parsed[0] if parsed else ""
    required = ("ID", "VERSION_ID", "PRETTY_NAME")
    if any(not values.get(key) for key in required):
        raise ValueError("OS release metadata is missing ID, VERSION_ID or PRETTY_NAME")
    return {key.lower(): values[key] for key in required}


def parse_dpkg_inventory(text: str) -> list[dict]:
    records, seen = [], set()
    for number, line in enumerate(text.splitlines(), 1):
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) != 3:
            raise ValueError(f"dpkg inventory line {number} must have three tab-separated fields")
        status, binary_name, version = fields
        if len(status) < 2 or status[1] != "i":
            continue
        if not binary_name or not version:
            raise ValueError(f"dpkg inventory line {number} is incomplete")
        name, separator, architecture = binary_name.rpartition(":")
        if not separator:
            name, architecture = binary_name, "unknown"
        if not re.fullmatch(r"[A-Za-z0-9+.-]+", name) or not re.fullmatch(r"[A-Za-z0-9_.-]+", architecture):
            raise ValueError(f"dpkg inventory line {number} has an invalid package identity")
        identity = (name, architecture, version)
        if identity in seen:
            raise ValueError(f"dpkg inventory line {number} duplicates an installed package")
        seen.add(identity)
        records.append({
            "kind": "os-package",
            "name": name,
            "version": version,
            "architecture": architecture,
            "purl": f"pkg:deb/ubuntu/{_purl_segment(name)}@{_purl_segment(version)}?arch={_purl_segment(architecture)}",
        })
    if not records:
        raise ValueError("dpkg inventory contains no installed packages")
    return sorted(records, key=lambda item: item["purl"])


def parse_python_packages(text: str) -> list[dict]:
    try:
        values = json.loads(text, object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise ValueError("pip package inventory is not valid JSON") from exc
    if not isinstance(values, list):
        raise ValueError("pip package inventory must be a JSON array")
    records, seen = [], set()
    for item in values:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not isinstance(item.get("version"), str):
            raise ValueError("pip package entry must contain string name and version")
        normalized = re.sub(r"[-_.]+", "-", item["name"]).lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", normalized) or not item["version"]:
            raise ValueError("pip package entry has an invalid identity")
        if normalized in seen:
            raise ValueError(f"duplicate Python package: {normalized}")
        seen.add(normalized)
        records.append({
            "kind": "python-package",
            "name": normalized,
            "version": item["version"],
            "purl": f"pkg:pypi/{_purl_segment(normalized)}@{_purl_segment(item['version'])}",
        })
    return sorted(records, key=lambda item: item["purl"])


def parse_sdkmanager_packages(text: str) -> list[dict]:
    records, seen = [], set()
    for line in text.splitlines():
        if "|" not in line:
            continue
        fields = [part.strip() for part in line.split("|")]
        if len(fields) < 2:
            continue
        package_id, version = fields[0], fields[1]
        if package_id.lower() == "path" or version.lower() == "version":
            continue
        if not SDK_ID_RE.fullmatch(package_id) or not version:
            continue
        if package_id in seen:
            raise ValueError(f"duplicate Android SDK package: {package_id}")
        seen.add(package_id)
        records.append({"package_id": package_id, "version": version})
    if not records:
        raise ValueError("sdkmanager output contains no installed packages")
    return sorted(records, key=lambda item: item["package_id"])


def parse_action_pins(workflow_text: str) -> list[dict]:
    records, seen = [], set()
    for match in ACTION_RE.finditer(workflow_text):
        reference = match.group(1)
        if reference.startswith("./") or "@" not in reference:
            raise ValueError(f"CI-003 action must use an immutable repository SHA: {reference}")
        repository, revision = reference.rsplit("@", 1)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError(f"unsupported GitHub Action reference: {reference}")
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError(f"GitHub Action is not pinned to a full lowercase commit SHA: {reference}")
        if reference in seen:
            continue
        seen.add(reference)
        records.append({
            "kind": "github-action",
            "name": repository,
            "version": revision,
            "purl": f"pkg:github/{repository}@{revision}",
            "commit_sha": revision,
        })
    if not records:
        raise ValueError("CI-003 workflow contains no pinned GitHub Actions")
    return sorted(records, key=lambda item: item["purl"])


def parse_gradle_inputs(root_gradle: str, app_gradle: str, workflow: str) -> dict:
    plugins = {}
    for plugin_id, version in PLUGIN_RE.findall(root_gradle):
        if plugin_id in plugins:
            raise ValueError(f"duplicate Gradle plugin declaration: {plugin_id}")
        plugins[plugin_id] = version
    required = ("com.android.application", "org.jetbrains.kotlin.android")
    if any(plugin not in plugins for plugin in required):
        raise ValueError("root Gradle file is missing a required pinned Android/Kotlin plugin")
    compile_match = re.search(r"\bcompileSdk\s*=\s*(\d+)", app_gradle)
    if not compile_match:
        raise ValueError("app Gradle file does not declare a numeric compileSdk")
    checksum_match = re.search(
        r'echo\s+"([0-9a-f]{64})\s+\$RUNNER_TEMP/gradle-[^"]+-bin\.zip"\s*\|\s*sha256sum\s+--check',
        workflow,
    )
    if not checksum_match:
        raise ValueError("CI-003 workflow does not pin a Gradle distribution SHA-256")
    sdk_installs = sorted(set(re.findall(r'"((?:platforms|build-tools);[^"]+)"', workflow)))
    if not sdk_installs:
        raise ValueError("CI-003 workflow does not declare Android platform/build-tools packages")
    return {
        "agp_version": plugins["com.android.application"],
        "kotlin_version": plugins["org.jetbrains.kotlin.android"],
        "compile_sdk": compile_match.group(1),
        "gradle_sha256_expected": checksum_match.group(1),
        "sdk_packages_required": sdk_installs,
    }


def parse_properties(text: str) -> dict:
    values = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def parse_java_properties(text: str) -> dict:
    values = {}
    for key in ("java.vendor", "java.runtime.version", "java.version", "java.vm.name"):
        match = re.search(r"^\s*" + re.escape(key) + r"\s*=\s*(.+?)\s*$", text, re.MULTILINE)
        if match:
            values[key] = match.group(1)
    if not values.get("java.vendor") or not values.get("java.runtime.version"):
        raise ValueError("Java properties do not identify vendor and runtime version")
    return values


def parse_gradle_version(text: str) -> str:
    match = re.search(r"^Gradle\s+([^\s]+)", text, re.MULTILINE)
    if not match:
        raise ValueError("Gradle --version output is missing its version")
    return match.group(1)


def parse_python_version(text: str) -> str:
    match = re.search(r"^Python\s+([^\s]+)\s*$", text.strip(), re.MULTILINE)
    if not match:
        raise ValueError("python3 --version output is malformed")
    return match.group(1)


def _sdk_package_components(packages: list[dict], sdk_root: Path, required: set[str]) -> tuple[list[dict], str, str]:
    components = []
    by_id = {item["package_id"]: item for item in packages}
    missing = sorted(required - set(by_id))
    if missing:
        raise ValueError("required Android SDK packages are missing: " + ", ".join(missing))
    for item in packages:
        package_id = item["package_id"]
        source_path = sdk_root.joinpath(*package_id.split(";")) / "source.properties"
        source_digest = None
        revision = item["version"]
        if source_path.is_file() and not source_path.is_symlink():
            props = parse_properties(read_regular(source_path))
            source_revision = props.get("Pkg.Revision")
            if source_revision:
                if package_id in required and source_revision != item["version"]:
                    raise ValueError(f"sdkmanager/source.properties version mismatch for required package {package_id}")
                revision = source_revision
            source_digest = sha256_file(source_path)
        elif package_id in required:
            raise ValueError(f"required Android SDK package has no source.properties: {package_id}")
        purl_path = "/".join(_purl_segment(part) for part in package_id.split(";"))
        components.append({
            "kind": "android-sdk-package",
            "name": package_id,
            "version": revision,
            "purl": f"pkg:generic/android-sdk/{purl_path}@{_purl_segment(revision)}",
            "sha256": source_digest,
        })
    required_build_tools = [package_id for package_id in required if package_id.startswith("build-tools;")]
    if len(required_build_tools) != 1:
        raise ValueError("CI-003 requires exactly one workflow-pinned build-tools package")
    build_tools = by_id.get(required_build_tools[0])
    if not build_tools:
        raise ValueError("workflow-pinned Android build-tools package is not installed")

    cmdline_path = sdk_root / "cmdline-tools" / "latest" / "source.properties"
    cmdline_props = parse_properties(read_regular(cmdline_path))
    sdkmanager_version = cmdline_props.get("Pkg.Revision")
    if not sdkmanager_version:
        raise ValueError("Android command-line tools revision is missing")
    cmdline_digest = sha256_file(cmdline_path)
    cmdline_names = {"cmdline-tools;latest", f"cmdline-tools;{sdkmanager_version}"}
    cmdline_component = next((item for item in components if item["name"] in cmdline_names), None)
    if cmdline_component:
        cmdline_component["version"] = sdkmanager_version
        cmdline_component["sha256"] = cmdline_digest
    else:
        package_id = f"cmdline-tools;{sdkmanager_version}"
        components.append({
            "kind": "android-sdk-package",
            "name": package_id,
            "version": sdkmanager_version,
            "purl": f"pkg:generic/android-sdk/cmdline-tools/{_purl_segment(sdkmanager_version)}@{_purl_segment(sdkmanager_version)}",
            "sha256": cmdline_digest,
        })

    platform_tools_path = sdk_root / "platform-tools" / "source.properties"
    platform_tools_props = parse_properties(read_regular(platform_tools_path))
    platform_tools_version = platform_tools_props.get("Pkg.Revision")
    if not platform_tools_version:
        raise ValueError("Android platform-tools revision is missing")
    platform_tools_digest = sha256_file(platform_tools_path)
    platform_component = next((item for item in components if item["name"] == "platform-tools"), None)
    if platform_component:
        platform_component["version"] = platform_tools_version
        platform_component["sha256"] = platform_tools_digest
    else:
        components.append({
            "kind": "android-sdk-package",
            "name": "platform-tools",
            "version": platform_tools_version,
            "purl": f"pkg:generic/android-sdk/platform-tools@{_purl_segment(platform_tools_version)}",
            "sha256": platform_tools_digest,
        })
    return components, build_tools["version"], sdkmanager_version


def collect_inventory(args) -> dict:
    if not COMMIT_RE.fullmatch(args.commit):
        raise ValueError("expected full lowercase Git commit SHA")
    if type(args.created_epoch) is not int or args.created_epoch < 0:
        raise ValueError("created epoch must be a non-negative integer")
    if not args.runner_label or not args.runner_image_os or not args.runner_image_version:
        raise ValueError("runner label and immutable hosted-image identity are required")
    os_release = parse_os_release(read_regular(args.os_release_file))
    if os_release["id"] != "ubuntu":
        raise ValueError("CI-003 build environment is expected to run on Ubuntu")
    dpkg = parse_dpkg_inventory(read_regular(args.dpkg_packages_file))
    python_packages = parse_python_packages(read_regular(args.python_packages_file))
    sdk_packages = parse_sdkmanager_packages(read_regular(args.sdk_packages_file))
    workflow = read_regular(args.workflow_file)
    root_gradle = read_regular(args.root_gradle_file)
    app_gradle = read_regular(args.app_gradle_file)
    gradle_inputs = parse_gradle_inputs(root_gradle, app_gradle, workflow)
    actions = parse_action_pins(workflow)
    gradle_version = parse_gradle_version(read_regular(args.gradle_version_file))
    if args.gradle_zip.is_symlink() or not args.gradle_zip.is_file():
        raise ValueError("Gradle distribution input is missing, not a regular file, or is a symlink")
    gradle_digest = sha256_file(args.gradle_zip)
    if gradle_digest != gradle_inputs["gradle_sha256_expected"]:
        raise ValueError("downloaded Gradle distribution does not match the workflow-pinned SHA-256")
    java = parse_java_properties(read_regular(args.java_properties_file))
    python_version = parse_python_version(args.python_version)
    sdk_required = set(gradle_inputs["sdk_packages_required"]) | {
        f"platforms;android-{gradle_inputs['compile_sdk']}"
    }
    sdk_components, build_tools_version, sdkmanager_version = _sdk_package_components(
        sdk_packages, args.sdk_root, sdk_required
    )
    java_vendor = java["java.vendor"]
    jdk_distribution = "Temurin" if "Adoptium" in java_vendor else java_vendor
    jdk_version = args.jdk_version.strip()
    if not jdk_version:
        raise ValueError("JDK version string is missing")
    agp = gradle_inputs["agp_version"]
    kotlin = gradle_inputs["kotlin_version"]
    compile_sdk = gradle_inputs["compile_sdk"]
    components = []
    components.extend(dpkg)
    components.extend(python_packages)
    components.extend(sdk_components)
    components.extend(actions)
    components.extend([
        {
            "kind": "operating-system",
            "name": os_release["pretty_name"],
            "version": os_release["version_id"],
            "purl": f"pkg:generic/{_purl_segment(os_release['id'])}@{_purl_segment(os_release['version_id'])}",
        },
        {
            "kind": "jdk-runtime",
            "name": "Eclipse Adoptium Temurin JDK",
            "version": java["java.runtime.version"],
            "purl": f"pkg:generic/eclipse-temurin-jdk@{_purl_segment(java['java.runtime.version'])}",
            "metadata": java,
        },
        {
            "kind": "python-runtime",
            "name": "Python",
            "version": python_version,
            "purl": f"pkg:generic/python@{_purl_segment(python_version)}",
        },
        {
            "kind": "gradle-distribution",
            "name": "Gradle",
            "version": gradle_version,
            "purl": f"pkg:generic/gradle@{_purl_segment(gradle_version)}",
            "sha256": gradle_digest,
        },
        {
            "kind": "gradle-plugin",
            "name": "com.android.tools.build:gradle",
            "version": agp,
            "purl": f"pkg:maven/com.android.tools.build/gradle@{_purl_segment(agp)}",
        },
        {
            "kind": "gradle-plugin",
            "name": "org.jetbrains.kotlin:kotlin-gradle-plugin",
            "version": kotlin,
            "purl": f"pkg:maven/org.jetbrains.kotlin/kotlin-gradle-plugin@{_purl_segment(kotlin)}",
        },
    ])
    purls = [item["purl"] for item in components]
    if len(purls) != len(set(purls)):
        raise ValueError("build environment contains duplicate package URLs")
    components.sort(key=lambda item: (item["kind"], item["purl"]))
    created = datetime.fromtimestamp(args.created_epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    counts = {}
    for item in components:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    return {
        "schema": "mrnothing-ci006-build-environment-v1",
        "source_commit": args.commit,
        "created": created,
        "runner": {
            "label": args.runner_label,
            "image_os": args.runner_image_os,
            "image_version": args.runner_image_version,
            "os_release": os_release,
        },
        "toolchain": {
            "operating_system": args.runner_label,
            "jdk_distribution": jdk_distribution,
            "jdk_version": jdk_version,
            "jdk_runtime_version": java["java.runtime.version"],
            "jdk_vendor": java_vendor,
            "gradle_version": gradle_version,
            "gradle_sha256": gradle_digest,
            "agp_version": agp,
            "kotlin_version": kotlin,
            "compile_sdk": compile_sdk,
            "build_tools": build_tools_version,
            "sdkmanager_version": sdkmanager_version,
        },
        "counts": dict(sorted(counts.items())),
        "components": components,
        "scope": SCOPE,
    }


def make_spdx(inventory: dict, inventory_sha256: str) -> dict:
    commit = inventory["source_commit"]
    created = inventory["created"]
    root_id = "SPDXRef-Package-CI003BuildEnvironment"
    root_purl = f"pkg:generic/mrnothing-ci003-build-environment@{commit[:12]}"
    packages = [{
        "name": "MrNothing CI-003 Build Environment",
        "SPDXID": root_id,
        "versionInfo": commit[:12],
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "copyrightText": "NOASSERTION",
        "primaryPackagePurpose": "OTHER",
        "externalRefs": [{"referenceCategory": "PACKAGE-MANAGER", "referenceType": "purl", "referenceLocator": root_purl}],
    }]
    relationships = [{
        "spdxElementId": "SPDXRef-DOCUMENT",
        "relationshipType": "DESCRIBES",
        "relatedSpdxElement": root_id,
    }]
    for component in inventory["components"]:
        purl = component["purl"]
        package_id = "SPDXRef-Package-" + hashlib.sha256(purl.encode("utf-8")).hexdigest()[:24]
        package = {
            "name": component["name"],
            "SPDXID": package_id,
            "versionInfo": component["version"],
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
            "externalRefs": [{"referenceCategory": "PACKAGE-MANAGER", "referenceType": "purl", "referenceLocator": purl}],
        }
        if component.get("sha256"):
            package["checksums"] = [{"algorithm": "SHA256", "checksumValue": component["sha256"]}]
        packages.append(package)
        relationships.append({
            "spdxElementId": root_id,
            "relationshipType": "DEPENDS_ON",
            "relatedSpdxElement": package_id,
        })
    packages.sort(key=lambda item: item["SPDXID"])
    relationships[1:] = sorted(relationships[1:], key=lambda item: item["relatedSpdxElement"])
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"MrNothing-OS-CI003-build-environment-{commit[:12]}",
        "documentNamespace": f"https://spdx.org/spdxdocs/mrnothing-ci003-build-environment-{commit}-{inventory_sha256}",
        "creationInfo": {"created": created, "creators": [f"Tool: {TOOL_NAME}"]},
        "packages": packages,
        "relationships": relationships,
        "annotations": [{
            "annotationDate": created,
            "annotationType": "OTHER",
            "annotator": f"Tool: {TOOL_NAME}",
            "comment": SCOPE,
        }],
        "files": [],
        "snippets": [],
        "hasExtractedLicensingInfos": [],
    }


def validate_inventory_and_sbom(inventory_path: Path, sbom_path: Path, expected_commit: str) -> tuple[dict, dict]:
    if not COMMIT_RE.fullmatch(expected_commit):
        raise ValueError("expected full lowercase Git commit SHA")
    inventory = load_json(inventory_path)
    sbom = load_json(sbom_path)
    if inventory.get("schema") != "mrnothing-ci006-build-environment-v1":
        raise ValueError("unknown build environment inventory schema")
    if inventory.get("source_commit") != expected_commit:
        raise ValueError("build environment inventory source commit mismatch")
    if not isinstance(inventory.get("created"), str) or not re.fullmatch(
        r"\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z", inventory["created"]
    ):
        raise ValueError("build environment inventory creation time is malformed")

    components = inventory.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("build environment inventory components must be a non-empty array")
    seen_purls = set()
    observed_counts = {}
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            raise ValueError(f"build environment component {index} must be an object")
        for field in ("kind", "name", "version", "purl"):
            value = component.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"build environment component {index} has an invalid {field}")
        if not component["purl"].startswith("pkg:"):
            raise ValueError(f"build environment component {index} has an invalid package URL")
        if component["purl"] in seen_purls:
            raise ValueError("build environment inventory contains a duplicate package URL")
        seen_purls.add(component["purl"])
        digest = component.get("sha256")
        if digest is not None and (
            not isinstance(digest, str) or not SHA256_RE.fullmatch(digest)
        ):
            raise ValueError(f"build environment component {index} checksum must be lowercase SHA-256")
        observed_counts[component["kind"]] = observed_counts.get(component["kind"], 0) + 1

    if components != sorted(components, key=lambda item: (item["kind"], item["purl"])):
        raise ValueError("build environment inventory components are not in canonical order")
    if inventory.get("counts") != dict(sorted(observed_counts.items())):
        raise ValueError("build environment inventory component counts do not match its records")

    if sbom.get("spdxVersion") != "SPDX-2.3":
        raise ValueError("build environment SBOM must be SPDX-2.3")
    inventory_digest = sha256_file(inventory_path)
    expected_sbom = make_spdx(inventory, inventory_digest)
    if sbom != expected_sbom:
        raise ValueError(
            "build environment SPDX document does not exactly match the canonical inventory-derived document"
        )
    return inventory, sbom

def _provenance_link(inventory_path: Path, sbom_path: Path) -> dict:
    return {
        "schema": "mrnothing-ci006-build-environment-v1",
        "inventory": {"filename": inventory_path.name, "sha256": sha256_file(inventory_path)},
        "sbom": {"filename": sbom_path.name, "format": "SPDX-2.3", "sha256": sha256_file(sbom_path)},
        "scope": SCOPE,
    }


def attach_provenance(inventory_path: Path, sbom_path: Path, provenance_path: Path, expected_commit: str) -> dict:
    inventory, _ = validate_inventory_and_sbom(inventory_path, sbom_path, expected_commit)
    provenance = load_json(provenance_path)
    if provenance.get("schema") != "mrnothing-ci003-provenance-v2" or provenance.get("source_commit") != expected_commit:
        raise ValueError("build provenance schema or source commit mismatch")
    toolchain = inventory["toolchain"]
    expected_environment = {
        "operating_system": toolchain["operating_system"],
        "jdk_distribution": toolchain["jdk_distribution"],
        "jdk_version": toolchain["jdk_version"],
        "gradle_version": toolchain["gradle_version"],
        "gradle_sha256": toolchain["gradle_sha256"],
        "agp_version": toolchain["agp_version"],
        "kotlin_version": toolchain["kotlin_version"],
        "compile_sdk": toolchain["compile_sdk"],
        "build_tools": toolchain["build_tools"],
        "sdkmanager_version": toolchain["sdkmanager_version"],
    }
    if provenance.get("build_environment") != expected_environment:
        raise ValueError("build environment inventory does not match provenance toolchain fields")
    link = _provenance_link(inventory_path, sbom_path)
    existing = provenance.get("build_environment_sbom")
    if existing is not None and existing != link:
        raise ValueError("existing build environment SBOM provenance link differs; refusing overwrite")
    provenance["build_environment_sbom"] = link
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return link


def verify_bundles(first: Path, second: Path, expected_commit: str, output: Path) -> dict:
    if not COMMIT_RE.fullmatch(expected_commit):
        raise ValueError("expected full lowercase commit SHA")
    bundles = []
    for directory in (first, second):
        inventory_path = directory / "build-environment.inventory.json"
        sbom_path = directory / "build-environment.spdx.json"
        provenance_path = directory / "provenance.json"
        if not all(path.is_file() and not path.is_symlink() for path in (inventory_path, sbom_path, provenance_path)):
            raise ValueError(f"build environment bundle is incomplete: {directory}")
        inventory, sbom = validate_inventory_and_sbom(inventory_path, sbom_path, expected_commit)
        provenance = load_json(provenance_path)
        expected_link = _provenance_link(inventory_path, sbom_path)
        if provenance.get("build_environment_sbom") != expected_link:
            raise ValueError("build environment SBOM hashes do not match provenance")
        if provenance.get("build_environment") != {
            "operating_system": inventory["toolchain"]["operating_system"],
            "jdk_distribution": inventory["toolchain"]["jdk_distribution"],
            "jdk_version": inventory["toolchain"]["jdk_version"],
            "gradle_version": inventory["toolchain"]["gradle_version"],
            "gradle_sha256": inventory["toolchain"]["gradle_sha256"],
            "agp_version": inventory["toolchain"]["agp_version"],
            "kotlin_version": inventory["toolchain"]["kotlin_version"],
            "compile_sdk": inventory["toolchain"]["compile_sdk"],
            "build_tools": inventory["toolchain"]["build_tools"],
            "sdkmanager_version": inventory["toolchain"]["sdkmanager_version"],
        }:
            raise ValueError("build environment inventory disagrees with provenance")
        bundles.append({
            "directory": directory,
            "inventory_path": inventory_path,
            "sbom_path": sbom_path,
            "inventory": inventory,
            "sbom": sbom,
        })
    inventory_equal = bundles[0]["inventory_path"].read_bytes() == bundles[1]["inventory_path"].read_bytes()
    sbom_equal = bundles[0]["sbom_path"].read_bytes() == bundles[1]["sbom_path"].read_bytes()
    provenance_environment_equal = (
        bundles[0]["inventory"]["runner"] == bundles[1]["inventory"]["runner"]
        and bundles[0]["inventory"]["toolchain"] == bundles[1]["inventory"]["toolchain"]
    )
    result = {
        "schema": "mrnothing-ci006-build-environment-verification-v1",
        "source_commit": expected_commit,
        "build_environment_identical": inventory_equal and sbom_equal and provenance_environment_equal,
        "checks": {
            "inventory_identical": inventory_equal,
            "spdx_sbom_identical": sbom_equal,
            "runner_identity_identical": bundles[0]["inventory"]["runner"] == bundles[1]["inventory"]["runner"],
            "toolchain_identical": bundles[0]["inventory"]["toolchain"] == bundles[1]["inventory"]["toolchain"],
            "provenance_hashes_valid": True,
            "spdx_inventory_binding_valid": True,
        },
        "component_count": len(bundles[0]["inventory"]["components"]),
        "component_counts": bundles[0]["inventory"]["counts"],
        "inventory_sha256": [sha256_file(item["inventory_path"]) for item in bundles],
        "sbom_sha256": [sha256_file(item["sbom_path"]) for item in bundles],
        "scope": SCOPE,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not result["build_environment_identical"]:
        raise ValueError("independent runner build environments are not identical")
    return result


def run_negative_control(workflow_path: Path) -> dict:
    workflow = read_regular(workflow_path)
    match = ACTION_RE.search(workflow)
    if not match:
        raise ValueError("negative control could not find a GitHub Action reference")
    bad_reference = match.group(1)
    repository = bad_reference.rsplit("@", 1)[0] if "@" in bad_reference else bad_reference
    mutated = workflow[:match.start(1)] + repository + "@v7" + workflow[match.end(1):]
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory) / "workflow.yml"
        fixture.write_text(mutated, encoding="utf-8")
        try:
            parse_action_pins(read_regular(fixture))
        except ValueError as exc:
            return {"negative_control": "passed", "rejected_reference": repository + "@v7", "reason": str(exc)}
    raise ValueError("negative control failed: mutable GitHub Action reference was accepted")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    for name in ("commit", "runner-label", "runner-image-os", "runner-image-version", "jdk-version", "python-version"):
        generate.add_argument("--" + name, required=True)
    generate.add_argument("--created-epoch", type=int, required=True)
    for name in (
        "os-release-file", "dpkg-packages-file", "python-packages-file", "sdk-packages-file",
        "sdk-root", "gradle-zip", "gradle-version-file", "java-properties-file", "workflow-file",
        "root-gradle-file", "app-gradle-file", "output-inventory", "output-sbom",
    ):
        generate.add_argument("--" + name, type=Path, required=True)
    attach = sub.add_parser("attach")
    for name in ("inventory", "sbom", "provenance"):
        attach.add_argument("--" + name, type=Path, required=True)
    attach.add_argument("--expected-commit", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--first", type=Path, required=True)
    verify.add_argument("--second", type=Path, required=True)
    verify.add_argument("--expected-commit", required=True)
    verify.add_argument("--output", type=Path, required=True)
    negative = sub.add_parser("negative-control")
    negative.add_argument("--workflow", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "generate":
        inventory = collect_inventory(args)
        args.output_inventory.parent.mkdir(parents=True, exist_ok=True)
        args.output_inventory.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        inventory_digest = sha256_file(args.output_inventory)
        sbom = make_spdx(inventory, inventory_digest)
        args.output_sbom.parent.mkdir(parents=True, exist_ok=True)
        args.output_sbom.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        validate_inventory_and_sbom(args.output_inventory, args.output_sbom, args.commit)
        print(json.dumps({"components": len(inventory["components"]), "inventory_sha256": inventory_digest,
                          "sbom_sha256": sha256_file(args.output_sbom)}, sort_keys=True))
    elif args.command == "attach":
        print(json.dumps(attach_provenance(args.inventory, args.sbom, args.provenance, args.expected_commit), sort_keys=True))
    elif args.command == "verify":
        print(json.dumps(verify_bundles(args.first, args.second, args.expected_commit, args.output), sort_keys=True))
    elif args.command == "negative-control":
        print(json.dumps(run_negative_control(args.workflow), sort_keys=True))


if __name__ == "__main__":
    main()
