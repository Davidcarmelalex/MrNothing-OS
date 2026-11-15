"""Deterministic metadata for a debug APK. Not a signature or SLSA attestation."""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
import re


def build_record(apk: Path, commit: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("expected full lowercase Git commit SHA")
    # Bind the digest and recorded size to one opened inode. Do not follow a
    # symlink to an untrusted artifact, even if it changes during inspection.
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("no-follow artifact opening unsupported")
    try:
        descriptor = os.open(apk, flags | os.O_NOFOLLOW)
    except OSError as exc:
        raise ValueError("APK cannot be safely opened") from exc
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_size == 0:
        os.close(descriptor)
        raise ValueError("APK missing, empty or not regular")
    with os.fdopen(descriptor, "rb") as stream:
        digest = hashlib.sha256()
        total = 0
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            total += len(chunk)
        after = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
            before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size,
            after.st_mtime_ns, after.st_ctime_ns) or total != after.st_size:
            raise ValueError("APK changed while recording provenance")
    return {
        "artifact": apk.name,
        "artifact_sha256": digest.hexdigest(),
        "bytes": total,
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
