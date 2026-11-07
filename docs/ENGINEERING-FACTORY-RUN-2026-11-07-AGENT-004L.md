# Engineering Factory Run — AGENT-004L

Repository: Davidcarmelalex/MrNothing-OS  
Authorized branch: feat/phase1-agentic-phone  
Audit baseline: 43ad1c83fa46d3d3305d5a96948cb171d8f0e8f7  
Scope: M3/M4 boundary — owner-visible Accessibility disclosure and revocation handoff.

## Repository and governance audit

- Recursive tree: 312 entries, truncated=false.
- Latest 20 branch commits inspected. Branch compare: 260 commits ahead of main, zero behind; merge base f3c9a701d2a337de8ef393ac14df044a79843d60.
- Six open PRs: #1 and #3–#7. PR #1 is open/draft against main, and its head matched the authorized branch. It had zero submitted reviews and zero inline review threads. Other PRs were not modified.
- Branch metadata reports protected=false; the rulesets collection is empty. The branch-protection detail endpoint returned HTTP 403 to the connected integration, so enforcement is not independently verified.
- PROJECT-ADAPTER.md and docs/ENGINEERING-FACTORY-ROADMAP.md are present. Repository SKILL.md is absent. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed.
- Exact-head baseline 43ad1c83 passed Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR workflows (runs 42351751632, 42351756233, 42351751577, 42351756078 and 42351756443). The Phase 1 Python jobs each reported 668 tests passed; Android debug unit/build/repeat-build/dependency gates passed; CI-003 independent unsigned release reproducibility passed; every QA-005 job step completed successfully on its disposable API 35 x86_64 emulator. QA-011 remains a TalkBack availability preflight and QA-012 structural semantics only, not spoken TalkBack acceptance.
- The main manifest has no AccessibilityService or MediaProjection service. ScreenActionPreflight expects the future exact component tech.mrnothing.os.OwnerScreenControlAccessibilityService; action permission probes and the lifecycle registry remain disconnected from CommandRouter.

## Selected task

Implement owner-visible Accessibility disclosure and Android Settings handoff without declaring or enabling a service. This is the next unblocked step in docs/M3-PLATFORM-SESSION-LIFECYCLE.md. Independent security/accessibility review remains a prerequisite before any real service declaration.

## Implementation

1. Added a pure-JVM status reader with NOT_REGISTERED, REGISTERED_DISABLED, ENABLED_IN_SETTINGS and fail-closed UNAVAILABLE states.
2. Added a read-only Android probe that checks the exact app package and centralized service component in the package manifest and enabled AccessibilityService list.
3. Added a non-exported disclosure Activity, explicit owner-initiated Settings.ACTION_ACCESSIBILITY_SETTINGS handoff, Settings fallback and fresh status read on resume.
4. Added a launcher entry with a descriptive label.
5. Reused the centralized component identity in ScreenActionPreflight.
6. Added pure-JVM, instrumentation and Python source-boundary tests.
7. Kept the manifest free of AccessibilityService/MediaProjection declarations and new permissions. No permission prompt, service toggle, executor, session provider or command-router integration was added.

## Tests and CI at submission

- Local pure-JVM Kotlin harness: five disclosure state scenarios passed (not a Gradle/JUnit run).
- Full repository Python policy suite, Android Gradle/JUnit and emulator validation: exact-head GitHub Actions pending at commit preparation.
- No Android SDK was installed in the local container, so no local Android Gradle build or emulator run is claimed.

## Safety and remaining gates

No service is registered, no accessibility or projection permission is declared/granted, no system setting is modified, no screen content is read, no gesture/navigation action is performed, no network listener or executor is connected, and no physical device is accessed.

M1 FOUNDATION — IN PROGRESS.  
M2 OS INTERFACE — IN PROGRESS.  
M3 AGENTIC INTELLIGENCE — PARTIAL.  
M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED.  
M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED.  
M6 SECURITY/PRIVACY — IN PROGRESS.  
M7 PHYSICAL HARDWARE VALIDATION — BLOCKED.  
M8 PRODUCTION READINESS — BLOCKED.

No milestone is complete. Independent human security review, spoken TalkBack acceptance, physical Pixel 9 Pro/StrongBox validation, signed release, OTA rollback and production readiness remain unverified.

## Next task

After independent security/accessibility review, implement the narrowly scoped AccessibilityService provider and wire only its actual onServiceConnected, onUnbind and destruction callbacks to the exact session lease. Keep the service undeclared until the review gate passes. Add process-death, reconnect, stale-callback, stop/revocation and TalkBack coexistence tests. MediaProjection remains a separate later workstream.
