# QA-STACK-008 — isolated UX rehearsal + MemoryVault integration candidate

**Scope:** `Davidcarmelalex/MrNothing-OS`, authorized development root `feat/phase1-agentic-phone`. **Draft only; not approved for merge, runtime enrollment, device execution or production.**

## Pinned inputs and semantic reconciliation

- MemoryVault/security stack: draft PR #33 at `68295f8db9a39284170cafb6d134854497004679`, including PR #32's atomic crash-marker test-harness repair.
- UX rehearsal stack: draft PR #49 at `9cbb96166ced776b37920a11b05ea292b4bbcfcf`.
- Development root: `f42af837bcb8eed478cadbc472b7571441449a7a`; neither source PR nor this integration candidate modifies it.
- Read-only `git merge-tree --write-tree` reported **two content conflicts**: `android/app/build.gradle.kts` and `tests/test_qa005_workflow_gate.py`. Both were resolved by retaining the union of explicitly enumerated instrumentation tests: seven security/owner tests plus the UX `AgentPlanPreviewActivityTest` = **eight**. The test inventory still compares against actual `InstrumentationTestCase` declarations and rejects duplicates/missing classes.
- The remaining 37 paths from the UX stack were auto-merged. In particular, the merged manifest keeps MemoryVault **disabled/non-exported** and the offline preview **non-exported**; no executor or permission-grant path is connected.
- The existing QA-005 emulator and CI-003 independent unsigned-build jobs are extended **only** to this exact same-repository, development-target integration PR branch. Existing branch allowlists, timeouts, SHA-pinned checkout, read-only workflow permissions and cleanup guards remain.

## Test and evidence contract

The integration candidate must pass (1) full Python preflight, (2) Android manifest source security and launcher accessibility source gates, (3) hosted exact-head Gradle JVM and **121 required MemoryVault security methods** from JUnit XML, (4) QA-005 emulator with the combined UX/owner/vault instrumentation inventory, and (5) CI-003 two-runner byte-identical **unsigned** debug APK comparison. Do not infer any of these from separate parent-PR runs. The emulator is not a Pixel 9 Pro; structural accessibility is not spoken TalkBack testing.

**Pre-commit local verification on the isolated merge tree:** `bash scripts/phase1-preflight.sh` **1127/1127 Python tests passed**; focused QA-005 gate **38/38**, UX source **10/10**, consent protocol **26/26**; manifest source gate, Python compilation and staged whitespace checks passed. Three cross-stack boundary regression tests also passed. These are not independent human signoff and do not prove hosted CI.

## Independent review and remaining blockers

Independent non-author security/Android/UX approval is **PENDING**. Review the combined diff, both resolved conflicts, no-op supervisor isolation, preview cancellation on lifecycle changes, memory/consent fail-closed behavior, emulator artifacts, reproducibility evidence, and the full 121-method JUnit XML inventory. MemoryVault signer provenance, durable anti-rollback, physical Pixel StrongBox, spoken TalkBack, signed OTA/recovery and release signing remain unproven. No milestone M1–M8 is independently accepted. The shared upstream `SKILL.md` remains unverified; the project-specific `PROJECT-ADAPTER.md` is not a substitute for an installed upstream skill.

**Safety:** no root, flashing, hardware access, permissions, key provisioning, release, main/dev merge, or production deployment. All draft source PRs remain intact and unmerged. This integration candidate is a review and CI target, not authorization to execute agents.

## QA-STACK-008 executed-UX-evidence hardening — 2026-11-13

The initial exact-head integration run passed the Android emulator job and reported 39 executed instrumentation cases, but the existing XML evidence parser required only the two disabled-MemoryVault manifest methods. A green emulator job alone did not independently enforce execution of the three UX rehearsal lifecycle/mode-isolation instrumentation methods. This gap is now addressed with an **opt-in, exact-branch-bound** raw XML gate that requires all three named methods, with no duplicates, failures, errors or skips. Missing, spoofed, duplicated, skipped or failed UX cases are negative controls. Existing non-integration PRs retain the prior two-method MemoryVault gate.

The change touches only the QA workflow, its XML evidence verifier and Python tests. It does not alter the Android app, consent, executor, MemoryVault or runtime permissions. Pre-push isolated preflight: 1,134 Python tests passed; 24 focused evidence tests, 39 QA workflow tests, compilation, source manifest, launcher source gate and whitespace passed. **Exact-head hosted CI and emulator execution must be rechecked after push**; earlier green runs do not certify the new commit. This remains a draft, review-only integration candidate. Independent non-author review, physical Pixel, spoken TalkBack, StrongBox and signed OTA/recovery remain pending.
