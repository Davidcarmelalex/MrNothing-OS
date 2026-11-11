#!/usr/bin/env python3
"""QA-STACK-003: read-only-ref, disposable-object Git merge simulation.

Runs git merge-tree in a throwaway clone. It does not update refs, index, worktree,
or grant merge approval. merge-tree may write unreachable objects to the clone.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import pr_stack_gate as graph

SHA = re.compile(r"^[0-9a-f]{40}$")
MAX_PRS = 40
MAX_PATHS = 2000


class SimulationError(ValueError):
    pass


def git(repo, *args, accepted=(0,)):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        check=False,
        timeout=45,
    )
    if result.returncode not in accepted:
        raise SimulationError(f"git {args[0]} failed (exit {result.returncode})")
    return result


def ref_sha(repo, branch):
    graph.branch(branch)
    result = git(repo, "rev-parse", "--verify",
                 f"refs/remotes/origin/{branch}^{{commit}}")
    sha = result.stdout.decode("ascii", "strict").strip()
    if not SHA.fullmatch(sha):
        raise SimulationError("invalid remote-tracking SHA")
    return sha


def changed_paths(repo, start, end):
    data = git(repo, "diff", "--no-ext-diff", "--no-textconv",
               "--name-only", "-z", start, end).stdout
    paths = sorted({p.decode("utf-8", "surrogateescape")
                    for p in data.split(b"\0") if p})
    if len(paths) > MAX_PATHS:
        raise SimulationError("changed-path limit exceeded")
    return paths


def audit(repo, pulls, root_sha, selected, root=graph.ROOT):
    if not SHA.fullmatch(root_sha or ""):
        raise SimulationError("invalid root SHA")
    if ref_sha(repo, root) != root_sha:
        raise SimulationError("root ref changed since snapshot")
    if not isinstance(pulls, list) or len(pulls) > 100:
        raise SimulationError("invalid or oversized PR inventory")
    if not selected or len(selected) > MAX_PRS or len(set(selected)) != len(selected):
        raise SimulationError("invalid PR selection")
    by_number = {}
    for p in pulls:
        if not isinstance(p, dict) or type(p.get("number")) is not int:
            raise SimulationError("invalid PR entry")
        if p["number"] in by_number:
            raise SimulationError("duplicate PR number")
        by_number[p["number"]] = p
    results = []
    for number in sorted(selected):
        p = by_number.get(number)
        if p is None or p.get("state") != "open" or p.get("draft") is not True:
            raise SimulationError(f"PR #{number}: missing or not open draft")
        head = p.get("head")
        base = p.get("base")
        if not isinstance(head, dict) or not isinstance(base, dict):
            raise SimulationError(f"PR #{number}: missing head/base")
        branch = head.get("ref")
        expected = head.get("sha")
        if not isinstance(branch, str) or not isinstance(expected, str) or not SHA.fullmatch(expected):
            raise SimulationError(f"PR #{number}: invalid head")
        if base.get("ref") != root or branch == root:
            raise SimulationError(f"PR #{number}: unexpected parent")
        if ref_sha(repo, branch) != expected:
            raise SimulationError(f"PR #{number}: stale head SHA")
        merge_base = git(repo, "merge-base", root_sha, expected).stdout.decode("ascii").strip()
        if not SHA.fullmatch(merge_base):
            raise SimulationError(f"PR #{number}: missing common ancestor")
        already_ancestor = git(repo, "merge-base", "--is-ancestor", root_sha,
                               expected, accepted=(0, 1)).returncode == 0
        # --quiet suppresses output; status 1 means textual/tree conflict.
        # No checkout, ref updates, index changes, hooks or working tree mutation.
        simulation = git(repo, "merge-tree", "--write-tree", "--quiet",
                         root_sha, expected, accepted=(0, 1))
        pr_paths = changed_paths(repo, merge_base, expected)
        root_paths = changed_paths(repo, merge_base, root_sha)
        overlap = sorted(set(pr_paths) & set(root_paths))
        results.append({
            "number": number, "head": branch, "head_sha": expected,
            "merge_base": merge_base, "root_is_ancestor": already_ancestor,
            "merge_tree": "clean_simulation" if simulation.returncode == 0 else "conflict",
            "pr_paths": pr_paths, "overlap_with_root": overlap,
            "needs_human_review": True,
        })
    return {
        "schema": "mrnothing.pr-stack-merge-simulation.v1",
        "status": "blocked_conflicts" if any(x["merge_tree"] == "conflict" for x in results)
                  else "review_required_not_merge_approved",
        "root_sha": root_sha, "selected_count": len(results),
        "results": results,
        "limitations": [
            "Requires fresh remote-tracking refs and an exact PR snapshot",
            "merge-tree may create unreachable objects in the disposable clone",
            "Clean merge-tree does not prove semantic compatibility or CI correctness",
            "No refs, index, worktree, device, deployment or production changes",
            "No merge or rebase authorization; independent review remains mandatory",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--root-sha", required=True)
    parser.add_argument("--pr", type=int, action="append", required=True)
    args = parser.parse_args(argv)
    try:
        if args.input.stat().st_size > 2_000_000:
            raise SimulationError("snapshot exceeds 2MB")
        data = json.loads(args.input.read_text(encoding="utf-8"))
        pulls = data["pulls"] if isinstance(data, dict) else data
        report = audit(args.repo, pulls, args.root_sha, args.pr)
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["status"] == "blocked_conflicts" else 0


if __name__ == "__main__":
    sys.exit(main())
