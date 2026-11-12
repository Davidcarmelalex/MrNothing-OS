# QA-STACK-035 — Exact-head Android emulator and reproducibility gate

**Parent:** QA-STACK-034 draft PR #63 at `6808143dcda30e8ee3817e0fe78a4d34bd0cfb87`.
**Scope:** test/CI-only, no Android application, permission, executor, network, firmware or signing change.

## Problem

The latest stacked security fixes have exact-head Phase 1 Python/JVM evidence, but no new hosted emulator or independent-runner reproducibility proof. Both existing workflows have intentionally narrow manual-dispatch allowlists; they would skip a run dispatched on this candidate branch.

## Bounded solution

Allow manual `workflow_dispatch` for the exact QA-STACK-035 branch in both CI-003 build/verifier jobs and QA-005 emulator job, bound to the owned GitHub repository. Preserve existing automatic trigger guards, read-only workflow permissions, noncancelling concurrency, pinned checkout SHA and the no-production-release boundary. Add static regression tests.

## Acceptance gates

1. New static tests and the full Python suite pass on the exact candidate SHA in an independent checkout.
2. CI-003 hosted build matrix and verifier pass, with byte-identical unsigned release APKs and provenance bound to the exact SHA.
3. QA-005 hosted emulator passes with actual instrumentation and recovery/accessibility evidence. Spoken TalkBack is a separate hardware/service gate.
4. Independent human security/accessibility approval remains **PENDING**. Neither a passing emulator nor reproducibility proves Pixel 9 Pro, StrongBox, signed OTA or production readiness.

Do not claim gates 2–3 until their GitHub workflow jobs and artifacts are inspected. No merge to main or production deployment is authorized.
