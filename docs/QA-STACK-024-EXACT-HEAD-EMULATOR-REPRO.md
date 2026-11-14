# QA-STACK-024 — exact-head CI provenance in emulator and independent reproducibility

**Scope:** Stacked on QA-STACK-023, for the `feat/phase1-agentic-phone` development program only. No modification of Android runtime, device permissions, CI trigger allowlists, concurrency policy, production release signing, or protected branches.

## Failure mode and correction

An explicit `actions/checkout` ref selects the requested PR head, but a successful job should additionally prove that the checked-out Git commit equals the event head before building, running an emulator, or downloading/comparing artifacts. The Phase 1 jobs already have this assertion (QA-STACK-023); QA-005 and both CI-003 jobs previously did not. This change adds the same fail-closed assertion to all three jobs and three Python source-regression tests, including negative controls for substituted commit refs and missing assertions.

## Acceptance boundaries

- Source checks and local Python tests are not emulator execution, independent runner execution, Pixel 9 Pro hardware validation, signed release validation or independent human approval.
- CI-003 and QA-005 intentionally retain their narrow event/branch gates. This scoped stacked PR does not automatically run either expensive workflow. Any future run must be checked at its exact commit and with its actual artifacts.
- An exact Git SHA proves source selection only; it does not establish supply-chain trust in the runner, artifact provenance by itself, Android consent behavior, or production readiness.
- Upstream shared `SKILL.md` remains unverified; repository `PROJECT-ADAPTER.md` is a project-specific adapter.
- M1–M8 remain without independent acceptance. No production deployment, root escalation, device flashing or protected-branch merge is authorized.
