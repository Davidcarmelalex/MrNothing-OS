# Engineering Factory Run AGENT-005ZC — QA build-tool parity

**Date:** 2026-11-08  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Audit head:** `44f3b5597c48dbc6a92b2f965a872a6fced1128d`  
**Task:** Make the QA-005 emulator build consume the same pinned, checksum-verified Gradle toolchain and cache policy as the Phase 1 and CI-003 Android jobs.

## Audit

- Recursive tree: 374 entries, not truncated.
- Branch comparison: 329 commits ahead of main, zero behind.
- Recent history: 20 commits inspected.
- Open PRs: #1 and #3–#7. PR #1 is open/draft against main, points to this branch, and has no submitted reviews or inline review comments.
- `PROJECT-ADAPTER.md` and the engineering roadmap exist.
- Repository `SKILL.md` is absent. The upstream shared factory package remains unverified and is not claimed as installed.
- The other five PRs and their branches were not modified.

## Evidence that selected the task

At the audit head, exact-head rerun attempt 3 showed:

| Workflow | Result | Finding |
|---|---|---|
| Phase 1 push | Passed | 785 Python tests; Android debug build/unit tests, repeat-build comparison and dependency-verification negative control passed |
| Phase 1 PR | Failed | Gradle 8.9 download returned HTTP 504 from both official endpoints |
| CI-003 push | Failed | Kotlin compiler artifact download returned HTTP 504 |
| CI-003 PR | Failed | Kotlin compiler artifact download returned HTTP 504 |
| QA-005 PR | Failed | Kotlin compiler artifact download returned HTTP 504 before emulator startup |

The QA workflow was an outlier: it used an unpinned Java 17 selector, no Gradle cache, and a direct single-host Gradle download instead of the shared checksum-verified downloader.

## Changes

1. `.github/workflows/qa005-emulator.yml`
   - Pin Temurin 17.0.21+9.
   - Use the same `~/.gradle/caches` and `~/.gradle/distributions` cache paths.
   - Keep PR cache consumers read-only.
   - Use `scripts/download_gradle_distribution.sh` for pinned Gradle 8.9 acquisition and checksum validation.
2. `tests/test_qa005_workflow_gate.py`
   - Add static tests for JDK/cache parity.
   - Reject a separate direct single-host Gradle download.
3. `docs/CI-004-DOWNLOAD-RESILIENCE.md`
   - Extend the shared acquisition policy and acceptance gates to QA-005.
4. `docs/ENGINEERING-FACTORY-ROADMAP.md`
   - Record the audit, failure evidence, implementation scope and next gate.

No Android application source, Python security runtime, permission, consent, enrollment, executor, network listener, OTA or release-signing behavior changed.

## Verification state

The two new static assertions are included in the next exact-head Phase 1 Python suite. Exact-head push/PR CI-003 and QA-005 are also required. They were not yet available at commit creation. No new-head test pass is claimed here.

The observed HTTP 504 responses are external acquisition failures, not evidence of a code assertion failure. No dependency checksum was changed, no untrusted mirror was added, and no integrity gate was bypassed.

## Safety and milestones

- No physical Pixel 9 Pro was tested or flashed.
- No production authority or signing key was provisioned.
- No device executor, production deployment or OTA was enabled.
- No merge to main or force-push occurred.
- Independent human security review of SEC-021A/B/C and SEC-022/AGENT-005Y remains pending.
- No milestone is complete. M1/M2/M6 remain in progress; M3 partial; M4 not started; M5 not accepted; M7 and M8 blocked.

## Next task

Independent security review of SEC-021A/B/C, SEC-022/AGENT-005Y and the trusted final-admission callback boundary. Keep the real executor disconnected until that gate is approved.
