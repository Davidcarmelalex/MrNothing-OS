#!/usr/bin/env python3
"""Candidate-only OCI image pin syntax and workflow binding check; no attestation."""
import argparse
import json
from pathlib import Path
import re
import sys

PIN = re.compile(r"^([^/@]+)/(.*)@sha256:([0-9a-f]{64})$")
# Conservative OCI/Docker repository component grammar: no empty or dot-only
# segments, no leading/trailing separators, and no mutable tag before digest.
REGISTRY_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
REPOSITORY_PART = re.compile(r"^[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*$")


def pinned_image(image):
    if not isinstance(image, str) or len(image) > 512:
        raise ValueError("image must be a bounded string")
    match = PIN.fullmatch(image)
    if not match or match.group(3) == "0" * 64:
        raise ValueError("image must use registry/repository@sha256:<64 lowercase hex>")
    registry, repository, _digest = match.groups()
    if registry.count(":") > 1:
        raise ValueError("unsupported registry authority")
    hostname, separator, port = registry.partition(":")
    if separator and (not port.isascii() or not port.isdigit() or
                      len(port) > 5 or port.startswith("0") or
                      not 1 <= int(port) <= 65535):
        raise ValueError("invalid registry port")
    if len(hostname) > 253 or not all(REGISTRY_LABEL.fullmatch(label)
                                      for label in hostname.split(".")):
        raise ValueError("invalid registry hostname")
    if not repository or any(not REPOSITORY_PART.fullmatch(part)
                             for part in repository.split("/")):
        raise ValueError("invalid repository component")
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
    """Parse only a conservative literal jobs.build.container.image YAML subset.

    This is intentionally not a general YAML parser or an attestation verifier.
    Reject duplicate/ambiguous security-sensitive keys instead of guessing which
    mapping entry GitHub Actions would ultimately evaluate.
    """
    if not isinstance(text, str) or len(text) > 65536:
        raise ValueError("workflow must be bounded text")
    jobs_count = build_count = container_count = 0
    in_jobs = in_build = in_container = False
    images = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = line[:len(line) - len(line.lstrip(" \t"))]
        if "\t" in indent:
            raise ValueError("ambiguous YAML tab indentation")
        if not line.startswith(" "):
            in_build = in_container = False
            if re.match(r"""^(?:jobs|["']jobs["'])\s*:""", line):
                jobs_count += 1
                if line != "jobs:":
                    raise ValueError("ambiguous jobs mapping")
                in_jobs = True
            else:
                in_jobs = False
            continue
        if in_jobs and line.startswith("  ") and not line.startswith("   "):
            if not re.fullmatch(r"  [a-zA-Z][a-zA-Z0-9_-]*:", line):
                raise ValueError("ambiguous jobs mapping")
            in_container = False
            key = line[2:-1]
            if key == "build":
                build_count += 1
                in_build = True
            else:
                in_build = False
            continue
        if in_build and line.startswith("    ") and not line.startswith("     "):
            if not re.match(r"^    [a-zA-Z][a-zA-Z0-9_-]*\s*:", line):
                raise ValueError("ambiguous build job field")
            key = line.strip().split(":", 1)[0].strip()
            if key == "container":
                if line != "    container:":
                    raise ValueError("ambiguous container")
                container_count += 1
                in_container = True
            else:
                in_container = False
            continue
        if in_container and line.startswith("      ") and not line.startswith("       "):
            if not re.fullmatch(r"      image: [^\s#]+", line):
                raise ValueError("unsupported or ambiguous container field")
            images.append(line.split(": ", 1)[1])
    if jobs_count != 1 or build_count != 1 or container_count != 1 or len(images) != 1:
        raise ValueError("no unique pinned build container under jobs")
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
