# QA-STACK-036 — PR #64 / PR #67 integration candidate

Review-only, not accepted for production. Scope: development ancestry
feat/phase1-agentic-phone only. The new branch is stacked on PR #67
(cfed080ad88ea4c8a9aa5e6587e602ff86e6982f) and locally merges the
complete PR #64 head (02e4493355449e94bc71d354d4744e34893bad07).
Both original draft branches are preserved; neither is merged to the
development branch or main.

## Conflict resolution

The disposable merge identified exactly three content conflicts:
- .github/workflows/ci003-reproducibility.yml: preserve both existing
  fail-closed CI job guards, retain strict independent-runner verification,
  add only one exact repository/branch-bound manual candidate dispatch per job.
  Do not broaden the existing pull-request branch trigger.
- .github/workflows/qa005-emulator.yml: retain existing PR trigger, preserve
  the UX rehearsal instrumentation requirement and QA-STACK-011's complete
  split-instrumentation evidence requirement, with exact manual candidate gate.
  Neither gate authorizes device controls.
- tests/test_qa005_workflow_gate.py: retain all eight instrumentation
  classes and the stronger assertions for MemoryVault and UX rehearsal.

All other merge changes are Git's non-conflicting union, including the
replay-ledger, command-admission, consent and CI test changes from PR #64.
No source-side security implementation is deliberately dropped.

## Acceptance boundaries

- [ ] All Python tests pass at exact candidate SHA.
- [ ] Source manifest security, accessibility, Python compilation, whitespace
      and workflow-static gates pass.
- [ ] Hosted Android/JVM and QA-005 emulator runs pass at exact candidate SHA.
- [ ] CI-003 independent runners pass strict inventory, SBOM, provenance and
      unsigned APK comparison; runner drift is not waived.
- [ ] Independent non-author reviewer checks conflict resolutions, security
      code preservation and CI evidence.
- [ ] Physical Pixel 9 Pro tests, signing, recovery and OTA remain separate
      later milestone gates.

This is an integration candidate only. No local test proves physical
hardware behavior, release readiness or an independently approved milestone.
The upstream shared SKILL.md remains unverified; PROJECT-ADAPTER.md is the
repository-specific contract.
