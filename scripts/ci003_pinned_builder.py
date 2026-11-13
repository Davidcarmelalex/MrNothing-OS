#!/usr/bin/env python3
"""Candidate-only OCI image pin syntax and workflow binding check; no attestation."""
import argparse
import json
from pathlib import Path
import re
import sys

PIN = re.compile(r"^[a-z0-9][a-z0-9.-]*(?::[0-9]{1,5})?/[a-z0-9_.-]+(?:/[a-z0-9_.-]+)*@sha256:([0-9a-f]{64})$")


def pinned_image(image):
    if not isinstance(image, str) or len(image) > 512:
        raise ValueError("image must be a bounded string")
    match = PIN.fullmatch(image)
    if not match or match.group(1) == "0" * 64:
        raise ValueError("image must use registry/repository@sha256:<64 lowercase hex>")
    return image


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def policy_image(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4096:
        raise ValueError("policy must be a small regular file")
    obj = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(obj, dict) or set(obj) != {"schema_version", "platform", "image"}:
        raise ValueError("invalid policy keys")
    if type(obj["schema_version"]) is not int or obj["schema_version"] != 1:
        raise ValueError("unsupported policy schema")
    if obj["platform"] != "linux/amd64":
        raise ValueError("unsupported platform")
    return pinned_image(obj["image"])


def workflow_image(text):
    job = None
    build_count = 0
    images = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.fullmatch(r"  [a-zA-Z][a-zA-Z0-9_-]*:", line):
            job = line.strip()[:-1]
            if job == "build":
                build_count += 1
        if job != "build":
            continue
        if line.startswith("    container:"):
            if line != "    container:" or i + 1 >= len(lines):
                raise ValueError("ambiguous container")
            image_line = lines[i + 1]
            if not re.fullmatch(r"      image: [^\s#]+", image_line):
                raise ValueError("container requires a literal image")
            images.append(image_line.split(": ", 1)[1])
    if build_count != 1 or len(images) != 1:
        raise ValueError("no unique pinned build container")
    return pinned_image(images[0])


def validate(policy, workflow):
    expected = policy_image(policy)
    if workflow.is_symlink() or not workflow.is_file() or workflow.stat().st_size > 65536:
        raise ValueError("workflow must be a bounded regular file")
    actual = workflow_image(workflow.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError("candidate image differs from workflow")
    return "PIN_SYNTAX_VALID_NOT_ATTESTED"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-policy", type=Path, required=True)
    parser.add_argument("--workflow", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(validate(args.candidate_policy, args.workflow))
        return 0
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print("PIN_PREFLIGHT_REJECTED: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
