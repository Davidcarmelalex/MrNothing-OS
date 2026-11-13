# QA-STACK-004 — Safe consent timestamp contract port

**Scope:** `feat/phase1-agentic-phone`, based on the exact authorized development branch. This is a narrowly scoped, non-authorizing integration alternative to divergent draft PR #7.

## Why this is a new candidate, not a merge of PR #7

PR #7's current head is based on a much older repository tree. A three-way `git merge-tree` against the current development head reports a conflict in `tests/test_owner_consent_protocol.py`. A direct PR-head-to-root diff would also delete many newer security, Android, QA and engineering-factory files. Do **not** merge, rebase or force-push PR #7 automatically.

This candidate preserves the current development tree and ports only the relevant signed-64-bit epoch-millisecond constraint. The Python verifier now rejects timestamps beyond Kotlin's `Long.MAX_VALUE` while retaining the 30-second TTL, strict integer typing, P-256 signature verification, enrollment and replay controls. Regression tests exercise both v1 and v2 challenges and the maximum representable expiry; a Kotlin JVM test covers the corresponding boundary.

## Verification and gates

Run targeted Python tests, full Python preflight, Android source gates and exact-head hosted Gradle/JUnit CI. A local test result does not imply hosted Android or physical Pixel testing. This change grants no permission, executes no device action and does not connect the agent executor.

Keep this PR draft pending independent security review and hosted CI. Treat PR #7 as requiring separate maintainer reconciliation; do not close it or change its branch without approval. The local `PROJECT-ADAPTER.md` remains the project-specific contract; upstream `SKILL.md` is absent and unverified.
