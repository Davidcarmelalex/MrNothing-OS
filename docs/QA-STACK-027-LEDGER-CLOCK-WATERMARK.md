# QA-STACK-027 — Durable replay-ledger clock rollback refusal

## Reproduction at exact parent
Parent: `6ff08037c452185dd06589dc095e8f01e8438b8f`.
Five new regressions failed on the parent: a decreasing wall-clock time was accepted by direct reservation and signed-command admission, and no durable clock watermark existed. Baseline focused suite: 54 tests, four assertion failures and one missing-table error.

## Bounded security change
The host-side SQLite replay ledger now persists an accepted-time high-water mark in a singleton `ledger_clock` table. The table and initial watermark are created transactionally, seeding from the latest retained legacy `seen_at` timestamp when upgrading an existing database. Each reservation acquires SQLite's immediate transaction, refuses `now < max_now` before nonce pruning, and updates the watermark atomically with a successful nonce insertion. Replayed/capacity-rejected commands roll back the watermark with the transaction. Missing/corrupted watermark state fails closed. The public admission API maps the SQLite refusal to `LEDGER_UNAVAILABLE`.

Tests cover rollback refusal before pruning, preservation of the rejected nonce, TTL-pruning/restart persistence, signed-command denial, migration from the legacy schema, and a deleted watermark row. No Android application code, permission, executor, CI workflow, release, or production service changes.

## Limits / required review
This prevents rollback below the last **successfully reserved** time in this one-host ledger, not clock manipulation before the first reservation, cross-host replay, tampering by a same-UID attacker with database write access, filesystem TOCTOU races, or device anti-rollback. A backward clock adjustment can deliberately halt command admission until the wall clock catches up; this is a fail-closed availability tradeoff. Legacy databases can seed only from timestamps still retained when upgraded; previously pruned history cannot be reconstructed. No network endpoint is enabled. This is not a replacement for a trusted monotonic clock, authenticated device-bound protocol, or independently reviewed distributed replay strategy.

## Acceptance gates
- Reproduce five failing regression tests before patch.
- Run focused admission suite, full Python preflight, compilation, manifest and accessibility source checks, Git whitespace check.
- Independently clone exact commit and re-execute tests.
- Hosted exact-head CI and independent human security/accessibility review remain required.
- No Pixel 9 Pro hardware, StrongBox, spoken TalkBack, signed release, OTA/recovery or production-readiness acceptance is implied.
- Local `PROJECT-ADAPTER.md` remains project-specific; upstream shared `SKILL.md` remains unverified.
- M1–M8 independently accepted: **0/8**.
