# QA-STACK-008 — UX rehearsal × MemoryVault integration candidate

**Scope:** disposable draft branch feat/qa-stack008-ux-memoryvault-combined-20261111; parent 1 security tip PR #33 1561ac15d5e370411283b80d3275c87f306e4b43, parent 2 UX tip PR #49 9cbb96166ced776b37920a11b05ea292b4bbcfcf. The authorized development root remains f42af837bcb8eed478cadbc472b7571441449a7a. Do not merge into that root or main without separate approval.

## Conflict resolution

The isolated Git merge produced exactly two textual conflict files. In android/app/build.gradle.kts, retain both MemoryVaultManifestBoundaryTest and AgentPlanPreviewActivityTest in the explicit legacy instrumentation runner allowlist (eight unique tests total). In tests/test_qa005_workflow_gate.py, update the exact-count assertion from the independently correct but now obsolete 7/6 to 8; retain the source-discovery equality and uniqueness gates.

The auto-merged Android manifest retains the disabled, non-exported MemoryVault service and the non-exported preview activity. The auto-merged emulator workflow retains QA-UX-008 instrumentation, 200% text and keyboard/recovery smoke checks, with power-state restoration. CI-003 and QA-005 allow the single named combined PR against the authorized development branch to obtain exact-head evidence; existing narrow candidates and main-target checks remain unchanged. No broad automatic emulator fan-out.

## Fail-closed acceptance

- Security: MemoryVault remains dormant, non-exported and disabled; no key creation, permission grants, executor or network transport is introduced.
- AI/UX: rehearsal remains simulation-only and supervisor denies execution; mode switches cancel active rehearsal; cancellation, accessibility and launcher recovery require runtime checks.
- CI/QA: full Python preflight, manifest/accessibility gates, Android/JVM, exact-head emulator instrumentation and CI-003 independent-runner release reproducibility on this combined SHA. Inspect JUnit XML and artifacts; earlier isolated PR runs do not count.
- Independent verifier: semantic security/UX review and explicit human sign-off required; spoken TalkBack, Pixel 9 Pro physical device, StrongBox hardware and signed OTA/recovery remain unverified.
- Shared upstream factory SKILL.md remains unverified; the local PROJECT-ADAPTER.md is not proof of installation.

**Do not claim M1–M8 acceptance or production readiness from a green CI result.**
