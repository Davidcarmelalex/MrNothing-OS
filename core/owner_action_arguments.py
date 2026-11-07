"""Strict, versioned action-argument canonicalization for owner-consent v2."""
from __future__ import annotations

import hashlib
import json
import re

_ARGUMENTS_DOMAIN = b"mrnothing-owner-action-arguments-v2\x00"
_PACKAGE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")
MAX_CANONICAL_ARGUMENT_BYTES = 1_024


def canonical_action_arguments(action: object, arguments: object) -> bytes:
    """Return deterministic ASCII JSON for one exact, bounded action schema."""
    if type(action) is not str or type(arguments) is not dict:
        raise ValueError("invalid action arguments")
    if action == "read_screen":
        if arguments:
            raise ValueError("read_screen accepts no arguments")
        normalized = {}
    elif action == "navigate":
        if set(arguments) != {"target_package"}:
            raise ValueError("navigate requires exactly target_package")
        target = arguments["target_package"]
        if type(target) is not str or not 1 <= len(target) <= 255 or _PACKAGE_RE.fullmatch(target) is None:
            raise ValueError("invalid target package")
        normalized = {"target_package": target}
    elif action == "scroll":
        if set(arguments) != {"direction", "distance_dp"}:
            raise ValueError("scroll requires exactly direction and distance_dp")
        direction = arguments["direction"]
        distance_dp = arguments["distance_dp"]
        if type(direction) is not str or direction not in {"up", "down"}:
            raise ValueError("invalid scroll direction")
        if type(distance_dp) is not int or not 1 <= distance_dp <= 1_000:
            raise ValueError("invalid scroll distance")
        normalized = {"direction": direction, "distance_dp": distance_dp}
    else:
        raise ValueError("unsupported action")
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
    if not 1 <= len(encoded) <= MAX_CANONICAL_ARGUMENT_BYTES:
        raise ValueError("canonical arguments exceed size limit")
    return encoded


def action_arguments_sha256(action: object, arguments: object) -> str:
    """Return the domain-separated SHA-256 digest signed by consent protocol v2."""
    canonical = canonical_action_arguments(action, arguments)
    return hashlib.sha256(_ARGUMENTS_DOMAIN + action.encode("ascii") + b"\x00" + canonical).hexdigest()
