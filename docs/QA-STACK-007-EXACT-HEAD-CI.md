# QA-STACK-007 — bounded exact-head CI candidate

Source: issue #45, built on draft PR #44 at `afccd926c38fc3b6a5713e09f677213e74946f80`.
Target remains `feat/phase1-agentic-phone`. This branch is an **unmerged draft**.

The existing CI-003 independent unsigned-release builder and QA-005 disposable emulator
are made eligible for one explicit PR head:
`feat/qa-stack007-exact-head-ci-20261111`, when it targets the development branch
and originates in `Davidcarmelalex/MrNothing-OS`. Other development-target PRs
are job-skipped; existing main-target and development-push behavior is preserved.
Both workflows use the PR's immutable head SHA for checkout. Concurrency retains
active jobs; each job remains time-bounded, and the emulator PIN cleanup remains.

**Caveat:** GitHub may create skipped workflow runs for unrelated development PRs,
but no expensive builder/emulator job should be scheduled by these conditions.
CI-003 compares two independent hosted runners, not cryptographic release signing.
QA-005 uses a disposable x86_64 Android emulator, not a physical Pixel 9 Pro.
The emulator's structural accessibility checks are not spoken TalkBack acceptance.
These claims require actual exact-head hosted run IDs and artifacts.

The upstream shared SKILL.md remains unverified; the local PROJECT-ADAPTER.md
and engineering roadmap are the current project-specific factory contract.
Independent human security, accessibility and semantic review is **PENDING**.
No M1–M8 milestone is accepted. No permission, executor, root, OTA, device
flash, release signature or production deployment is introduced.
