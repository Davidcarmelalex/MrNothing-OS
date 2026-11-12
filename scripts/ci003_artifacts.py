#!/usr/bin/env python3
"""Deterministic unsigned Android artifact, runtime SBOM and CI provenance helpers."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile
from urllib.parse import quote

try:
    from .release_variant_metadata import load_release_variant_metadata
except ImportError:  # Direct script execution from CI.
    from release_variant_metadata import load_release_variant_metadata

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
NOASSERTION = "NOASSERTION"
TOOL_NAME = "MrNothing CI-003 Artifact and SBOM Generator"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def created_utc(epoch: int) -> str:
    if type(epoch) is not int or epoch < 0:
        raise ValueError("created epoch must be a non-negative integer")
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _is_signature_entry(name: str) -> bool:
    upper = name.upper()
    if not upper.startswith("META-INF/"):
        return False
    basename = PurePosixPath(upper).name
    return basename.startswith("SIG-") or basename.endswith((".SF", ".RSA", ".DSA", ".EC"))

def inspect_unsigned_apk(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("APK is missing, not a regular file, or empty")
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise ValueError("APK contains duplicate ZIP entry names")
            entries = []
            for info in infos:
                name = info.filename
                parts = PurePosixPath(name).parts
                if not name or name.startswith("/") or "\\" in name or ".." in parts:
                    raise ValueError("APK contains an unsafe ZIP entry path")
                if info.flag_bits & 0x1:
                    raise ValueError("APK contains an encrypted ZIP entry")
                mode = (info.external_attr >> 16) & 0o170000
                if mode == stat.S_IFLNK:
                    raise ValueError("APK contains a symbolic-link ZIP entry")
                if _is_signature_entry(name):
                    raise ValueError("APK contains a v1 signing entry; expected unsigned output")
                data = archive.read(info)
                entries.append({"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
            if archive.testzip() is not None:
                raise ValueError("APK ZIP CRC validation failed")
            signed_block = False
            if archive.start_dir >= 16:
                with path.open("rb") as raw:
                    raw.seek(archive.start_dir - 16)
                    signed_block = raw.read(16) == b"APK Sig Block 42"
            if signed_block:
                raise ValueError("APK contains an APK Signing Block; expected unsigned output")
    except zipfile.BadZipFile as exc:
        raise ValueError("APK is not a valid ZIP/APK archive") from exc
    entries.sort(key=lambda item: item["name"])
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "entry_count": len(entries),
        "entries": entries,
        "normalized_entries_sha256": hashlib.sha256(canonical).hexdigest(),
        "signature_status": "unsigned",
    }

def compare_apks(first: Path, second: Path) -> dict:
    left = inspect_unsigned_apk(first)
    right = inspect_unsigned_apk(second)
    normalized_equal = left["entries"] == right["entries"]
    byte_equal = left["sha256"] == right["sha256"] and left["bytes"] == right["bytes"]
    return {
        "schema": "mrnothing-ci003-comparison-v1",
        "byte_identical": byte_equal,
        "normalized_content_identical": normalized_equal,
        "reproducible": byte_equal and normalized_equal,
        "first": {k: left[k] for k in ("sha256", "bytes", "entry_count", "normalized_entries_sha256")},
        "second": {k: right[k] for k in ("sha256", "bytes", "entry_count", "normalized_entries_sha256")},
    }

def parse_runtime_inventory(path: Path) -> list[dict]:
    if not path.is_file():
        raise ValueError("Gradle runtime dependency inventory is missing")
    records, seen = [], set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) != 5:
            raise ValueError(f"inventory line {line_number} must contain five tab-separated fields")
        group, name, version, filename, digest = fields
        if not all((group, name, version, filename)):
            raise ValueError(f"inventory line {line_number} contains an empty field")
        if Path(filename).name != filename or filename in (".", ".."):
            raise ValueError(f"inventory line {line_number} has an unsafe artifact filename")
        if not SHA256_RE.fullmatch(digest):
            raise ValueError(f"inventory line {line_number} has an invalid SHA-256")
        identity = (group, name, version, filename)
        if identity in seen:
            raise ValueError(f"inventory line {line_number} duplicates an artifact")
        seen.add(identity)
        records.append({"group": group, "name": name, "version": version, "filename": filename, "sha256": digest})
    return sorted(records, key=lambda item: (item["group"], item["name"], item["version"], item["filename"]))

def generate_sbom(inventory: Path, commit: str, app_version: str, created_epoch: int, output: Path) -> dict:
    if not COMMIT_RE.fullmatch(commit):
        raise ValueError("expected full lowercase Git commit SHA")
    if not app_version or any(ch in app_version for ch in "\r\n\t"):
        raise ValueError("invalid application version")
    records = parse_runtime_inventory(inventory)
    inventory_digest = sha256_file(inventory)
    created = created_utc(created_epoch)
    app_id = "SPDXRef-Package-MrNothingOS"
    packages = [{
        "name": "MrNothingOS", "SPDXID": app_id, "versionInfo": app_version,
        "downloadLocation": NOASSERTION, "filesAnalyzed": False,
        "licenseConcluded": NOASSERTION, "licenseDeclared": NOASSERTION,
        "copyrightText": NOASSERTION, "primaryPackagePurpose": "APPLICATION",
        "externalRefs": [{"referenceCategory": "PACKAGE-MANAGER", "referenceType": "purl",
                          "referenceLocator": f"pkg:generic/MrNothingOS@{quote(app_version, safe='.-_')}"}],
    }]
    relationships = [{"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES",
                      "relatedSpdxElement": app_id}]
    for item in records:
        identity = f'{item["group"]}:{item["name"]}:{item["version"]}:{item["filename"]}'
        package_id = "SPDXRef-Package-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
        purl = (f'pkg:maven/{quote(item["group"], safe=".-_")}/'
                f'{quote(item["name"], safe=".-_")}@{quote(item["version"], safe=".-_")}')
        packages.append({
            "name": f'{item["group"]}:{item["name"]}', "SPDXID": package_id,
            "versionInfo": item["version"], "packageFileName": item["filename"],
            "downloadLocation": NOASSERTION, "filesAnalyzed": False,
            "licenseConcluded": NOASSERTION, "licenseDeclared": NOASSERTION,
            "copyrightText": NOASSERTION,
            "checksums": [{"algorithm": "SHA256", "checksumValue": item["sha256"]}],
            "externalRefs": [{"referenceCategory": "PACKAGE-MANAGER", "referenceType": "purl",
                              "referenceLocator": purl}],
        })
        relationships.append({"spdxElementId": app_id, "relationshipType": "DEPENDS_ON",
                               "relatedSpdxElement": package_id})
    packages[1:] = sorted(packages[1:], key=lambda item: item["SPDXID"])
    relationships[1:] = sorted(relationships[1:], key=lambda item: item["relatedSpdxElement"])
    document = {
        "spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0", "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"MrNothing-OS-Android-runtime-{commit[:12]}",
        "documentNamespace": f"https://spdx.org/spdxdocs/mrnothing-os-runtime-{commit}-{inventory_digest}",
        "creationInfo": {"created": created, "creators": [f"Tool: {TOOL_NAME}"]},
        "packages": packages, "relationships": relationships,
        "annotations": [{
            "annotationDate": created, "annotationType": "OTHER", "annotator": f"Tool: {TOOL_NAME}",
            "comment": ("Scope is the resolved Android releaseRuntimeClasspath only. Build plugins, Gradle internals, "
                        "SDK packages and operating-system packages are recorded separately in build provenance "
                        "and are not represented as application runtime dependencies. This is not a complete "
                        "build-environment SBOM.")
        }],
        "files": [], "snippets": [], "hasExtractedLicensingInfos": [],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return document

def generate_provenance(apk: Path, sbom: Path, commit: str, created_epoch: int,
                        environment: dict, release_variant_metadata: Path, output: Path) -> dict:
    if not COMMIT_RE.fullmatch(commit):
        raise ValueError("expected full lowercase Git commit SHA")
    apk_info = inspect_unsigned_apk(apk)
    if not sbom.is_file():
        raise ValueError("SPDX SBOM is missing")
    try:
        sbom_document = json.loads(sbom.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("SPDX SBOM is not valid JSON") from exc
    if sbom_document.get("spdxVersion") != "SPDX-2.3":
        raise ValueError("expected an SPDX-2.3 SBOM")
    required = ("operating_system", "jdk_distribution", "jdk_version", "gradle_version",
                "gradle_sha256", "agp_version", "kotlin_version", "compile_sdk",
                "build_tools", "sdkmanager_version")
    if any(not environment.get(key) for key in required):
        raise ValueError("build environment is missing a required toolchain input")
    if not SHA256_RE.fullmatch(environment["gradle_sha256"]):
        raise ValueError("invalid Gradle distribution SHA-256")
    variant = load_release_variant_metadata(release_variant_metadata)
    release_variant = {
        "application_id": variant["application_id"],
        "variant_name": variant["variant_name"],
        "build_type": variant["build_type"],
        "metadata_sha256": variant["sha256"],
    }
    record = {
        "schema": "mrnothing-ci003-provenance-v2", "source_commit": commit,
        "created": created_utc(created_epoch), "build_environment": environment,
        "release_variant": release_variant,
        "artifact": {
            "filename": apk.name, "bytes": apk_info["bytes"], "sha256": apk_info["sha256"],
            "signature_status": "unsigned", "entry_count": apk_info["entry_count"],
            "normalized_entries_sha256": apk_info["normalized_entries_sha256"],
        },
        "sbom": {"filename": sbom.name, "format": "SPDX-2.3",
                 "sha256": sha256_file(sbom), "scope": "Android releaseRuntimeClasspath"},
        "cross_runner_comparison": "pending-two-runner-verification",
        "release_ready": False, "provenance_signed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record

def verify_bundles(first: Path, second: Path, expected_commit: str) -> dict:
    if not COMMIT_RE.fullmatch(expected_commit):
        raise ValueError("expected full lowercase commit SHA")
    bundles = []
    for directory in (first, second):
        apk, sbom = directory / "app-release-unsigned.apk", directory / "sbom.spdx.json"
        inventory, provenance_path = directory / "release-runtime-dependencies.tsv", directory / "provenance.json"
        variant_metadata_path = directory / "release-variant-metadata.json"
        if not all(path.is_file() for path in (apk, sbom, inventory, provenance_path, variant_metadata_path)):
            raise ValueError(f"bundle is incomplete: {directory}")
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        sbom_document = json.loads(sbom.read_text(encoding="utf-8"))
        if provenance.get("schema") != "mrnothing-ci003-provenance-v2":
            raise ValueError("unknown provenance schema")
        variant = load_release_variant_metadata(variant_metadata_path)
        expected_variant = {
            "application_id": variant["application_id"],
            "variant_name": variant["variant_name"],
            "build_type": variant["build_type"],
            "metadata_sha256": variant["sha256"],
        }
        if provenance.get("release_variant") != expected_variant:
            raise ValueError("release variant metadata does not match provenance")
        if provenance.get("source_commit") != expected_commit:
            raise ValueError("bundle source commit does not match expected commit")
        if provenance.get("release_ready") is not False or provenance.get("provenance_signed") is not False:
            raise ValueError("CI-003 bundle must remain explicitly non-release and unsigned")
        if provenance.get("artifact", {}).get("signature_status") != "unsigned":
            raise ValueError("provenance does not declare an unsigned APK")
        apk_info = inspect_unsigned_apk(apk)
        if provenance["artifact"].get("sha256") != apk_info["sha256"]:
            raise ValueError("APK digest does not match its provenance")
        if provenance["artifact"].get("normalized_entries_sha256") != apk_info["normalized_entries_sha256"]:
            raise ValueError("APK normalized-entry digest does not match its provenance")
        if provenance["sbom"].get("sha256") != sha256_file(sbom):
            raise ValueError("SBOM digest does not match its provenance")
        if sbom_document.get("spdxVersion") != "SPDX-2.3":
            raise ValueError("bundle does not contain an SPDX-2.3 SBOM")
        parse_runtime_inventory(inventory)
        bundles.append({"apk": apk, "sbom": sbom, "inventory": inventory,
                        "provenance": provenance, "release_variant": expected_variant,
                        "sbom_sha256": sha256_file(sbom),
                        "inventory_sha256": sha256_file(inventory)})
    comparison = compare_apks(bundles[0]["apk"], bundles[1]["apk"])
    sbom_equal = bundles[0]["sbom"].read_bytes() == bundles[1]["sbom"].read_bytes()
    inventory_equal = bundles[0]["inventory"].read_bytes() == bundles[1]["inventory"].read_bytes()
    environment_equal = bundles[0]["provenance"]["build_environment"] == bundles[1]["provenance"]["build_environment"]
    commit_equal = bundles[0]["provenance"]["source_commit"] == bundles[1]["provenance"]["source_commit"]
    release_variant_equal = bundles[0]["release_variant"] == bundles[1]["release_variant"]
    reproducible = (
        comparison["reproducible"] and sbom_equal and inventory_equal and
        environment_equal and commit_equal and release_variant_equal
    )
    return {
        "schema": "mrnothing-ci003-verification-v1", "source_commit": expected_commit,
        "reproducible": reproducible, "release_ready": False,
        "checks": {
            "unsigned_apks": True, "byte_identical_apks": comparison["byte_identical"],
            "normalized_apk_contents_identical": comparison["normalized_content_identical"],
            "sbom_identical": sbom_equal, "runtime_inventory_identical": inventory_equal,
            "toolchain_identical": environment_equal, "source_commit_identical": commit_equal,
            "release_variant_identical": release_variant_equal,
        },
        "release_variant": bundles[0]["release_variant"],
        "apk_comparison": comparison,
        "sbom_sha256": [item["sbom_sha256"] for item in bundles],
        "runtime_inventory_sha256": [item["inventory_sha256"] for item in bundles],
        "build_environment": bundles[0]["provenance"]["build_environment"],
        "interpretation": (
            "Byte-identical unsigned APKs and matching runtime SBOM/provenance were observed on two independent "
            "GitHub-hosted runner jobs. This does not establish a signed production release or complete build-environment SBOM."
            if reproducible else
            "Independent-runner equivalence failed. Preserve both bundles and investigate the first differing artifact, SBOM, inventory or toolchain input."
        ),
    }

def write_result(result: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("sbom")
    p.add_argument("--inventory", type=Path, required=True); p.add_argument("--commit", required=True)
    p.add_argument("--app-version", required=True); p.add_argument("--created-epoch", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("provenance")
    p.add_argument("--apk", type=Path, required=True); p.add_argument("--sbom", type=Path, required=True)
    p.add_argument("--commit", required=True); p.add_argument("--created-epoch", type=int, required=True)
    p.add_argument("--release-variant-metadata", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    for name in ("operating-system", "jdk-distribution", "jdk-version", "gradle-version", "gradle-sha256",
                 "agp-version", "kotlin-version", "compile-sdk", "build-tools", "sdkmanager-version"):
        p.add_argument("--" + name, required=True)
    p = sub.add_parser("compare")
    p.add_argument("--first", type=Path, required=True); p.add_argument("--second", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("verify")
    p.add_argument("--first", type=Path, required=True); p.add_argument("--second", type=Path, required=True)
    p.add_argument("--expected-commit", required=True); p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "sbom":
        result = generate_sbom(args.inventory, args.commit, args.app_version, args.created_epoch, args.output)
        print(f"Generated SPDX-2.3 runtime SBOM: {args.output} ({len(result['packages'])} packages)")
    elif args.command == "provenance":
        environment = {
            "operating_system": args.operating_system, "jdk_distribution": args.jdk_distribution,
            "jdk_version": args.jdk_version, "gradle_version": args.gradle_version,
            "gradle_sha256": args.gradle_sha256, "agp_version": args.agp_version,
            "kotlin_version": args.kotlin_version, "compile_sdk": args.compile_sdk,
            "build_tools": args.build_tools, "sdkmanager_version": args.sdkmanager_version,
        }
        generate_provenance(
            args.apk, args.sbom, args.commit, args.created_epoch, environment,
            args.release_variant_metadata, args.output
        )
        print(f"Generated unsigned, non-release provenance: {args.output}")
    elif args.command == "compare":
        result = compare_apks(args.first, args.second); write_result(result, args.output)
        if not result["reproducible"]: raise SystemExit(1)
    else:
        result = verify_bundles(args.first, args.second, args.expected_commit); write_result(result, args.output)
        if not result["reproducible"]: raise SystemExit(1)

if __name__ == "__main__":
    main()
