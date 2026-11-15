#!/usr/bin/env python3
"""ROM-003 offline, fail-closed staged unsigned launcher APK integrity gate.

This checks operator-supplied claims and bytes, NOT independent builder identity,
source-to-binary reproducibility, signatures, licensing, or release authorization.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import zipfile

SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = {"schema", "source_commit", "apk_sha256", "apk_kind", "build_variant",
            "unsigned", "provenance_sha256", "release_manifest_sha256"}


def object_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=object_no_duplicates)


def safe_regular_file(path):
    if path.is_symlink():
        raise ValueError("symlink forbidden")
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise ValueError("not a private regular file")
    return path


def digest(path):
    h = hashlib.sha256()
    with safe_regular_file(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(apk, record, provenance, release_manifest, expected_source):
    for p in (apk, record, provenance, release_manifest):
        safe_regular_file(p)
    r = read_json(record)
    if not isinstance(r, dict) or set(r) != REQUIRED:
        raise ValueError("invalid provenance record schema")
    if r["schema"] != "mrnothing-staged-apk-v1":
        raise ValueError("unsupported schema")
    if not isinstance(expected_source, str) or not COMMIT.fullmatch(expected_source):
        raise ValueError("invalid pinned source commit")
    if r["source_commit"] != expected_source:
        raise ValueError("source commit mismatch")
    if r["apk_kind"] != "launcher" or r["build_variant"] != "release" or r["unsigned"] is not True:
        raise ValueError("debug/signed/non-launcher artifact forbidden")
    for key in ("apk_sha256", "provenance_sha256", "release_manifest_sha256"):
        if not isinstance(r[key], str) or not SHA.fullmatch(r[key]):
            raise ValueError("invalid digest")
    if digest(apk) != r["apk_sha256"] or digest(provenance) != r["provenance_sha256"] or digest(release_manifest) != r["release_manifest_sha256"]:
        raise ValueError("artifact or evidence digest mismatch")
    # Parse, reject duplicates and require source linkage in BOTH evidence records.
    for path in (provenance, release_manifest):
        doc = read_json(path)
        if not isinstance(doc, dict) or doc.get("source_commit") != expected_source:
            raise ValueError("evidence source commit mismatch")
    if not zipfile.is_zipfile(apk):
        raise ValueError("invalid APK ZIP")
    with zipfile.ZipFile(apk) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or "AndroidManifest.xml" not in names or "classes.dex" not in names:
            raise ValueError("invalid APK structure")
        if any(n.startswith("META-INF/") and n.upper().endswith((".RSA", ".DSA", ".EC", ".SF")) for n in names):
            raise ValueError("signed APK not permitted")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--release-manifest", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args(argv)
    try:
        verify(args.apk, args.record, args.provenance, args.release_manifest, args.source_commit)
    except (OSError, ValueError, TypeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"BLOCKED: {exc}; flash/release authorization=false", file=sys.stderr)
        return 1
    print("INTEGRITY ONLY: staged bytes match operator records; flash/release authorization=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
