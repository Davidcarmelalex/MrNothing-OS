# QA-STACK-002 — Git ancestry and incremental overlap preflight

This **read-only** offline gate extends QA-STACK-001's branch-name dependency graph with exact Git commit ancestry and sibling-path overlap checks. It must never authorize a merge.

1. Fetch all open PRs from the GitHub REST API, including pagination, into a complete JSON array (same format as QA-STACK-001). Record the exact root branch SHA.
2. Use a fresh isolated clone and fetch every scoped PR head into its corresponding `refs/remotes/origin/<head>` remote-tracking ref, plus the root branch. Do not use an existing working tree with concurrent writers.
3. Run `python3 scripts/pr_stack_ancestry_gate.py --input open-pulls.json --repo /path/to/clone --root-sha <40-hex-root-sha>`.
4. Treat nonzero exit as BLOCKED. Review every sibling overlap, source diff, CI status, human review, permission change, and merge-order consequence separately. Even a zero exit means **not merge-approved**.

The script checks exact snapshot SHA against local remote refs, verifies each immediate parent is a Git ancestor, computes incremental `git diff --name-only` paths, and reports overlapping paths among siblings. It refuses missing or stale refs, diverged ancestry, malformed snapshots and invalid root SHA. It executes Git via argv (no shell), makes no network calls, and never writes Git refs or the checkout.

**Limitations:** File-path overlap is not a semantic conflict detector. Non-overlapping changes can still conflict; renames and generated artifacts need manual review. It does not verify CI, approvals, signing, Android builds, devices, production readiness, or independently protected signer enrollment. It is a dependency preflight only. `PROJECT-ADAPTER.md` is project-specific; upstream `SKILL.md` remains absent/unverified.

No root escalation, firmware flashing, app installation, agent execution, production deployment or merge is permitted by this gate.
