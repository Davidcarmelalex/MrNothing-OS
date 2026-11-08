# Engineering Factory Run AGENT-005Q

**Date:** 2026-11-08  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Starting commit:** `103ebdd61849bdfde14ec4919d58acd4e2e9035d`  
**Task:** Prove that the mandatory final-admission callback runs while both SQLite writer locks are held.

## Audit

- Complete recursive tree: 362 entries; not truncated.
- Latest 20 branch commits inspected.
- Branch comparison: 311 commits ahead of `main`, zero behind.
- Six open PRs inspected: #1 and #3–#7. PR #1 alone uses the authorized branch; it is open/draft, targets `main`, and has no submitted reviews or inline review threads.
- Branch listing reports `protected=false`.
- `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` exist.
- Repository `SKILL.md` is absent. The upstream shared engineering-factory package remains unverified and is not claimed installed.
- Other PR branches were not modified.

## Starting-head verification

- Phase 1 push [42439006024](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42439006024) and PR [42439010276](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42439010276): both passed; each Python-policy job ran 761 tests. Android unit/build, repeat debug APK comparison, strict dependency verification, modified-dependency negative control and source-manifest gate passed.
- CI-003 push [42439006083](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42439006083) and PR [42439010052](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42439010052): both passed. Independent runners produced byte-identical unsigned APKs, 7,867,868 bytes, SHA-256 `c7036c64e3a49ea9d8642c29082c42537e2c8ba0863d43d3cbd4fbb098603da7`. Provenance reports `release_ready=false`.
- QA-005 [42439010136](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42439010136): 30/30 instrumentation tests passed on a disposable Android 15/API 35 x86_64 emulator. QA-005–QA-010, QA-013 and QA-020B2/B3 passed. QA-011 remains service-disabled preflight only; QA-012 is structural semantics only, not spoken TalkBack acceptance.

## Implementation

Added `test_final_admission_guard_runs_under_both_database_writer_locks` to `tests/test_owner_enrollment_registry.py`.

The guard starts two competing operations using separate SQLite connections:
1. A signed owner/device revocation.
2. A pre-dispatch reservation cancellation.

Both must remain blocked while the guard runs. Once the guard returns and the claim commits, cancellation must fail against `DISPATCH_STARTED`, while revocation commits only afterward. This closes a test-coverage gap: the existing lock test held the enrollment lock before claim, but did not prove the callback itself executes while both database writer locks are held.

Updated SEC-021B, the project adapter and roadmap with the new regression.

## Acceptance status

The new exact-head push/PR Python, Android, CI-003 and QA-005 workflows are triggered by the commit. **They are pending at commit creation; no test pass is claimed in this record.** This test-only change does not connect or enable any executor or Android device action.

## Boundaries

- The lock-coupling guarantee remains single-host/single-database-pair, not distributed.
- The final guard remains trusted in-process code; it must never be provided by model/request input.
- No production Android code, manifest permission, service, listener, executor, signing key, OTA or device state was changed.
- No physical Pixel 9 Pro test, spoken TalkBack acceptance, signed release or production readiness is claimed.
- Independent human security review remains pending.
- No merge to `main` occurred.

## Milestones

M1 foundation: in progress. M2 OS interface: in progress. M3 agentic intelligence: partial. M4 integrations: not started. M5 Pixel 9 Pro: not accepted. M6 security/privacy: in progress. M7 physical hardware: blocked. M8 production readiness: blocked. No milestone is complete.
