#!/usr/bin/env python3
"""QA-STACK-002: read-only exact-ref ancestry and sibling change-overlap audit."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import pr_stack_gate as graph

SHA = re.compile(r"^[0-9a-f]{40}$")


class AncestryError(ValueError):
    pass


def git(repo, *args, accepted=(0,)):
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=False
    )
    if proc.returncode not in accepted:
        raise AncestryError(f"git {args[0]} failed (exit {proc.returncode})")
    return proc


def remote_sha(repo, branch):
    graph.branch(branch)
    ref = f"refs/remotes/origin/{branch}^{{commit}}"
    result = git(repo, "rev-parse", "--verify", ref)
    value = result.stdout.decode("ascii", "strict").strip()
    if not SHA.fullmatch(value):
        raise AncestryError(f"invalid remote SHA for {branch}")
    return value


def audit(repo, pulls, root_sha, root=graph.ROOT):
    if not isinstance(root_sha, str) or not SHA.fullmatch(root_sha):
        raise AncestryError("invalid pinned root SHA")
    inventory = graph.audit(pulls, root)
    if remote_sha(repo, root) != root_sha:
        raise AncestryError("root remote ref changed since snapshot")
    heads = {p["head"]: p for p in inventory["parent_first"]}
    rows = []
    for item in inventory["parent_first"]:
        head, base = item["head"], item["base"]
        if remote_sha(repo, head) != item["sha"]:
            raise AncestryError(f"PR #{item['number']}: stale head ref")
        parent_sha = root_sha if base == root else heads[base]["sha"]
        ancestor = git(repo, "merge-base", "--is-ancestor", parent_sha,
                       item["sha"], accepted=(0, 1))
        if ancestor.returncode != 0:
            raise AncestryError(f"PR #{item['number']}: parent is not ancestor")
        raw = git(repo, "diff", "--no-ext-diff", "--no-textconv",
                  "--name-only", "-z", parent_sha, item["sha"]).stdout
        files = sorted({p.decode("utf-8", "surrogateescape")
                        for p in raw.split(b"\0") if p})
        if len(files) > 10000:
            raise AncestryError("excessive changed paths")
        rows.append({"number": item["number"], "head": head, "base": base,
                     "head_sha": item["sha"], "parent_sha": parent_sha,
                     "depth": item["depth"], "incremental_files": files})
    overlaps = []
    for i, left in enumerate(rows):
        for right in rows[i + 1:]:
            if left["base"] != right["base"]:
                continue
            common = sorted(set(left["incremental_files"]) &
                            set(right["incremental_files"]))
            if common:
                overlaps.append({"pr_a": left["number"], "pr_b": right["number"],
                                 "paths": common})
    return {"schema": "mrnothing.pr-stack-ancestry.v1",
            "status": "review_required" if overlaps else
                      "ancestry_verified_not_merge_approved",
            "root": root, "root_sha": root_sha,
            "pr_count": len(rows), "max_depth": inventory["max_depth"],
            "sibling_overlap_pairs": len(overlaps), "overlaps": overlaps,
            "parent_first": rows,
            "limitations": ["Local remote-tracking refs must be freshly fetched",
                            "Git ancestry is not mergeability or review approval",
                            "Changed paths do not detect semantic conflicts",
                            "Renames use Git's reported destination path",
                            "No merge, deployment or device operation"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--root-sha", required=True)
    parser.add_argument("--root", default=graph.ROOT)
    args = parser.parse_args(argv)
    try:
        if args.input.stat().st_size > 2_000_000:
            raise AncestryError("input exceeds 2 MB")
        data = json.loads(args.input.read_text(encoding="utf-8"))
        pulls = data.get("pulls") if isinstance(data, dict) else data
        report = audit(args.repo, pulls, args.root_sha, args.root)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}),
              file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
