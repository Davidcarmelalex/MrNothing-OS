# Engineering roadmap addendum — AGENT-005R

**Audit head:** `d517b416ab59c5a75e4d68dc50399e75a3a4035b` on `feat/phase1-agentic-phone`.  
**Task:** fault-inject post-commit acknowledgement loss across both SQLite stores and terminal outcome persistence.

## Verified increment

Three real-SQLite proxy tests execute the first `COMMIT` and then raise a synthetic acknowledgement-loss error:

- Action-ledger `DISPATCH_STARTED` commit: durable state survives restart and cannot be claimed again.
- Enrollment lock commit after the ledger claim: the result is reported as uncertain while the ledger remains `DISPATCH_STARTED`.
- `UNKNOWN_OUTCOME` commit: the terminal state survives restart, repeated recording is idempotent, and dispatch remains terminal.

This is test-only hardening. No production implementation or Android code changed.

## Milestone status (unchanged)

| Milestone | Status | Remaining acceptance |
|---|---|---|
| M1 Foundation | IN PROGRESS | Independent review, full threat-model and release gates |
| M2 OS interface | IN PROGRESS | Genuine spoken TalkBack acceptance and independent UX review |
| M3 Agentic intelligence | PARTIAL | Independent security review; no integrated executor |
| M4 Permission-controlled integrations | NOT STARTED | Five opt-in workflows and revocation tests |
| M5 Pixel 9 Pro compatibility | NOT ACCEPTED | `caiman` hardware/ABI/boot-chain validation |
| M6 Security/privacy | IN PROGRESS | Independent review, production trust provenance and privacy gates |
| M7 Physical hardware | BLOCKED | Supervised physical Pixel 9 Pro validation |
| M8 Production readiness | BLOCKED | Signed reproducible release, OTA/rollback and M1–M7 acceptance |

No milestone is complete.

## Next task

Obtain an independent security review of SEC-021A/B/C and the trusted in-process callback boundary. Do not connect an executor until that review accepts the single-host assumptions, crash semantics, permission preflight and revocation ordering. If independent review is unavailable, keep the gate pending and continue only with isolated no-side-effect verification.


## Exact-head CI checkpoint — AGENT-005R

At corrected head `e94f87e903e8b5345eeb9b0b8f4bfea0712f39e0`, Phase 1 push/PR both passed with 765 Python tests each, Android unit/build/repeat-build and dependency-verification gates passed; CI-003 push/PR both passed with byte-identical unsigned APKs and matching runtime/scoped build-environment SBOMs. QA-005 for e94 remained queued behind an earlier emulator run at last inspection. The previous d517 head's 30/30 emulator result is baseline evidence only. Independent human security review remains pending; no milestone is complete.
