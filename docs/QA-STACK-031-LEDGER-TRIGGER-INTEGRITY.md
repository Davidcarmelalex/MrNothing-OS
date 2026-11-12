# QA-STACK-031 — Replay ledger schema-trigger integrity

**Scope:** host-side Python `DurableReplayLedger` only; no Android executor, permission, transport, production service, firmware or release changes. Base: QA-STACK-030 (`bdce6c5836248be59f85bfeb4cde8268e0e77d95`), stacked ultimately on `feat/phase1-agentic-phone`.

## Reproduced failure before correction

An external SQLite connection could install an `AFTER INSERT ON seen` trigger that deleted the newly reserved nonce. The existing ledger returned `True` for both the first reservation and the replay of the **same device/command ID**, while retaining zero nonce rows. An `AFTER UPDATE ON ledger_clock` trigger could also silently reset the clock watermark. Three regression tests failed against the unchanged base commit.

## Bounded correction and acceptance

A dedicated replay ledger has no legitimate application-defined SQLite triggers. Reject any persisted trigger in `sqlite_master` under `BEGIN IMMEDIATE`, both when opening/migrating the ledger and on every reservation. This write transaction prevents concurrent SQLite schema changes between the check and reservation. Unexpected triggers raise `sqlite3.DatabaseError`; signed admission maps SQLite errors to `LEDGER_UNAVAILABLE`. No trigger is removed or automatically repaired. Existing non-trigger legacy schema migration remains unchanged.

Regression gates: reject nonce-erasing trigger without admitting or reserving; reject trigger-bearing database on reopen; reject clock-resetting trigger before updating watermark. Existing normal replay, migration, concurrency, and filesystem permission tests must remain green. Full Python suite and static checks are required; exact-head hosted Android/JVM CI and independent human review remain separate gates.

## Explicit limitations

This is **not** a defense against an attacker with the same OS user privileges who can edit the database directly, remove triggers between operations, rewrite both watermark and nonce rows, or race filesystem pathnames. Cross-host replay, trusted monotonic anti-rollback, power-loss durability, Android/Pixel 9 Pro StrongBox, spoken TalkBack, signed releases, OTA/recovery, and production readiness remain unverified. Unexpected legitimate legacy triggers now fail closed and require manual review/migration. No milestone M1–M8 is independently accepted.

The project-specific `PROJECT-ADAPTER.md` applies. The upstream shared `SKILL.md` package remains unverified; it was not installed.
