# Engineering Factory Run AGENT-005G — 2026-11-08

## Audit

- Repository: Davidcarmelalex/MrNothing-OS
- Authorized branch: `feat/phase1-agentic-phone`
- Parent SHA: `155295c299067c0161eddb481b7ea9a956f9a3d5`
- Recursive tree: 344 entries, complete and not truncated.
- PR #1: open, draft, targets main, head matches the authorized branch; 293 commits in PR; no submitted reviews or inline review threads.
- Other open PRs: #3–#7, inspected and untouched.
- Branch protection: unprotected; required-review enforcement is not established.
- `PROJECT-ADAPTER.md` and roadmap are present. Repository `SKILL.md` is absent. Upstream shared factory package remains unverified and is not claimed installed.

## Evidence-led diagnosis

QA-005 PR run [42407298271](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42407298271) passed SDK setup, debug and AndroidTest APK builds, emulator boot and dependency-verification negative control, then failed before test discovery. UTP reported `Starting 0 tests`, `Finished 0 tests`, and `INSTRUMENTATION_FAILED: Process crashed`. The synthetic emulator PIN cleanup succeeded.

Downloaded artifact [13588166608](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42407298271/artifacts/13588166608) contains a DropBox ANR trace. Its main thread is inside `DexFile.getClassNameList`, `DexFile.entries`, `ClassPathPackageInfoSource.findClassesInApk`, `scanForApkFiles`, `getTopLevelClassesRecursive`, `TestGrouping.testCaseClassesInPackage` and `InstrumentationTestRunner.onCreate`. The process subject is `tech.mrnothing.os failed to complete startup`. This proves the default legacy instrumentation runner's whole-package DexFile discovery is the blocked startup work; it is not evidence of MainActivity/product initialization failure. CPU pressure avg10=62.88, avg60=55.41 and total CPU 93% may amplify the scan.

## Implementation

- Keep the existing platform `android.test.InstrumentationTestRunner` and existing `InstrumentationTestCase` classes.
- Set its documented comma-separated `class` argument to the five explicit instrumentation test classes.
- Add a Python source regression test that discovers every InstrumentationTestCase class under the androidTest source directory and requires exact equality with the Gradle allowlist.
- Preserve all 30 current instrumentation test methods.
- No new dependency, product code, permission, service, trust, consent, executor, timeout or ANR-threshold change.

## Parent-head CI (not new-head acceptance)

- Phase 1 PR [42407298188](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42407298188): success; Python policy 722/722; Android unit tests, debug assembly, repeat-build comparison, strict dependency verification and modified-dependency negative control passed.
- CI-003 PR [42407298169](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42407298169): runner A, runner B and independent verifier all passed; unsigned artifacts only, `release_ready=false`.
- QA-005 PR [42407298271](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42407298271): failed before test discovery as described.

## Independent responsibilities

- Android: lifecycle and platform API correctness.
- AI/agents: deterministic plans, bounded tools and cancellation; executor remains disconnected.
- Security: owner identity, consent, revocation and fail-closed review.
- UX/accessibility: TalkBack, keyboard, large text and owner disclosure.
- CI/QA: exact-head Gradle, explicit instrumentation discovery, emulator and reproducibility evidence.
- Hardware/release: Pixel 9 Pro (caiman), StrongBox, signed artifacts, OTA and rollback.
- Independent supervisor/verifier: inspect diff and exact-head evidence separately; human security/accessibility approval remains pending.

## Milestones

- M1 Foundation: IN PROGRESS
- M2 OS interface: IN PROGRESS
- M3 Agentic intelligence: PARTIAL
- M4 Permission-controlled integrations: NOT STARTED
- M5 Pixel 9 Pro compatibility: NOT ACCEPTED
- M6 Security/privacy: IN PROGRESS
- M7 Physical hardware validation: BLOCKED — no physical-device evidence
- M8 Production readiness: BLOCKED

No milestone is complete.

## Next task — AGENT-005H

Inspect exact-head Phase 1, CI-003 and QA-005 runs. Confirm the new runner receives all five class names and executes all 30 methods. If the runner now reaches tests, fix only actual failing assertions from JUnit evidence. If class loading still stalls, capture runner arguments and per-class startup timing before changing frameworks. Keep PR #1 draft; do not merge, flash or deploy.
