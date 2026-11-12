# QA-STACK-028 — Replay ledger watermark integrity on restart

**Scope:** Host-side offline `DurableReplayLedger` only; stacked on draft PR #56 (`e07bf346aa70f2acfcf3dc3f52670843939181ce`). The target development branch is `feat/phase1-agentic-phone`, but this change must remain draft and unmerged pending independent approval.

## Reproduced baseline defects

At the parent SHA, a ledger with a successfully reserved nonce silently recreated a **deleted** `ledger_clock` row when reopened. It also accepted a backwards timestamp after `max_now` was lowered below a retained nonce timestamp. Both were reproduced using disposable SQLite databases, without any Android runtime or device action. This contradicted the prior documentation's missing-watermark fail-closed claim across restarts.

## Correction and acceptance

The initialization transaction now distinguishes creation of the `ledger_clock` table for a legacy database from reopening an existing table. It seeds only a genuinely missing table, never a missing row in an existing table. It checks that the watermark is a nonnegative SQLite integer and is not older than the newest retained nonce. Invalid state aborts initialization with a database error, leaving the ledger unavailable rather than silently repairing it. Three regression tests cover deleted-row restart, rollback below retained nonce, and negative/text watermark values.

**Limits:** The legacy-table migration remains intentionally supported. An attacker who can drop the entire table or rewrite both tables can evade these consistency checks; same-UID database tampering and filesystem races remain out of scope. Retained nonce timestamps cannot prove history that has already been pruned. A backwards wall clock can still cause fail-closed availability loss. This is not trusted monotonic time, cross-host replay protection, or a device anti-rollback guarantee.

**Evidence gates:** focused tests, full Python preflight, Python compilation, Android manifest and accessibility source checks, Git whitespace checks, a clean independent checkout, exact-head hosted CI, and separate human security/accessibility review. No physical Pixel, StrongBox, spoken TalkBack, OTA, signed release, or production execution is claimed. M1–M8 remain **0/8 independently accepted**. The local `PROJECT-ADAPTER.md` is present; upstream shared `SKILL.md` is unverified.
