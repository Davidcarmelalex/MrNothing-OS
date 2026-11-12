# QA-STACK-025 — scoped exact-head runtime verification

## Finding
PR #54 is stacked on PR #53, so its base branch is not among the restricted pull-request targets for QA-005 or CI-003. Its successful Phase 1 jobs cannot substitute for emulator or independent-runner unsigned APK evidence. No QA-005 or CI-003 run was observed for PR #54's previous head `059f7b1f0777469965ef07e4c4ef72eb4a2d4b2b`.

## Change
Allow an explicit `workflow_dispatch` only for `refs/heads/feat/qa-stack024-ci003-qa005-head-20261112` in the original repository. Both CI-003 builder and verifier jobs and the QA-005 emulator job enforce this scoped condition. Checkout still asserts the exact source SHA, persists no credentials, and uses read-only workflow permissions. The existing protected PR/push filters and concurrency semantics are unchanged.

## Acceptance
Run both workflows with `--ref feat/qa-stack024-ci003-qa005-head-20261112` after push; inspect job conclusions and downloaded emulator JUnit/QA-007 evidence and both independent unsigned builder artifacts, including exact source commit and reproducibility. A queued, skipped, or in-progress run is not a pass. Keep the PR draft, release_ready=false, and all milestones unaccepted pending independent human review, real Pixel 9 Pro testing, signing and OTA/recovery gates.

The upstream shared `SKILL.md` remains unverified; `PROJECT-ADAPTER.md` is the project-specific contract.
