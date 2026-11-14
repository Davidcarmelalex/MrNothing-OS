# QA-STACK-029 — In-process replay clock integrity

Scope: host-side DurableReplayLedger prototype only, stacked on QA-STACK-028. No Android executor or network exposure.

## Reproduced before correction

An initialized ledger accepted a signed command after another SQLite connection lowered the persisted clock below a retained nonce. Negative clocks passed direct reservation, and noninteger clocks returned a different error. Three new tests failed in four subcases before the correction.

## Correction

Every reservation now checks that the clock is a bounded nonnegative SQLite integer and no less than the maximum retained nonce timestamp, inside the existing BEGIN IMMEDIATE transaction. Corruption rolls back and signed admission returns LEDGER_UNAVAILABLE. The existing seen_age index supports MAX(seen_at). No schema migration.

## Boundaries

This detects clock corruption only while a retained nonce supplies a consistency witness. It does not stop a same-UID attacker who rewrites both tables, cross-host replay, filesystem TOCTOU, rollback after all nonces are pruned, or wall-clock rollback availability issues. Not hardware-backed anti-rollback or Android command authorization.

Independent human security/accessibility review and exact-head hosted CI remain pending. Upstream shared SKILL.md unverified; PROJECT-ADAPTER.md is project-specific.
