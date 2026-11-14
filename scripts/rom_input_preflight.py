"""Offline ROM source-input integrity preflight; never a build/release approval.

Input paths are relative to the explicitly supplied staging root. No network,
device commands, extraction, signing or writes are performed.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

KINDS = frozenset({"platform_manifest", "device_manifest", "kernel_manifest",
                   "vendor", "firmware", "toolchain"})


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def staged_file(root, name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("invalid staged path")
    parts = PurePosixPath(name)
    if parts.is_absolute() or any(p in {".", ".."} or ":" in p for p in name.split("/")) or "//" in name:
        raise ValueError("unsafe staged path")
    path = root
    for part in parts.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("symlink staged path")
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError("missing staged file")
    return path


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def check(data, root):
    """Validate an inventory, not its truth, compatibility or legal sufficiency.

    Staging must be private and quiescent: concurrent mutation is outside this
    offline check's threat model. Review references are hashed local records,
    never booleans that purport to grant legal or release approval.
    """
    root = Path(root).resolve(strict=True)
    if not isinstance(data, dict) or set(data) != {"schema", "device", "inputs"}:
        raise ValueError("invalid inventory fields")
    if data["schema"] != "mrnothing-rom-inputs-v1" or data["device"] != "caiman":
        raise ValueError("unsupported schema or device")
    items = data["inputs"]
    if not isinstance(items, list) or len(items) != len(KINDS):
        raise ValueError("all six ROM input kinds required")
    seen = set()
    for item in items:
        fields = {"kind", "path", "sha256", "review_path", "review_sha256"}
        if not isinstance(item, dict) or set(item) != fields:
            raise ValueError("invalid input fields")
        kind = item["kind"]
        if not isinstance(kind, str) or kind not in KINDS or kind in seen:
            raise ValueError("duplicate or unknown input kind")
        seen.add(kind)
        if item["path"] == item["review_path"]:
            raise ValueError("input cannot review itself")
        for path_key, hash_key in (("path", "sha256"), ("review_path", "review_sha256")):
            expected = item[hash_key]
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                raise ValueError("missing canonical SHA-256")
            path = staged_file(root, item[path_key])
            if path.stat().st_size == 0 or digest(path) != expected:
                raise ValueError("empty or mismatched staged file")
    return {"schema": "mrnothing-rom-input-preflight-v1", "device": "caiman",
            "input_integrity_passed": True, "compatibility_verified": False,
            "license_approval_verified": False, "bootable_rom_verified": False,
            "release_ready": False, "flash_authorized": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--staging-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.inventory.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        result = check(data, args.staging_root)
    except (ValueError, OSError, TypeError):
        print(json.dumps({"input_integrity_passed": False, "release_ready": False,
                          "flash_authorized": False, "reason": "INVALID_OR_MISSING_ROM_INPUTS"}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
