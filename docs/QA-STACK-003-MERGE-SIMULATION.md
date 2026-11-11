# QA-STACK-003 — Disposable Git merge-conflict simulation

**Scope:** read-only integration preflight for open draft PRs targeting `feat/phase1-agentic-phone`. This extends QA-STACK-001 and QA-STACK-002; do not duplicate or bypass them. The upstream shared `SKILL.md` is absent/unverified; `PROJECT-ADAPTER.md` is the project-specific contract.

## Procedure

1. In a **fresh isolated clone**, fetch the exact root branch and selected PR head branches. Do not modify existing worktrees, production hosts or shared Git refs.
2. Snapshot current open PR metadata from GitHub, with number/state/draft/head.ref/head.sha/base.ref. Pin root SHA separately and verify the remote-tracking ref against it.
3. Run `python3 scripts/pr_stack_merge_simulator.py --repo /isolated/clone --input /isolated/open-prs.json --root-sha <40-hex> --pr 3 --pr 5 --pr 6 --pr 7`.
4. Exit 0 = clean simulated merges **requiring review**; exit 1 = actual merge-tree conflict; exit 2 = stale/missing snapshot or tool error, **blocked**.
5. For each result, compare changed paths, exact diffs, CI and dependency order. A clean simulation does not imply safe merge, semantic compatibility, tests passing, or security approval.
6. Keep all existing PRs draft; no rebase, merge, push, flashing, root escalation, Android permission grant or production deployment.

Git `merge-tree --write-tree --quiet` may write unreachable objects inside the disposable clone, but does not change branch refs, index or working tree. Never run this on a shared clone if other workers are active.

**Release gates:** independent human reviewer, reproducible Android builds, security/privacy acceptance, real Pixel 9 Pro hardware validation, and signed release/OTA recovery remain pending. No milestone is accepted by this preflight.

## Observed isolated-clone audit — 2026-11-10

Pinned authorized root `f42af837bcb8eed478cadbc472b7571441449a7a`. Snapshot of PRs #3/#5/#6/#7 checked against fetched remote-tracking head refs. The simulation exited **1 (blocked conflicts)**:

| PR | Three-way merge-tree | Shared paths with current root | Integration action |
| --- | --- | --- | --- |
| #3 | clean | 0 | Review stale ancestry and Kotlin regression semantics |
| #5 | clean | 0 | Review provenance design; no trust anchor approval |
| #6 | clean | 2 (`.github/workflows/phase1-checks.yml`, `requirements-security-ci.txt`) | Review workflow/dependency semantics before integration |
| #7 | **content conflict** | 3 | Resolve `tests/test_owner_consent_protocol.py` in a **new isolated integration candidate**, retain both test intents |

All four heads diverge from the current root; a clean simulated merge is **not** an endorsement to rebase or merge. No existing branch or shared worktree was modified. 971 Python preflight tests passed in the candidate checkout, including 9 new synthetic regression tests; manifest and launcher source checks passed. Hosted Android CI, physical Pixel testing and independent human approval remain separate gates.
