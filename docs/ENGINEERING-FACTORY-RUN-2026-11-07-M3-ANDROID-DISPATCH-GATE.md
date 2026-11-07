# Engineering Factory Run — 2026-11-07
## M3: remove Boolean-only Android command authorization

**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Audit baseline:** `374706cd0cbe3077409d4d740d2cf832ccebea4c`  
**Status at commit preparation:** implementation prepared; exact-head CI pending.

### Repository and governance audit

- Recursive tree: 289 entries; `truncated=false`.
- Latest 20 commits inspected. Branch compare: 242 commits ahead of `main`, zero behind; merge base `f3c9a701d2a337de8ef393ac14df044a79843d60`.
- Six open PRs: #1 and #3–#7. PR #1 is open, draft, mergeable, targets `main`, and its head matched the authorized branch. It had zero submitted reviews and zero inline review threads. Other PRs were not modified.
- Branch metadata reports `protected=false`; required-review enforcement is not established.
- `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` are present. Repository `SKILL.md` is absent. No authorized upstream shared package was verified; it is not claimed as installed.
- The latest exact-head Actions runs on the baseline all completed successfully: Phase 1 push/PR, CI-003 push/PR, and QA-005 emulator PR. Phase 1 Python/security/static and Android Gradle jobs passed; CI-003 independent unsigned release verification passed; QA-005 passed its disposable API 35 x86_64 emulator sequence. The baseline run does not establish physical Pixel 9 Pro or spoken TalkBack acceptance.
- All 47 Kotlin source/test files in the recursive tree were inspected for `CommandRouter`, `TrustedCommand` and `AgentAction` references. Only `CommandRouter.kt`, `AgentPolicy.kt` and `AgentPolicyTest.kt` contained these symbols; no other Kotlin call site used the router or command types.

### Finding

The Android `CommandRouter.execute` accepted a caller-supplied `authenticatedByTransport: Boolean`. A caller could pass `true` and reach the low-risk `get_battery` and `open_app` branches. That Boolean is not cryptographic identity, owner consent, or Android permission evidence. Although the router had no production call site in the audited Kotlin tree, retaining a callable dispatch API created a dangerous future integration path.

### Bounded implementation

1. Replaced `AgentPolicy`'s Boolean authentication/contact inputs with a risk-only classifier. Low-risk classification is explicitly not execution authorization.
2. Renamed `TrustedCommand` to `UntrustedCommandRequest`.
3. Removed the Boolean parameter and direct device-action branches from `CommandRouter`. The router now rejects every request with `VERIFIED_TRANSPORT_SESSION_REQUIRED`; malformed action names receive `INVALID_ACTION`.
4. Added JVM tests proving low-risk, screen, communications, sensitive and unknown requests are refused until a verified-session integration exists.
5. Added Python source gates proving there is no Boolean authorization parameter, no direct action dispatch, and no Android main-source call site before the typed gate is integrated.
6. Updated the M3 security contract. No network listener, shell bridge, Android permission, executor, production key, device action or physical device was added or used.

### Acceptance evidence

- New JVM tests: `CommandRouterTest` (3 cases) and revised `AgentPolicyTest` (5 cases).
- New Python source tests: `tests/test_command_router_source.py` (4 cases).
- Exact-head Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR runs are required before acceptance. Baseline-head results are not substituted for new-head evidence.
- A local clone attempt was blocked by unavailable DNS resolution for github.com; no local repository tests are claimed. GitHub Actions is the execution environment for this change.

### Milestone state

M1 FOUNDATION — IN PROGRESS.  
M2 OS INTERFACE — IN PROGRESS.  
M3 AGENTIC INTELLIGENCE — PARTIAL.  
M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED.  
M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED.  
M6 SECURITY/PRIVACY — IN PROGRESS.  
M7 PHYSICAL HARDWARE VALIDATION — BLOCKED.  
M8 PRODUCTION READINESS — BLOCKED.

No milestone is complete. Independent human security review, spoken TalkBack, physical Pixel 9 Pro/StrongBox validation, signed release, OTA rollback and production readiness remain unverified.

### Next engineering task

Implement a verifier-originated typed action capability bound to owner, device, exact live transport session, action and canonical argument digest. It must not be constructible from caller-supplied identity fields. Add a fake/no-op executor only after the capability boundary and adversarial tests are accepted.


### Exact-head CI correction — stale source assertion

The first exact-head Phase 1 push and PR Python jobs (runs `42329977022` and `42329981830`) each executed 592 tests and reported one failure. The failure was the pre-existing `tests/test_screen_action_preflight_source.py` assertion still expecting the removed `Verdict.APPROVAL_REQUIRED` string after the risk-only API migration. The new command-router source tests themselves passed. This was a stale test contract, not an Android compile or runtime failure.

Updated the existing source gate to assert the new `ActionRisk.OWNER_APPROVAL_REQUIRED` classification and the router's explicit `VERIFIED_TRANSPORT_SESSION_REQUIRED` denial, while retaining checks that no screen-action strings or device dispatch appear in the router. No production Kotlin source changed in this correction. Exact-head Phase 1, CI-003 and QA-005 reruns are pending; the failed parent-head runs are not acceptance evidence.
