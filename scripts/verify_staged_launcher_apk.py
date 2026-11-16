#!/usr/bin/env python3
"""ROM-003 offline, fail-closed staged unsigned launcher APK integrity gate.

This checks operator-supplied claims and bytes, NOT independent builder identity,
source-to-binary reproducibility, signatures, licensing, or release authorization.
"""
import argparse
import errno
from contextlib import ExitStack
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
MAX_ZIP_ENTRIES = 4096
MAX_ZIP_NAME_BYTES = 4096
REQUIRED = {"schema", "source_commit", "apk_sha256", "apk_kind", "build_variant",
            "unsigned", "provenance_sha256", "release_manifest_sha256"}


def object_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_json(handle):
    handle.seek(0)
    return json.load(handle, object_pairs_hook=object_no_duplicates)


def open_regular_file(path):
    """Bind all later validation to one opened inode; never follow the leaf symlink."""
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("no-follow file opening unsupported")
    try:
        fd = os.open(path, flags | os.O_NOFOLLOW)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ValueError("symlink forbidden") from exc
        raise
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise ValueError("not a private regular file")
        return os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise


def digest_handle(handle):
    h = hashlib.sha256()
    handle.seek(0)
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()


def digest(path):
    with open_regular_file(path) as handle:
        return digest_handle(handle)


def reject_apk_signing_block(f):
    """Reject APK v2/v3 signing blocks; unsigned staging only, not cryptographic verification."""
    f.seek(0, os.SEEK_END)
    length = f.tell()
    f.seek(max(0, length - 65557))
    tail = f.read()
    i = tail.rfind(bytes.fromhex("504b0506"))
    if i < 0 or len(tail) - i < 22:
        raise ValueError("missing ZIP end-of-central-directory")
    eocd = tail[i:]
    if len(eocd) != 22 + int.from_bytes(eocd[20:22], "little"):
        raise ValueError("invalid ZIP end-of-central-directory")
    offset = int.from_bytes(eocd[16:20], "little")
    size = int.from_bytes(eocd[12:16], "little")
    if offset == 0xffffffff or size == 0xffffffff or offset + size != length - len(eocd):
        raise ValueError("unsupported ZIP central directory")
    if offset < 24:
        return
    f.seek(offset - 24)
    footer = f.read(24)
    if footer[8:] != b"APK Sig Block 42":
        return
    block_size = int.from_bytes(footer[:8], "little")
    if block_size < 24 or block_size > offset - 8:
        raise ValueError("malformed APK signing block")
    f.seek(offset - block_size - 8)
    if int.from_bytes(f.read(8), "little") != block_size:
        raise ValueError("malformed APK signing block header")
    raise ValueError("APK v2/v3 signing block forbidden")

def reject_unsafe_raw_zip_names(handle):
    """Inspect central-directory filename bytes before zipfile can truncate NULs."""
    handle.seek(0, os.SEEK_END)
    length = handle.tell()
    handle.seek(max(0, length - 65557))
    tail = handle.read()
    end = tail.rfind(b"PK\\x05\\x06")
    if end < 0 or len(tail) - end < 22:
        raise ValueError("invalid ZIP central directory")
    eocd = tail[end:]
    if len(eocd) != 22 + int.from_bytes(eocd[20:22], "little"):
        raise ValueError("invalid ZIP central directory")
    count = int.from_bytes(eocd[10:12], "little")
    size = int.from_bytes(eocd[12:16], "little")
    offset = int.from_bytes(eocd[16:20], "little")
    if (count == 0xffff or size == 0xffffffff or offset == 0xffffffff or
            count > MAX_ZIP_ENTRIES or offset + size != length - len(eocd)):
        raise ValueError("unsupported ZIP central directory")
    handle.seek(offset)
    consumed = 0
    for _ in range(count):
        header = handle.read(46)
        if len(header) != 46 or header[:4] != b"PK\\x01\\x02":
            raise ValueError("invalid ZIP central directory")
        name_len = int.from_bytes(header[28:30], "little")
        extra_len = int.from_bytes(header[30:32], "little")
        comment_len = int.from_bytes(header[32:34], "little")
        consumed += 46 + name_len + extra_len + comment_len
        if name_len > MAX_ZIP_NAME_BYTES or consumed > size:
            raise ValueError("ZIP entry limits exceeded")
        name = handle.read(name_len)
        if len(name) != name_len or b"\\x00" in name:
            raise ValueError("unsafe raw APK ZIP entry")
        handle.seek(extra_len + comment_len, os.SEEK_CUR)
    if consumed != size:
        raise ValueError("invalid ZIP central directory")


def verify(apk, record, provenance, release_manifest, expected_source):
    with ExitStack() as stack:
        apk_file, record_file, provenance_file, manifest_file = (
            stack.enter_context(open_regular_file(p))
            for p in (apk, record, provenance, release_manifest)
        )
        r = read_json(record_file)
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
        if (digest_handle(apk_file) != r["apk_sha256"] or
                digest_handle(provenance_file) != r["provenance_sha256"] or
                digest_handle(manifest_file) != r["release_manifest_sha256"]):
            raise ValueError("artifact or evidence digest mismatch")
        for handle in (provenance_file, manifest_file):
            doc = read_json(handle)
            if not isinstance(doc, dict) or doc.get("source_commit") != expected_source:
                raise ValueError("evidence source commit mismatch")
        apk_file.seek(0)
        if not zipfile.is_zipfile(apk_file):
            raise ValueError("invalid APK ZIP")
        reject_apk_signing_block(apk_file)
        reject_unsafe_raw_zip_names(apk_file)
        apk_file.seek(0)
        with zipfile.ZipFile(apk_file) as z:
            entries = z.infolist()
            if len(entries) > MAX_ZIP_ENTRIES or any(len(e.filename.encode("utf-8")) > MAX_ZIP_NAME_BYTES for e in entries):
                raise ValueError("APK ZIP entry limits exceeded")
            # Fail closed on ambiguous, unsafe or encrypted ZIP metadata. APK
            # entries are never extracted here, but downstream tooling may be.
            if any(e.flag_bits & 1 or e.filename.startswith(("/", "\\")) or
                   "\\" in e.filename or "\x00" in e.filename or
                   any(part in ("", ".", "..") for part in e.filename.rstrip("/").split("/"))
                   for e in entries):
                raise ValueError("unsafe APK ZIP entry")
            names = [e.filename for e in entries]
            if len(names) != len(set(names)) or "AndroidManifest.xml" not in names or "classes.dex" not in names:
                raise ValueError("invalid APK structure")
            if any(n.startswith("META-INF/") and n.upper().endswith((".RSA", ".DSA", ".EC", ".SF")) for n in names):
                raise ValueError("signed APK not permitted")
        # Detect in-place changes made while parsing pinned files. Descriptor binding
        # prevents path substitution, but not writes to the same inode.
        for handle, expected in ((apk_file, r["apk_sha256"]),
                                 (provenance_file, r["provenance_sha256"]),
                                 (manifest_file, r["release_manifest_sha256"])):
            if digest_handle(handle) != expected:
                raise ValueError("input mutated during verification")
        # The record itself is not independently authenticated; ensure its
        # contents did not change after the initial parse.
        if read_json(record_file) != r:
            raise ValueError("record mutated during verification")
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

