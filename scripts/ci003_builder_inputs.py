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
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "builder/toolchain-candidate.lock.json"
NAMES = {
    "commandlinetools-linux-16111833_latest.zip",
    "gradle-8.9-bin.zip",
}
SHA = re.compile(r"^[0-9a-f]{64}$")


def _open_input_archive(path):
    """Open a single no-follow descriptor, never a second pathname lookup."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("safe file opening unsupported")
    try:
        return os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK |
                       getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise ValueError("cannot safely open input archive") from exc


def _verify_open_sha256(fd, expected, maximum):
    """Hash an already-open bounded regular inode; return its initial stat."""
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        raise ValueError("invalid expected SHA-256")
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
    if _file_identity(before) != _file_identity(after):
        raise ValueError("archive changed during hashing")
    if digest.hexdigest() != expected:
        raise ValueError("input SHA-256 mismatch")
    return before


def _file_identity(st):
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns


def verify_regular_sha256(path, expected, maximum=250_000_000):
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        raise ValueError("invalid expected SHA-256")
    fd = _open_input_archive(path)
    try:
        return _verify_open_sha256(fd, expected, maximum).st_size
    finally:
        os.close(fd)


def verify_zip_archive(path, expected, prefix, maximum=250_000_000):
    """Hash and inspect ZIP metadata through one inode-bound descriptor.

    The caller must still secure subsequent Docker COPY inputs: this does not
    bind a later build-context pathname read to the verified inode.
    """
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        raise ValueError("invalid expected SHA-256")
    fd = _open_input_archive(path)
    try:
        before = _verify_open_sha256(fd, expected, maximum)
        os.lseek(fd, 0, os.SEEK_SET)
        # dup retains the opened inode even if the directory entry is replaced.
        with os.fdopen(os.dup(fd), "rb") as archive_file:
            members, expanded = validate_zip_members(archive_file, prefix)
        if _file_identity(before) != _file_identity(os.fstat(fd)):
            raise ValueError("archive changed during ZIP inspection")
        return before.st_size, members, expanded
    finally:
        os.close(fd)


def validate_zip_members(path, prefix, *, max_members=100_000, max_expanded=4_000_000_000):
    """Fail-closed metadata preflight for archives the Dockerfile will unpack.

    This does not extract files, attest archive origin, or replace the SHA-256
    check. All limits are deliberately independent of archive-supplied totals.
    """
    if not isinstance(prefix, str) or not prefix.endswith("/") or "/" in prefix[:-1]:
        raise ValueError("invalid archive root prefix")
    seen = set()
    files = set()
    total = 0
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if not members or len(members) > max_members:
                raise ValueError("invalid ZIP member count")
            for member in members:
                name = member.filename
                if (not name.startswith(prefix) or "\\" in name or
                        "\x00" in name or name.startswith("/") or
                        any(part in ("", ".", "..") for part in name.rstrip("/").split("/"))):
                    raise ValueError("unsafe ZIP member path")
                canonical = name.rstrip("/")
                if canonical in seen:
                    raise ValueError("duplicate ZIP member path")
                seen.add(canonical)
                parts = canonical.split("/")
                if any("/".join(parts[:n]) in files for n in range(1, len(parts))):
                    raise ValueError("ZIP member nested under a file")
                if member.flag_bits & 1:
                    raise ValueError("encrypted ZIP member")
                mode = member.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if kind not in (0, stat.S_IFDIR if member.is_dir() else stat.S_IFREG):
                    raise ValueError("ZIP special file or symlink")
                if member.is_dir():
                    if member.file_size:
                        raise ValueError("ZIP directory contains data")
                else:
                    if canonical == prefix[:-1]:
                        raise ValueError("ZIP root must be a directory")
                    files.add(canonical)
                    if any(other.startswith(canonical + "/") for other in seen):
                        raise ValueError("ZIP file shadows directory")
                    if member.file_size < 0 or member.file_size > max_expanded:
                        raise ValueError("ZIP member exceeds expansion limit")
                    total += member.file_size
                    if total > max_expanded:
                        raise ValueError("ZIP expanded data exceeds limit")
                    if member.file_size > 0 and member.compress_size == 0:
                        raise ValueError("ZIP member has invalid compressed size")
                    if member.compress_size and member.file_size > member.compress_size * 1000:
                        raise ValueError("ZIP member exceeds compression ratio limit")
    except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError) as exc:
        raise ValueError("invalid ZIP archive") from exc
    return len(seen), total


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
            prefix = "cmdline-tools/" if name.startswith("commandlinetools-") else "gradle-8.9/"
            size, members, expanded = verify_zip_archive(args.directory / name, digest, prefix)
            print(f"{name}: verified {size} bytes, {members} ZIP members, {expanded} expanded bytes")
        print("CANDIDATE_INPUTS_VERIFIED_NOT_ATTESTED")
        return 0
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print("CANDIDATE_INPUTS_REJECTED: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
