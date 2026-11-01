"""Deterministic metadata for a debug APK. Not a signature or SLSA attestation."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def build_record(apk: Path, commit: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("expected full lowercase Git commit SHA")
    if not apk.is_file() or apk.stat().st_size == 0:
        raise ValueError("APK missing or empty")
    digest = hashlib.sha256()
    with apk.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "artifact": apk.name,
        "artifact_sha256": digest.hexdigest(),
        "bytes": apk.stat().st_size,
        "source_commit": commit,
        "gradle_version": "8.9",
        "android_compile_sdk": 35,
        "build_variant": "debug",
        "release_ready": False,
        "provenance_signed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    record = build_record(args.apk, args.commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Recorded debug APK SHA-256:", record["artifact_sha256"])


if __name__ == "__main__":
    main()
