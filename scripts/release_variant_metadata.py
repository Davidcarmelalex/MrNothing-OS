#!/usr/bin/env python3
"""Strict reader for the single Gradle-derived Android release variant identity."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SCHEMA = "mrnothing-gradle-release-variant-v1"
APPLICATION_ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+")


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("release variant metadata contains a duplicate JSON key")
        result[key] = value
    return result


def load_release_variant_metadata(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Gradle release variant metadata is missing, not a regular file, or a symlink")
    if path.stat().st_size > 16 * 1024:
        raise ValueError("Gradle release variant metadata exceeds the 16 KiB safety limit")
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Gradle release variant metadata is unavailable or invalid JSON") from exc
    if type(data) is not dict:
        raise ValueError("Gradle release variant metadata must be a JSON object")
    if set(data) != {"schema", "applicationId", "variantName", "buildType"}:
        raise ValueError("Gradle release variant metadata has missing or unknown fields")
    if data["schema"] != SCHEMA:
        raise ValueError("Gradle release variant metadata schema is unsupported")
    application_id = data["applicationId"]
    variant_name = data["variantName"]
    build_type = data["buildType"]
    if type(application_id) is not str or not APPLICATION_ID_RE.fullmatch(application_id):
        raise ValueError("Gradle release variant applicationId is invalid")
    if type(variant_name) is not str or variant_name != "release":
        raise ValueError("Gradle release variant name must be release")
    if type(build_type) is not str or build_type != "release":
        raise ValueError("Gradle release variant buildType must be release")
    return {
        "application_id": application_id,
        "variant_name": variant_name,
        "build_type": build_type,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
