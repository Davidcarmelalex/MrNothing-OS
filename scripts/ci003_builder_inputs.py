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


def parse_candidate_lock(raw):
    """Refuse ambiguous JSON keys, including duplicate nested archive names."""
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate candidate lock key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique_pairs)


def check_candidate_recipe(lock, recipe):
    """Bind the offline candidate's high-risk Dockerfile declarations to its lock.

    This is a syntax/declaration check, NOT an OCI attestation or Docker build.
    """
    if not isinstance(recipe, str) or len(recipe.encode('utf-8')) > 65536:
        raise ValueError("invalid candidate Dockerfile size")
    lines = [line.strip() for line in recipe.splitlines()]
    declarations = lambda word: [line for line in lines if re.match(r'^' + word + r'(?:\s+|$)', line, re.IGNORECASE)]
    expected_from = [
        'FROM --platform=linux/amd64 ' + lock['jdk_base'] + ' AS jdk',
        'FROM --platform=linux/amd64 ' + lock['python_base'] + ' AS candidate',
    ]
    if declarations('FROM') != expected_from:
        raise ValueError("candidate Dockerfile base image mismatch")
    expected_copies = [
        'COPY --from=jdk /opt/java/openjdk /opt/java/openjdk',
        'COPY builder/inputs/commandlinetools-linux-16111833_latest.zip /tmp/commandlinetools.zip',
        'COPY builder/inputs/gradle-8.9-bin.zip /tmp/gradle.zip',
    ]
    if declarations('COPY') != expected_copies:
        raise ValueError("candidate Dockerfile COPY scope mismatch")
    archives = lock['archives']
    checksum = (
        "RUN printf '%s  %s\\n' "
        + "'" + archives['commandlinetools-linux-16111833_latest.zip'] + "' /tmp/commandlinetools.zip "
        + "'" + archives['gradle-8.9-bin.zip'] + "' /tmp/gradle.zip | sha256sum --check --strict"
    )
    expected_runs = [
        checksum,
        "RUN python3 - <<'PY'",
        'RUN python3 --version && java -version && /opt/gradle/gradle-8.9/bin/gradle --version',
        'RUN groupadd -g 10001 builder && useradd --create-home -u 10001 -g 10001 builder',
        'RUN mkdir -p /workspace && chown 10001:10001 /workspace',
    ]
    if declarations('RUN') != expected_runs:
        raise ValueError("candidate Dockerfile RUN declarations mismatch")
    if declarations('USER') != ['USER 10001:10001'] or declarations('WORKDIR') != ['WORKDIR /workspace']:
        raise ValueError("candidate Dockerfile non-root runtime mismatch")
    for forbidden in ('ADD', 'ARG', 'ONBUILD', 'ENTRYPOINT', 'CMD', 'SHELL', 'VOLUME', 'EXPOSE'):
        if declarations(forbidden):
            raise ValueError("candidate Dockerfile unexpected instruction: " + forbidden)
    # Declaration checks alone cannot see a modified Dockerfile heredoc body,
    # extra ENV, or other syntax the strict subset does not recognize.
    # The exact recipe bytes are therefore locked as a separate invariant.
    if hashlib.sha256(recipe.encode("utf-8")).hexdigest() != lock["recipe_sha256"]:
        raise ValueError("candidate Dockerfile recipe SHA-256 mismatch")
    return True


def check_lock(lock):
    if not isinstance(lock, dict) or set(lock) != {"schema_version", "platform", "status", "python_base", "jdk_base", "archives", "recipe_sha256"}:
        raise ValueError("invalid candidate lock schema")
    if type(lock["schema_version"]) is not int or lock["schema_version"] != 1 or lock["platform"] != "linux/amd64" or lock["status"] != "UNAPPROVED_CANDIDATE":
        raise ValueError("unexpected candidate status or platform")
    if not isinstance(lock["recipe_sha256"], str) or not SHA.fullmatch(lock["recipe_sha256"]):
        raise ValueError("invalid candidate Dockerfile recipe SHA-256")
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
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        check_candidate_recipe(lock, (LOCK.parent / "Dockerfile.candidate").read_bytes().decode("utf-8"))
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
