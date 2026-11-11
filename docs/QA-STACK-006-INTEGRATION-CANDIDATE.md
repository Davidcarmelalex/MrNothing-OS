# QA-STACK-006 — UX-AGENT + integration QA candidate

**Status: DRAFT / NOT MERGED / NO INDEPENDENT HUMAN APPROVAL.**

This candidate combines two existing, independently authored draft stacks on a scoped branch targeting `feat/phase1-agentic-phone`, without changing that branch or `main`:

- UX-AGENT-001–005, culminating in PR #43 at `d16d3e31f72492ec792411ea449e779ef941e80c` (offline, display-only rehearsal and deny-only supervisor).
- QA-STACK-001–003, culminating in PR #36 at `fd1556bc0534c3a05317701f837f44f09d0d4257` (read-only PR graph, Git ancestry and disposable merge simulation).

The pinned development baseline is `f42af837bcb8eed478cadbc472b7571441449a7a`. The two candidate parent commits were combined with `git merge-tree --write-tree` in a fresh isolated clone. The simulation returned exit 0 and tree `6999e0eb853713b269f41d957edf31aa3e18f90d`. No content conflict was reported. The two-parent integration commit was created **only on this scoped candidate**, not on the development branch. The candidate also removes three pre-existing trailing blank lines in the QA-STACK-001 files so the scoped diff passes `git diff --check`.

## Local verification at the pre-cleanup combined tree

- Full Python unittest discovery: **984/984 passed** on Python 3.14.4.
- Focused QA-STACK tests: **33/33 passed**.
- `scripts/android_manifest_gate.py`: passed (source-only).
- `scripts/launcher_accessibility_gate.py`: passed (source-only).
- `python3 -m compileall -q core tests scripts`: passed.
- `git diff --check` initially flagged three trailing blank lines; this candidate corrects those, requiring a fresh post-fix check.

The original PR #36 hosted workflow failed in an enrollment crash-marker race; the UX-AGENT chain includes the independently tested atomic-marker fix from PR #38. This combined candidate needs **its own exact-head hosted Python and Android CI**, not inference from parent CI. Its merge simulation does not establish semantic compatibility or authorize any merge.

## Security and acceptance

No new device action, executor, transport, Android permission, root, installation, flashing, release signing, OTA, or production deployment is added. All preview and supervisor outcomes remain non-authorizing. The `PROJECT-ADAPTER.md` is project-specific; no upstream shared `SKILL.md` has been verified or installed. Physical Pixel 9 Pro, real TalkBack speech, hardware StrongBox, production signing, and independent human security/UX review remain unverified. M1/M2/M6 are in progress; M3 partial; M4/M5 not accepted; M7/M8 blocked. **No M1–M8 milestone is accepted.**

Do not merge this draft or close predecessor PRs until exact-head CI, semantic/security review, and a deliberate integration decision are recorded. No production or device operation is authorized by this document.
