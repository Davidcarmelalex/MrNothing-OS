#!/usr/bin/env python3
"""Verify exact offline inputs for unapproved CI-003J OCI candidate; no build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "builder/toolchain-candidate.lock.json"
NAMES = {
    "commandlinetools-linux-16111833_latest.zip",
    "gradle-8.9-bin.zip",
}
SHA = re.compile(r"^[0-9a-f]{64}$")


def verify_regular_sha256(path, expected, maximum=250_000_000):
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        raise ValueError("invalid expected SHA-256")
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("safe file opening unsupported")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise ValueError("cannot safely open input archive") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum:
            raise ValueError("input must be a bounded nonempty regular file")
        digest = hashlib.sha256()
        total = 0
        while True:
            data = os.read(fd, 1024 * 1024)
            if not data:
                break
            total += len(data)
            if total > maximum:
                raise ValueError("input exceeded maximum while hashing")
            digest.update(data)
        after = os.fstat(fd)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("archive changed during hashing")
        if digest.hexdigest() != expected:
            raise ValueError("input SHA-256 mismatch")
        return before.st_size
    finally:
        os.close(fd)


def check_lock(lock):
    if not isinstance(lock, dict) or set(lock) != {"schema_version", "platform", "status", "python_base", "jdk_base", "archives"}:
        raise ValueError("invalid candidate lock schema")
    if type(lock["schema_version"]) is not int or lock["schema_version"] != 1 or lock["platform"] != "linux/amd64" or lock["status"] != "UNAPPROVED_CANDIDATE":
        raise ValueError("unexpected candidate status or platform")
    if set(lock["archives"]) != NAMES or any(not isinstance(x, str) or not SHA.fullmatch(x) for x in lock["archives"].values()):
        raise ValueError("invalid archive manifest")
    for name in ("python_base", "jdk_base"):
        ref = lock[name]
        if not isinstance(ref, str) or not re.fullmatch(r"docker\.io/library/[a-z0-9-]+@sha256:[0-9a-f]{64}", ref):
            raise ValueError("base must be a digest-pinned Docker Hub image")
    return lock


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    try:
        lock = check_lock(json.loads(LOCK.read_text(encoding="utf-8")))
        for name, digest in sorted(lock["archives"].items()):
            size = verify_regular_sha256(args.directory / name, digest)
            print(f"{name}: verified {size} bytes")
        print("CANDIDATE_INPUTS_VERIFIED_NOT_ATTESTED")
        return 0
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print("CANDIDATE_INPUTS_REJECTED: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
