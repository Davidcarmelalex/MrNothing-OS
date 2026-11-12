# Engineering Factory Roadmap Addendum — AGENT-005T

Branch: feat/phase1-agentic-phone  
Baseline: 360ef619930bcb6b662a024e82b58e9aea72d4de  
Increment: test-only process-death recovery at the cross-store commit boundary.

## Measurable milestone status

| Milestone | Status | Evidence / remaining gate |
|---|---|---|
| M1 — Foundation | IN PROGRESS | Consent, enrollment, durable admission, process-death tests and CI foundations exist; independent review and complete release gates remain. |
| M2 — OS interface | IN PROGRESS | Exact-head emulator launcher/recovery checks pass; spoken TalkBack acceptance remains open. |
| M3 — Agentic intelligence | PARTIAL | HERMES planning/policy and no-op simulation exist; real executor remains disconnected. |
| M4 — Permission-controlled integrations | NOT STARTED | Action-specific preflight exists; no accepted real device integration. |
| M5 — Pixel 9 Pro compatibility | NOT ACCEPTED | Emulator evidence only; no physical caiman validation. |
| M6 — Security/privacy | IN PROGRESS | SEC-021A/B/C, cross-process claim and post-commit process-death coverage; independent human security approval pending. |
| M7 — Physical hardware validation | BLOCKED | Requires supervised physical Pixel 9 Pro, StrongBox and recovery validation. |
| M8 — Production readiness | BLOCKED | Requires signed reproducible release, OTA/rollback, full security review and all prior gates. |

No milestone is complete.

## AGENT-005T acceptance

The exact-head Phase 1 Python push and PR suites must include the new process-death regression and pass. Android build/unit tests, CI-003 independent-runner reproducibility and QA-005 emulator evidence must be inspected for the exact head. The new regression proves only same-host process recovery after the ledger COMMIT and before enrollment-lock release; it is not a power-loss or distributed transaction guarantee.

## Next task

Independent security review of SEC-021A/B/C, with explicit challenge of lock ordering, callback trust, process death between commits, lost commit acknowledgements, duplicate claims and the no-retry rule. Do not connect the real executor before that gate is accepted.
