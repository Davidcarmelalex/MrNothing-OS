# CI-003 exact-head verification candidate — 2026-11-14

## Scope
This draft change is stacked on PR #86 (6fe4adb070b3aa104978a409818be079b255b342).
It enables **only** the first-party PR whose head is
feat/ci003-exact-head-verify-20261114 and whose base is
feat/ci003-same-purl-drift-20261114 to enter both CI-003 builder and
independent-verifier jobs. The pull_request base-branch filter is updated
accordingly. Neither pull_request_target nor arbitrary forks are enabled.

## Why
The exact-head CI-003 reproducibility workflow did not run for PR #86.
Passing Phase 1 CI does not demonstrate that its new runner-drift diagnostics
survive independent builder comparison. The existing runner-image/OS-package
inventory mismatch is a **known blocker**, not something this trigger patch
purports to repair. A failed strict provenance check is a correct outcome.

## Acceptance and safety
1. Both independent builders check out the PR's exact head and run release
   unit tests and unsigned APK assembly.
2. The independent verifier compares APKs, environment inventory, SPDX
   documents and provenance; mismatches fail closed.
3. Any runner drift is reported as a blocker, not suppressed or normalized
   away.
4. Independent non-author review is required before integration.
5. No signing, flashing, root escalation, OTA, production deployment or merge
   is authorized by this change.

Upstream shared SKILL.md is absent/unverified. PROJECT-ADAPTER.md remains the
local project-specific adapter. M1-M8 acceptance remains unchanged (0/8).
