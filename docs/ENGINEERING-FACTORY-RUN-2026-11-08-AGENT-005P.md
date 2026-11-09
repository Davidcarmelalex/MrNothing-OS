# Engineering Factory Run — AGENT-005P

**Date:** 2026-11-08  
**Repository:** Davidcarmelalex/MrNothing-OS  
**Authorized branch:** feat/phase1-agentic-phone  
**Starting head:** 0814acbba4c8c4fcab3f99467dea66e5ec5545af  
**Task:** require live final-admission revalidation for every durable dispatch claim.

## Audit

- Complete recursive tree: 361 entries; not truncated.
- Latest 20 commits inspected.
- Branch is 309 commits ahead of main and zero behind (main: f3c9a701d2a337de8ef393ac14df044a79843d60).
- Six open PRs (#1, #3–#7). PR #1 is the only PR using this branch; it targets main and remains draft. It has no submitted reviews or inline review threads. PRs #3–#7 were left untouched.
- PROJECT-ADAPTER.md and docs/ENGINEERING-FACTORY-ROADMAP.md exist. Repository SKILL.md is absent. Upstream shared package remains unverified and is not claimed installed.
- Rulesets endpoint returned an empty list. Branch-protection read was unavailable; required-review enforcement is not established.

## Starting-head verification

- Phase 1 push [42437648599](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42437648599) and PR [42437652145](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42437652145): success. PR Python-policy job ran 759 tests; all passed. Android manifest gate, Gradle unit tests, debug assembly, repeat-build comparison, strict dependency verification and modified-artifact negative control passed.
- CI-003 push [42437648584](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42437648584) and PR [42437652163](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42437652163): success. Independent runners produced byte-identical unsigned release APKs (7,867,868 bytes; SHA-256 c7036c64e3a49ea9d8642c29082c42537e2c8ba0863d43d3cbd4fbb098603da7; normalized-entry SHA-256 37b7e6846eaa4f58f143f430cb84aa481e4858c0cde392a7f2526cd8b89b9462). Runtime SBOM and scoped build-environment inventory/SBOM matched. Verifier reports reproducible=true, release_ready=false.
- QA-005 PR [42437652152](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42437652152): success on disposable Android API 35 x86_64 emulator. Launcher/recovery, large-text, HOME consent/cancel, stock-launcher restoration, keyboard navigation, insecure enrollment denial, owner-authority UI cancellation and credential-only prompt smoke passed. QA-011 reported blocked_service_disabled; QA-012 was structural only; spoken TalkBack was not tested. Evidence artifact [13599883659](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42437652152/artifacts/13599883659).
- No local tests, local Gradle build, physical device, Pixel 9 Pro, StrongBox or production release were tested/claimed in this run.

## Finding

DurableActionReservationLedger.claim_dispatch accepted an omitted/None final_admission_guard and defaulted the guard result to True. Thus any in-process caller with an active enrollment record could move a reservation to DISPATCH_STARTED without demonstrating that it had revalidated the adapter-retained live TLS socket/session and one-use capability. The only current production-style caller supplied a guard, but the storage API did not enforce the contract at all call sites.

## Implementation

- Make final_admission_guard a required keyword-only argument with no default.
- Reject explicit None/non-callable guards.
- Invoke the guard unconditionally under both database writer locks.
- Accept only exact Boolean True; false, truthy non-Boolean and exceptions fail closed.
- Add regression tests for omitted guard, explicit None and non-Boolean result.
- Update storage-only test helpers and enrollment/dispatch ordering tests to pass an explicit test-only lambda returning True.
- Update the durable reservation contract, project adapter and roadmap.

**Trust limitation:** a callback is still trusted in-process code. The ledger cannot authenticate arbitrary callbacks or protect against hostile code already running in the host process. Only the reviewed adapter may call this API; the callback must never be supplied by agent/model/request data.

## Safety

No Android source, manifest, permission, service, listener, dispatcher, shell bridge or executor changed. No device action, installation, permission grant, root operation, physical flash or deployment occurred. CommandRouter remains fail-closed.

## Verification plan

Exact-head GitHub Actions must pass after the commit: Phase 1 push/PR (Python suite, Android manifest gate, Gradle unit/build, dependency negative control), CI-003 independent-runner unsigned reproducibility, and QA-005 disposable-emulator smoke. This run did not execute tests locally because a local checkout/build environment was unavailable.

## Review and milestones

Author-side diff review only; independent human security review remains PENDING. M1 foundation, M2 OS interface and M6 security/privacy remain IN PROGRESS; M3 remains PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED pending physical Pixel 9 Pro evidence; M8 BLOCKED. No milestone is complete.

**Next task:** independent security review of the mandatory final-admission boundary and its callback trust assumptions, followed by a no-op Android admission integration only after approval. Keep the executor disconnected.


## Verification correction — invalid-guard response assertion

The first exact-head Phase 1 push run (42438951780) ran 761 tests and found one test-only assertion mismatch. The implementation correctly rejects an explicit non-callable guard before reading the reservation row, so the returned decision has state null; the durable row itself remains RESERVED. The test incorrectly expected the decision's state field to contain RESERVED. The assertion now checks a null decision state and separately reads the ledger to prove the row remains RESERVED. No implementation change was needed. The failed run is retained in Actions history; the corrected head must pass a fresh exact-head run.
