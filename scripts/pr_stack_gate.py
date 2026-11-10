#!/usr/bin/env python3
"""QA-STACK-001: offline, read-only PR branch dependency audit (not merge approval)."""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = "feat/phase1-agentic-phone"
REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")
SHA = re.compile(r"^[0-9a-f]{40}$")


class AuditError(ValueError):
    pass


def branch(value):
    if not isinstance(value, str) or not REF.fullmatch(value) or ".." in value or "//" in value or value.endswith("/"):
        raise AuditError("invalid branch ref")
    return value


def audit(pulls, root=ROOT):
    """Check scoped open PR names form a rooted DAG; never infer Git ancestry."""
    root = branch(root)
    if not isinstance(pulls, list) or len(pulls) > 500:
        raise AuditError("expected at most 500 pull requests")
    numbers, heads = {}, {}
    for pr in pulls:
        if not isinstance(pr, dict):
            raise AuditError("PR must be object")
        if pr.get("state", "open") != "open":
            continue
        number = pr.get("number")
        if type(number) is not int or number <= 0:
            raise AuditError("invalid PR number")
        h, b = pr.get("head"), pr.get("base")
        if not isinstance(h, dict) or not isinstance(b, dict):
            raise AuditError("missing head/base object")
        head, base = branch(h.get("ref")), branch(b.get("ref"))
        if head == root or base == "main":
            continue  # phase-one umbrella and unrelated main-targeted PRs
        sha = h.get("sha")
        if not isinstance(sha, str) or not SHA.fullmatch(sha):
            raise AuditError(f"PR #{number}: missing valid exact head SHA")
        if number in numbers or head in heads:
            raise AuditError(f"duplicate PR number or head: #{number}")
        item = {"number": number, "head": head, "base": base, "sha": sha,
                "draft": pr.get("draft") is True}
        numbers[number] = item
        heads[head] = item
    state, depth, ordered = {}, {}, []

    def visit(item):
        n = item["number"]
        if state.get(n) == 1:
            raise AuditError(f"dependency cycle at PR #{n}")
        if state.get(n) == 2:
            return depth[n]
        state[n] = 1
        base = item["base"]
        if base == root:
            d = 1
        elif base in heads:
            d = visit(heads[base]) + 1
        else:
            raise AuditError(f"PR #{n}: unresolved parent branch {base}")
        state[n] = 2
        depth[n] = d
        ordered.append({**item, "depth": d})
        return d

    for n in sorted(numbers):
        visit(numbers[n])
    return {"schema": "mrnothing.pr-stack-audit.v1", "root": root,
            "status": "dependency_refs_valid_not_merge_approved",
            "pr_count": len(ordered),
            "draft_count": sum(x["draft"] for x in ordered),
            "direct_root_count": sum(x["depth"] == 1 for x in ordered),
            "max_depth": max(depth.values(), default=0),
            "parent_first": ordered,
            "limitations": ["No Git ancestry verification", "No CI or review verification",
                            "No automatic merge or deployment"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--root", default=ROOT)
    args = parser.parse_args(argv)
    try:
        if args.input.stat().st_size > 2_000_000:
            raise AuditError("input exceeds 2 MB")
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        report = audit(raw.get("pulls") if isinstance(raw, dict) else raw, args.root)
    except (AuditError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

