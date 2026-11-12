# Independent security review packet — AGENT-006C

**Status:** Prepared for an independent reviewer; **no independent review has been performed or approved by this packet**.  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Required branch:** `feat/phase1-agentic-phone`  
**Review baseline:** `e49a9e33fca842601554e2357d0dfe9130a14f1e` (2026-11-08)  
**PR:** [#1 — Phase 1: agentic Android phone engineering foundation](https://github.com/Davidcarmelalex/MrNothing-OS/pull/1)

If the branch head changes before review, the reviewer must record the new exact SHA, inspect the delta from this baseline, and state whether the findings still apply. Do not silently review a moving branch.

## 1. Purpose and independence

This packet makes the outstanding security gate actionable. It is a review brief, not a security assessment, approval, certification, or substitute for a separate reviewer.

The reviewer must:
- Be a person distinct from the author of the implementation under review and from the automation agent that prepared this packet.
- Use a separate GitHub identity with appropriate security/code-review competence.
- Declare relevant employment, financial, authorship, and other conflicts.
- Inspect the exact source commit and relevant history, not only this summary or CI badges.
- Record reviewer identity, date, exact reviewed SHA, tools/versions, commands, evidence, findings, residual risks, and a clear disposition.
- Submit a review on PR #1. A self-review, an implementation-author comment, or a green CI run is not independent approval.

No reviewer identity was supplied or available in the repository audit. PR #1 had zero submitted reviews and zero inline review threads at the audit. The independent gate therefore remains **PENDING**.

## 2. Audit baseline and evidence

At the audit of `e49a9e33`:
- Recursive tree: 377 entries; not truncated.
- Recent history: 20 commits inspected.
- Branch comparison: 339 commits ahead of `main`, 0 behind; merge base `f3c9a701d2a337de8ef393ac14df044a79843d60`.
- PR #1: open, draft, base `main`, head `e49a9e33`, 339 commits, 313 changed files.
- Other open PRs: #3–#7; all remain on separate branches and are outside this packet's write scope.
- `PROJECT-ADAPTER.md` exists. Repository `SKILL.md` is absent. The upstream shared engineering-factory package remains unverified and is not claimed as installed.
- Repository rulesets endpoint returned an empty list. Branch-protection read returned HTTP 403, so branch protection is **unverified**, not assumed enabled.

### Exact-head GitHub Actions

All five workflows below completed successfully for source SHA `e49a9e33`:

| Workflow | Event | Run | Result |
|---|---|---:|---|
| Phase 1 checks | push | [42485836414](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42485836414) | success |
| Phase 1 checks | pull request | [42485840667](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42485840667) | success |
| CI-003 unsigned reproducibility | push | [42485836421](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42485836421) | success |
| CI-003 unsigned reproducibility | pull request | [42485840826](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42485840826) | success |
| QA-005 disposable emulator | pull request | [42485840704](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42485840704) | success |

The Phase 1 Python job reported **792 tests passed** on both push and PR. The Android job passed `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat debug-APK comparison, strict dependency verification, and the modified-dependency negative control. Python static compilation and the Android source-manifest security gate passed.

CI-003 compared two independent GitHub-hosted builders:
- Unsigned release APK: 7,867,868 bytes; 21 ZIP entries.
- APK SHA-256: `c7036c64e3a49ea9d8642c29082c42537e2c8ba0863d43d3cbd4fbb098603da7`.
- Normalized-entry SHA-256: `37b7e6846eaa4f58f143f430cb84aa481e4858c0cde392a7f2526cd8b89b9462`.
- The comparison reported byte-identical APKs, normalized contents, runtime inventory, runtime SBOM, and toolchain.
- The scoped build-environment inventory reported 1,260 components. It explicitly does not cover the complete hosted-runner image.
- CI-003 reports `reproducible=true`, `release_ready=false`. The APK is unsigned and is not a production release.

QA-005 passed on a disposable Android 15/API 35 x86_64 emulator. The log records launcher startup, 200% font scaling, HOME-role consent/cancellation, stock-launcher recovery, keyboard focus, insecure enrollment denial, owner-trust UI checks, and credential-prompt cancellation. QA-011 reports `blocked_service_disabled`; QA-012 is a structural audit only. **Spoken TalkBack navigation was not tested or accepted.** This is emulator evidence, not physical Pixel 9 Pro evidence.

These workflows are evidence of the listed automated checks only. They do not prove independent security approval, StrongBox behavior on the target device, power-cut durability, signed OTA, or production readiness.

## 3. Review scope

Review the following implementation and test surfaces together; do not infer the security property from documentation alone.

### Python admission, enrollment, and recovery
- `core/action_reservation.py`
- `core/owner_consent_transport.py`
- `core/owner_enrollment_registry.py`
- `core/owner_consent_protocol.py`
- `core/owner_consent_verifier.py`
- `core/owner_consent_issuer.py`
- `tests/test_action_reservation.py`
- `tests/test_owner_consent_transport.py`
- `tests/test_owner_enrollment_registry.py`
- Related command-admission and transport tests.

### Android permission and owner-authority boundary
- `android/app/src/main/java/tech/mrnothing/os/ActionPermissionGate.kt`
- `ActionPermissionSessionRegistry.kt`
- `ActionPreflightCoordinator.kt`
- `AndroidActionPermissionProbe.kt`
- `CommandRouter.kt`
- `OwnerAuthorityIoCoordinator.kt`
- `OwnerEnrollmentState.kt`
- Their corresponding JVM and instrumentation tests.
- `android/app/src/main/AndroidManifest.xml`

### Security contracts and threat mapping
- `docs/SEC-021A-LOCK-COUPLED-DISPATCH-ADMISSION.md`
- `docs/SEC-021B-LIVE-CAPABILITY-FINAL-ADMISSION.md`
- `docs/SEC-021C-COMMIT-ACK-LOSS-RECOVERY.md`
- `docs/SEC-022-ENROLLMENT-COMMIT-OUTCOME-UNKNOWN.md`
- `docs/THREAT-MODEL.md`
- `PROJECT-ADAPTER.md` and the roadmap for declared trust boundaries.

## 4. Required adversarial questions

The reviewer must answer each item with **PASS**, **FAIL**, or **INSUFFICIENT EVIDENCE**, cite code/test lines or a reproducible experiment, and describe impact.

### A. Identity, capability, and callback provenance
1. Can any untrusted caller construct, replay, substitute, or retain a `VerifiedOwnerActionCapability` outside the adapter-owned live session?
2. Is the exact TLS socket, TLS context, peer certificate, ALPN/version, session identity, challenge nonce, action, canonical argument digest, owner/device identity, credential generation, and consent-key digest revalidated at the final claim point?
3. Is the `final_admission_guard` genuinely supplied only by trusted adapter code in the intended deployment? The Python callable contract is not a sandbox against hostile code in the same process. Is that limitation explicit and technically acceptable for the next stage?
4. Can a public/low-level storage method's `applied` result be mistaken by any caller for authorization to execute? Trace all call sites and enforce the no-executor boundary.
5. Are clock domains and monotonic deadlines used consistently? Can wall-clock changes, integer overflow, stale challenge state, or callback reentrancy bypass expiry or replay controls?

### B. Lock ordering, concurrency, and lifecycle races
6. Verify the enrollment-registry `BEGIN IMMEDIATE` lock is acquired before the action-ledger writer transaction and held through the `DISPATCH_STARTED` commit.
7. Challenge the lock order across every code path that touches both stores. Look for reverse acquisition, nested callback database access, deadlocks, timeouts, and lock-release ambiguity.
8. Verify that signed rotation/revocation committed before the claim rejects the old credential, while a claim that commits first is durably ordered before later revocation.
9. Challenge concurrent claims, cancellation, session close, capability expiry, and revocation from separate threads and processes. Confirm exactly one claim and no automatic reclaim of `DISPATCH_STARTED`.
10. Determine whether process termination before and after each commit is adequately modeled, and clearly separate those tests from power-loss, filesystem, and storage-controller guarantees.

### C. SQLite durability, integrity, and replacement
11. Inspect database path validation, file permissions, symlink handling, sidecar/WAL behavior, transaction isolation, schema/integrity checks, and error handling.
12. Determine whether a same-user or privileged attacker can replace/rollback both stores or their containing directory. Identify what the application can and cannot detect.
13. Verify `PRAGMA query_only=ON` is applied before the reconciliation snapshot and that no reconciliation branch writes, retries, or invokes side effects.
14. Check that `APPLIED`, `NOT_OBSERVED`, and `UNRESOLVED` require exact durable history and current-row coherence; no exception text or partial history may imply success.
15. Verify commit-acknowledgement-loss behavior for enrollment, rotation, revocation, ledger claim, and outcome writes. Confirm unknown outcomes remain non-replayable.

### D. Android authority and permission enforcement
16. Trace the Android `CommandRouter` and all reachable call sites. Confirm no production executor, accessibility action, screen capture, shell, root, telephony, or other device side effect is reachable.
17. Verify owner-visible consent, system credential confirmation, permission/role/service checks, cancellation, expiry, and revocation are distinct gates; one must not be substituted for another.
18. Verify no debug-only test host or synthetic credential path is exported or included in the release variant.
19. Identify which Android checks are source/JVM-only, emulator-only, or require a physical Pixel 9 Pro/StrongBox test.

### E. Recovery and future executor boundary
20. Confirm no retry follows ambiguous storage/commit outcomes; require supervised reconciliation.
21. Specify the durable external side-effect journal and idempotency contract required before any real executor exists.
22. Define the stop/cancel/revoke semantics for an action already admitted but not yet invoked by a future platform adapter.
23. State explicit residual risks and the exact prerequisites for connecting an executor. A green CI result is not such a prerequisite.

## 5. Required independent test procedure

1. Check out exact SHA `e49a9e33fca842601554e2357d0dfe9130a14f1e`; record whether the branch has moved.
2. Inspect the complete diff for the scoped files from the merge base `f3c9a701d2a337de8ef393ac14df044a79843d60` and the relevant commit history.
3. Run the exact Python, Android unit/build, dependency-verification, and source-manifest commands declared in `.github/workflows/phase1-checks.yml`. Do not substitute a smaller test selection without marking the omitted checks.
4. Run the focused SEC-021A/B/C and SEC-022 regression cases independently, including concurrency, process-death, acknowledgement-loss, callback false/exception/non-boolean, expiry, replay, revocation, and inconsistent-history tests.
5. Inspect the QA-005 workflow and artifacts. Treat its Android 15/API 35 x86_64 emulator results as emulator-only. Do not claim spoken TalkBack or physical Pixel acceptance.
6. If a test cannot be run, record the exact missing tool/device/permission and mark it **NOT RUN** rather than passed.
7. Add adversarial tests for any uncovered issue on a separate review/fix commit; do not rewrite the reviewed baseline or silently amend it.

## 6. Acceptance and disposition

The independent review may recommend executor integration only if all of the following are satisfied:

- No unresolved Critical or High finding affects identity binding, consent, revocation, replay, final admission, or recovery.
- Every Medium/Low finding has an explicit mitigation, owner, and accepted residual-risk statement; unresolved material uncertainty blocks executor integration.
- Exact-head required tests and independent reviewer checks are reproducible.
- No Android permission or executor path bypasses owner consent, platform permission, cancellation, and recovery gates.
- External side effects remain impossible until the separate executor design, journal, idempotency, kill switch, and platform-specific tests are reviewed.
- The reviewer records one disposition: `APPROVE_REVIEW_ONLY`, `APPROVE_WITH_CONDITIONS`, `REQUEST_CHANGES`, or `INSUFFICIENT_EVIDENCE`. None of these automatically merges PR #1 or authorizes production deployment.

**This packet's current disposition: `PENDING_INDEPENDENT_REVIEW`.** It contains no findings from an independent reviewer and grants no authorization to connect a device executor.

## 7. Reviewer record (to be completed by the independent reviewer)

- Reviewer name / GitHub login:
- Role and relevant security experience:
- Independence and conflict declaration:
- Review date (UTC):
- Exact reviewed commit SHA:
- Tools and versions:
- Commands/tests executed:
- Tests not run and why:
- Findings (ID, severity, evidence, exploitability, remediation):
- Residual risks:
- Disposition:
- Executor-integration recommendation and conditions:
- GitHub review URL:

## 8. Factory stop condition

Until a separate reviewer records an acceptable disposition on the exact reviewed SHA, keep the production Android executor disconnected. Do not add accessibility execution, screen capture, shell/ADB, root, telephony control, remote device actions, production listener, release signing, OTA, or firmware flashing as a workaround for this review gate.
