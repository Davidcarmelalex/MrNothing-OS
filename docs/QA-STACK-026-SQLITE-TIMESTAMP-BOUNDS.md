# QA-STACK-026 — SQLite replay-ledger timestamp fail-closed bounds

## Evidence-driven defect
On the QA-STACK-025 integration head `e1764b5513d75838100a644bb7b802d0a47aaec9`, a correctly signed command with `issued_at = now = 2**63` reached `sqlite3` with a value outside SQLite's signed 64-bit INTEGER range. The admission call raised an uncaught `OverflowError: Python int too large to convert to SQLite INTEGER`, rather than returning a refusal. A negative timestamp could also be admitted. This is a host-side prototype input-validation defect, not an Android device exploit.

## Bounded correction
- Require integer Unix timestamps in `[0, 2**63 - 1]` before signature verification or replay reservation. Reject booleans and other types.
- Make direct replay-ledger reservation reject invalid timestamps with a `sqlite3.DataError`, which the admission layer handles as a fail-closed storage error.
- Reject ledger TTL settings that cannot fit the SQLite INTEGER range.
- Add three focused regression methods covering the formerly uncaught overflow, negative timestamps, direct reservation, and oversized TTL.
- Preserve existing ledger schema, file protections, replay semantics, signed-command protocol, Android code and CI workflows.

## Execution and acceptance
Baseline reproduction: `UNHANDLED_EXCEPTION OverflowError Python int too large to convert to SQLite INTEGER` at `2**63`.
Implementation checkout: focused command-admission tests **49/49 PASS**; full Phase 1 Python preflight **1188/1188 PASS**; Python compilation, Android manifest source security, launcher accessibility source gate and `git diff --check` PASS.

No Android emulator, physical Pixel, StrongBox, TalkBack speech, signed release, OTA, or production endpoint was tested for this change. Hosted exact-head CI and independent human security/accessibility approval remain pending until separately verified. The legacy HMAC admission prototype still relies on host wall-clock time and TTL-based replay pruning; clock rollback and cross-host replay are **not** solved by this patch. The separate atomic owner-consent enrollment registry is not modified.

**Integration:** scoped draft PR stacked on PR #54, ultimately targeting only `feat/phase1-agentic-phone`. Do not merge to the development branch or main without exact-head CI and independent review. No executor or permission grant is enabled. M1–M8 independently accepted: 0/8. Local `PROJECT-ADAPTER.md` exists; upstream shared `SKILL.md` remains unverified.
