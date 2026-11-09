# MrNothing OS — verified engineering milestones

## Current factory audit — 2026-11-08

**Source/test baseline:** `3fd85d229debc361ddece0e9cf2aeec567e104cd` on `feat/phase1-agentic-phone`. Recursive tree: 377 entries, not truncated. Latest 20 branch commits inspected. `main...feat/phase1-agentic-phone`: 333 ahead, 0 behind. Six open PRs (#1 and #3–#7) inspected. PR #1 remains open/draft against `main`, at the audited head, with 333 commits/313 changed files and no submitted reviews or inline review threads. `PROJECT-ADAPTER.md` exists; repository `SKILL.md` is absent; the upstream shared package remains unverified and is not claimed installed.

Exact-head Phase 1 push/PR, CI-003 push/PR and QA-005 PR all passed at this source baseline. Python policy: 792 tests passed on each Phase 1 event. Android Gradle unit/build, repeat debug build, strict dependency verification and negative control passed. Independent CI-003 runners produced byte-identical unsigned APKs; provenance reports `release_ready=false`. QA-005 completed on a disposable Android API 35 x86_64 emulator; 30/30 instrumentation progress, 0 failed/0 skipped. QA-011 remains `blocked_service_disabled`; QA-012 is structural only, not spoken TalkBack acceptance.

The security chain now includes SEC-021A/B/C and SEC-022 prototypes, but these remain same-host/no-side-effect foundations. The trusted in-process final-admission callback, database replacement assumptions, power-loss durability and external-effect recovery require independent review. The Android CommandRouter remains fail-closed and the real executor remains disconnected. No physical Pixel 9 Pro was tested; no milestone is complete.

**Historical SEC-017 audit baseline:** 2026-11-05, branch feat/phase1-agentic-phone at f5607aa9ddf52b3c9bacf8ac959fe786db1b4835. Exact-head push checks (run 41989793035), PR checks (run 41989800493) and QA-005 disposable x86_64 emulator workflow (run 41989800863) all completed successfully. Android Gradle/JUnit, Python policy/static checks and repeat debug-APK comparison passed. QA-005 through QA-010 and QA-013 passed; QA-011/012 remain read-only preflights, not TalkBack speech acceptance. SEC-017 signed durable paired enrollment is implemented with synthetic software keys. Production authority-key provisioning, verifier-time revocation, connected command execution, custom firmware, OTA and release signing have not been demonstrated.

| Gate | Owner(s) | Objective acceptance evidence | Baseline |
| --- | --- | --- | --- |
| **M1 Foundation** | CI/QA + Android | reproducible pinned build, test inventory, threat model, CI green, reviewed adapter, supervisor signoff | IN PROGRESS |
| **M2 OS interface** | Android + UX | default HOME role, app library, accessibility checks with TalkBack/large text, user-controlled stock-launcher recovery, emulator E2E | IN PROGRESS (QA-005 emulator workflow passed; TalkBack speech acceptance and hardware remain unverified) |
| **M3 Agentic intelligence** | AI/agents | authenticated deterministic plan->tool->result state machine, cancellation, injection and timeout tests, 20 sandbox scenarios | PARTIAL (v1/v2 capability primitives and durable reservation prototype; no integrated executor or Android permission gate) |
| **M4 Device integrations** | Android + security | opt-in permission UX, 5 supported app workflows, revocation tests, no restricted-screen bypass | NOT STARTED |
| **M5 Pixel 9 Pro compatibility** | Hardware/release | caiman build/ABI checks, vendor/boot chain analysis, modem limitations documented, recovery plan | NOT ACCEPTED (no physical-device evidence) |
| **M6 Security/privacy** | Security + verifier | threat model, device-bound keys, persistent replay prevention, no high-risk findings, encryption/retention/kill-switch tests | IN PROGRESS (StrongBox/consent prototypes; independent review pending) |
| **M7 Physical hardware** | Hardware + QA | actual Pixel 9 Pro evidence: install, reboot, SIM/VoLTE, Wi-Fi/Bluetooth, battery, thermal, accessibility, rollback; separately prove two-way SIM AI audio | BLOCKED: device access |
| **M8 Production readiness** | Release + supervisor | signed reproducible artifacts, SBOM, 100 scripted scenarios, measured reliability, OTA rollback drill, privacy/legal review, independent signoff | BLOCKED by M1–M7 |

**No milestone is COMPLETE.** Estimates are not acceptance evidence. Overall completion percentages are informal planning estimates and must never replace gates.

## Highest-priority engineering backlog
1. **SEC-001**: make signed command admission fail closed with durable replay state, explicit device-key boundary, strict payload validation and restart tests. *No network exposure.*
2. **CI-002**: pin Android build tooling and add reproducibility/manifest security checks; retain debug artifact labels. **IMPLEMENTED AND CI-PASSING** at ecfbf9f (two successful runs), but independent signoff and release-grade provenance remain pending. Do not duplicate this task.
3. **UX-003**: accessible launcher and owner-controlled stock-launcher recovery. **SOURCE IMPLEMENTED** at 6cb27de with contrast, 56dp touch-target and recovery source gates; TalkBack/large-font emulator tests and independent review remain open. Do not mark M2 complete.
4. **AGENT-004**: authenticated device enrollment and revocation design, Keystore-bound keys, idempotent task executor with cancellation. AGENT-004A/B/C provide isolated verifier, Android signer and host challenge issuer; AGENT-004D adds a server-side mTLS peer adapter; AGENT-004E provides a synthetic no-execution integration harness; AGENT-004F adds deterministic parser/signature mutation coverage. SEC-017 adds a signed durable paired owner/device registry and credential-generation snapshot binding. Verifier-time revocation, production authority-key provisioning, rate limiting, separate operational audit logging, remote attestation, independent security review and supervised executor remain open.
5. **QA-005**: Android emulator E2E launch/role tests and screenshot/accessibility evidence.
6. **HW-006**: Pixel hardware matrix, SIM audio feasibility and firmware rollback validation after hardware is available.

## Independent supervisor gate
For every PR: compare actual diff against task scope; verify tests independently; check secrets, permissions, command authorization, rollback and user consent; reject unsupported completion claims. The code author cannot self-approve. If a second reviewer is unavailable, record PENDING_INDEPENDENT_REVIEW.

## Release blocks
No root/firmware flash or production deployment from CI. No public command endpoint until identity enrollment, encryption, durable replay, revocation, rate limits, threat review and audit logging are tested. No physical-device or SIM audio claims without hardware logs.

## AGENT-013 offline plan simulator (2026-11-02)

Implemented a bounded M3 prototype at core/agent_sandbox.py with a strict 20-step limit, full preflight, explicit no-side-effect results, cancellation/deadline checks and 34 regression tests. See AGENT-013 evidence (AGENT-013-OFFLINE-PLAN-SIMULATOR.md). Local tests passed; GitHub CI and independent review are separate gates. This does not replace AGENT-004 authenticated enrollment, nor imply a production agent. The upstream shared SKILL.md remains unverified.

## AGENT-004A cross-platform consent protocol primitive (2026-11-05)

Implemented a bounded P-256 ECDSA verification primitive and matching Kotlin/Python canonical payload encoders. Both platforms consume the same Java-Properties fixture at android/app/src/test/resources/owner-consent-v1.properties. The Python verifier requires an authenticated transport, a host-issued challenge, an enrolled P-256 public key supplied by a trusted registry, exact challenge-field matching, a 30-second maximum lifetime and atomic nonce consumption through the existing SQLite replay ledger.

This is not yet Android signing, challenge issuance, key registry integration, permission granting or command execution. The existing HMAC consent verifier remains a separate offline prototype. See AGENT-004A-CONSENT-PROTOCOL.md. Keep M3 partial and M6 in progress until Android per-use signing, host challenge provenance, supervised integration and independent security review pass. The upstream shared SKILL.md remains unverified.

## AGENT-004B AndroidKeyStore per-use signing primitive (2026-11-05)

Added an isolated Android signer that loads only the existing StrongBox-backed owner-key alias, prepares SHA256withECDSA, binds the operation to the framework BiometricPrompt.CryptoObject, requires strong biometric or device-credential authentication, rechecks device safety, locally verifies the resulting signature and emits the AGENT-004A envelope. Cancellation and all failures refuse; no software-key or key-generation fallback exists.

The source manifest now declares only android.permission.USE_BIOMETRIC; the manifest gate explicitly allowlists that one permission and rejects duplicates or all unreviewed permissions. JVM tests cover canonical envelope formatting and synthetic DER bounds; Python source tests guard the StrongBox/CryptoObject/no-executor boundary.

This is not a production consent flow: no host challenge issuer, trusted registry, authenticated transport, caller integration, permission grant or command execution exists. The signed-64-bit parity correction remains in open draft PR #7 and is not part of this branch baseline. Physical StrongBox/Pixel validation and independent review remain pending. Keep M3 partial and M6 in progress.


## AGENT-004C host-side owner-consent challenge issuer prototype (2026-11-05)

Added core/owner_consent_issuer.py as a bounded library primitive. It creates a 128-bit secrets-based nonce, validates a live host-authenticated session assertion against a read-only enrolled-device registry, validates canonical P-256 SPKI DER, binds owner/device/session/action/time, limits challenge lifetime to 30 seconds and caps expiry at the session expiry. It returns the trusted registry public key for the host verifier and does not execute actions.

Eleven focused tests cover successful issuance, nonce format, session expiry capping, signed-64-bit boundary behavior, invalid/future/expired sessions, invalid clock and action, nonce-source failure, unknown/inactive/mismatched device records, registry failure and RSA/P-384/malformed public keys.

The session object is not cryptographically unforgeable; its provenance depends on a trusted transport adapter. SEC-017 now supplies a signed durable registry, but its offline authority key and first-install process are not provisioned or connected to a production service. No authenticated network endpoint, attestation-chain validation, rate limiter, audit log, Android caller integration, permission grant or command execution was added. The issuer is stateless; the existing SQLite replay ledger remains responsible for atomic one-use consumption. Keep M3 partial and M6 in progress pending integration and independent security review. The upstream shared SKILL.md remains unverified.


## AGENT-004E synthetic end-to-end consent-flow harness (2026-11-05)

Added `tests/test_owner_consent_flow.py` to exercise the existing AGENT-004C issuer, AGENT-004A P-256 verifier and SQLite `DurableReplayLedger` in one test-only path. The harness uses an in-memory fake registry, a synthetic transport-authenticated session assertion and ephemeral software P-256 keys generated inside tests. It covers no-execution admission, persistent replay rejection after ledger reopen, concurrent duplicate submission, signature tampering, wrong signing key, unauthenticated transport, session-expiry capping, owner/device mismatch, registry failure and ledger failure.

The only positive verifier result is `ADMITTED_NO_EXECUTION`. This does not establish authenticated-session provenance, Android StrongBox operation, real attestation, a persistent enrollment registry, rate limiting, production transport or any device-action execution. AGENT-004D now provides a testable mTLS peer adapter, but its synthetic certificate tests do not establish production enrollment provenance or Android client-certificate provisioning. Keep M3 partial and M6 in progress; no milestone is complete. The upstream shared SKILL.md remains unverified.


## AGENT-004F deterministic adversarial consent-envelope corpus (2026-11-05)

Added `tests/test_owner_consent_parser_mutations.py` and the matching test specification. The six test methods exercise valid JSON whitespace and the exact envelope-size boundary; malformed UTF-8/BOM, duplicate keys, invalid root/payload shapes, deep nesting and oversize input; payload type confusion and field-set changes; non-finite numbers; Base64URL alphabet/length/padding/pad-bit and malformed-DER cases; and a one-character mutation at every signature position. A final valid signature is accepted after the mutation corpus, demonstrating that rejected mutations did not reserve the challenge nonce.

This is test-only coverage: no production parser behavior, runtime dependency, transport, enrollment, Android permission, StrongBox, device action or release behavior changed. Synthetic software keys and a temporary SQLite ledger are used only inside tests. Exact-head GitHub Actions results determine acceptance. Keep M3 partial and M6 in progress; AGENT-004D's host-side mTLS adapter is implemented; trusted enrollment ceremony, rate limiting, audit logging, verifier-time revocation and independent review remain open. The upstream shared SKILL.md remains unverified.


## AGENT-004D mTLS peer-to-session adapter (2026-11-05)

Added `core/owner_consent_transport.py` and `tests/test_owner_consent_transport.py`. The adapter accepts only a live server-side `ssl.SSLSocket` created with its exact TLS server context; requires client certificates, TLS 1.2+, the owner-consent ALPN identifier and a current P-256 client-auth leaf certificate; maps the exact SHA-256 leaf fingerprint to an active trusted transport-enrollment record; then constructs a fresh 30-second `AuthenticatedOwnerSession` internally and delegates to AGENT-004C. It never accepts a caller-supplied authenticated flag or session object.

The local test harness uses a socket pair, an ephemeral software CA and synthetic client/server certificates. It covers successful owner/device-bound issuance, context identity, ALPN mismatch, missing client certificate, optional-client-cert rejection, unknown/revoked certificate, revocation recheck, unsupported P-384 transport key, registry failure, invalid clock, closed socket and consent-registry owner mismatch. These are host-side synthetic mTLS tests, not Android client authentication or hardware attestation.

Transport identity and the per-use owner-consent signing key remain separate credentials and must be bound by a trusted owner-approved enrollment ceremony. No network listener, public endpoint, production CA, certificate enrollment database, OCSP/CRL validation, rate limiter, durable audit log, Android client-certificate provisioning, command executor, permission grant or device action was added. Leaf revocation blocks new challenge issuance; the current verifier does not perform a live registry lookup at consumption time. Keep M3 partial and M6 in progress. Exact-head CI and independent security review remain required. The upstream shared SKILL.md remains unverified.


## SEC-017 signed durable owner/device enrollment registry (2026-11-05)

Implemented `core/owner_enrollment_registry.py` as a single SQLite store for both AGENT-004C consent-key lookup and AGENT-004D transport-certificate lookup. Enrollment, rotation and revocation require short-lived canonical Ed25519-signed statements from an externally pinned authority public key. The store binds owner, device, exact transport certificate fingerprint, canonical P-256 consent SPKI, credential generation and active state in one row. It enforces unique credential bindings, exact generation advancement, a 5-minute statement lifetime, signed-64-bit timestamps, 0600 POSIX file permissions, no symlink use, explicit first-install initialization, SQLite `BEGIN IMMEDIATE` transactions, bounded device/history/database capacity and append-only enrollment history.

AGENT-004D now places the transport fingerprint and credential generation in its internally created session. AGENT-004C compares that snapshot with the paired registry record and rejects a credential-generation change between the transport and consent lookups. This closes that specific inter-lookup rotation race; it does not replace verifier-time revocation. The authority private key is not in the repository, no production public key is provisioned, no Android enrollment ceremony or network listener is connected, and restoring an old complete SQLite database can roll back local history. A previously issued challenge may still be accepted until its 30-second expiry unless the verifier performs an active-generation lookup at consumption time.

Synthetic tests use ephemeral software keys and fingerprints only. Independent security review remains pending; no command executor, permission grant, physical device or production release is enabled. The upstream shared SKILL.md remains unverified.


## SEC-018 — verifier-time paired-enrollment revalidation (2026-11-05)

The P-256 verifier now requires the trusted host to supply the authenticated transport certificate fingerprint, credential generation and paired enrollment registry. After signature verification it re-reads the active owner/device record and compares owner, device, exact consent SPKI, transport fingerprint and generation with the challenge/session snapshot. It performs a second read after durable nonce reservation; any revocation, rotation, registry outage or identity/key mismatch observed before return fails closed. If a change is detected after nonce reservation, the nonce remains consumed, preventing retry with the same capability.

Regression tests cover revocation after issuance, transport/key rotation, registry outage, and revocation observed between the pre- and post-reservation checks. The positive result remains `ADMITTED_NO_EXECUTION`; no action is executed. This is a double-check around a separate replay-ledger transaction, not an atomic cross-database transaction. A revocation immediately after the final check can still race with a future executor; any executor must revalidate current enrollment atomically with action admission before it is implemented. The upstream shared SKILL.md remains unverified; this is project-specific work.


## SEC-019A — atomic enrollment-aware consent admission (2026-11-05)

The verifier no longer performs two enrollment reads around a nonce write to a separate replay database. The paired owner/device enrollment database now has an additive v2 schema containing `owner_consent_replay`. `SQLiteOwnerEnrollmentRegistry.consume_consent_nonce` checks active owner/device identity, exact P-256 SPKI, transport certificate fingerprint and credential generation, then inserts the one-use nonce under the same SQLite `BEGIN IMMEDIATE` transaction. Signed enrollment rotation/revocation uses the same writer lock, so admission and credential changes have a single database serialization order. Replay state is persistent across process/registry reopen, is never evicted using wall-clock time, and has a 10,000-row bound; capacity exhaustion fails closed. Existing v1 databases require an explicit, additive `migrate_v1_to_v2(explicit_migration=True)`; ordinary startup/lookup never silently migrates or resets them.

Synthetic registry tests cover one-use persistence after reopen, revocation and rotation committed before admission, concurrent duplicate submissions, wall-clock advance/rollback non-eviction, invalid nonce rejection and explicit/idempotent v1 migration. The verifier still accepts a trusted-host boolean plus certificate/generation snapshot; binding the challenge to the exact live TLS socket/session remains the next security gate. The host enrollment authority, client certificate provisioning, remote attestation, independent review and command execution remain unimplemented. Positive outcome remains `ADMITTED_NO_EXECUTION`. No milestone is complete and the upstream shared `SKILL.md` remains unverified.


## SEC-019B — exact live TLS socket/session binding (2026-11-05)

Implemented on feat/phase1-agentic-phone after SEC-019A. OwnerConsentTlsAdapter now retains each adapter-issued session and its challenges in a weak-key map keyed by the exact server-side SSLSocket object. It revalidates the open socket, exact server SSLContext, TLS 1.2+, ALPN, client-certificate profile, current transport-certificate enrollment and credential generation at challenge issue and verification. Challenge verification requires exact equality with a challenge issued on that same socket; a new or resumed connection cannot inherit the previous socket's challenges. Session and challenge expiry are additionally enforced with monotonic deadlines so wall-clock rollback cannot revive an expired in-memory capability.

The supported production-facing library call is OwnerConsentTlsAdapter.verify_and_consume(peer, envelope, challenge). Callers cannot provide an authentication boolean, session identifier, certificate fingerprint, credential generation or public verification key. The private P-256 verifier helper is not a request-facing API. The adapter re-reads the current paired owner/device record and passes the current key and adapter-derived transport binding to SEC-019A's atomic nonce transaction. The only success result remains ADMITTED_NO_EXECUTION.

Synthetic local mTLS tests cover same-socket admission and replay, cross-socket challenge substitution, modified/unissued challenge rejection, monotonic expiry despite wall-clock rollback, transport-certificate revocation, credential-generation changes, closed sockets, consent-registry outage and the public method signature. These tests do not create a public listener or connect an executor. Exact-head GitHub CI and emulator QA must be inspected after push; no physical Pixel test is implied. Independent security approval remains PENDING.

## Factory audit update — 2026-11-05

The current recursive feature-branch tree contains 203 entries and no SKILL.md. PROJECT-ADAPTER.md is present at repository root. An authorized Library title-only search for SKILL.md returned no result; no upstream shared package was supplied or verified. The local adapter remains project-specific and is not an upstream installation.

The branch still has open draft PRs #1, #3, #4, #5, #6 and #7. PR #1 is the only PR whose head is the authorized working branch; the others are separate workstreams and were not modified. The independent supervisor/security review remains pending. All M1–M8 gates remain incomplete or blocked as defined above.


## SEC-019B exact-head evidence — 2026-11-05

Implementation head `02ac61a00f2f49f4ca0c9ff779ad8fa5fbf14e7a` passed push Phase 1 run 42004622475 and PR Phase 1 run 42004630428. Both runs executed 358 Python tests (all passed), Python compile/static gates, Android manifest policy, Gradle unit tests, debug APK assembly and same-run repeat APK comparison. Debug APK provenance and a not-for-release artifact were uploaded.

The independent x86_64 emulator workflow [42004630445](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42004630445) passed QA-005 through QA-010 and QA-013. QA-011 reported `blocked_service_disabled`; QA-012 was structural semantics only, not spoken TalkBack acceptance. No Pixel 9 Pro was used.

Two independent GitHub runners generated different debug APK SHA-256 values for the same source commit: push runner `94cc1d20431c95689b4c4bd459d3f09c226472cdd01f1a9add14262e3d19a1f7`, PR runner `5b9e3d16c3f6fd5bc005afca12e92c46e74bddead840ff535dc9aecd0b39b9ae`. This is a confirmed cross-run hash mismatch. The default debug-signing setup may explain it, but the cause has not been isolated. Cross-host reproducibility remains unverified and is a production-readiness blocker.

## Next bounded release-engineering task — CI-003

Produce a deterministic unsigned Android build artifact (or a separately controlled, explicitly non-production CI signing profile), compare normalized APK contents and provenance across independent runners, record SDK/build-tools/action versions, and add an SBOM. Keep debug keys non-production and never introduce a production signing key into CI. Acceptance requires independent-runner equivalence and documented signature treatment; same-run repeat builds alone are insufficient.


## CI-003 — independent-runner unsigned Android reproducibility (2026-11-05)

Implemented a dedicated CI workflow with two isolated ubuntu-24.04 builder jobs and a third verifier job. Both builders use a checksum-verified Gradle 8.9 distribution, Temurin JDK 17.0.13+11, AGP 8.7.3, Kotlin 2.0.21, Android platform 35 and build-tools 35.0.0. The release build has no signing configuration; the verifier rejects v1 signatures and APK Signing Scheme v2/v3 blocks.

A deterministic SPDX-2.3 SBOM is generated from resolved releaseRuntimeClasspath artifacts and includes each dependency checksum and Maven purl. The SBOM explicitly excludes build plugins, Gradle internals and SDK packages; those top-level inputs are captured in unsigned build provenance. Whole APK bytes, normalized ZIP entry content, SBOM, runtime inventory, source commit and toolchain inputs must match across the independent runners.

**Acceptance state:** PASSED on exact source commit 43e0e0f5f86718fd1c3265364c71bed8547b8a7c. Push run 42014136696 and PR run 42014145465 both passed the two-builder and independent-verifier jobs. The unsigned APK was byte-identical across runners (SHA-256 4a79cd0be8e6001bae9246eb2b4e6b45ebdaaece79a068bde95ab64d0ba7a4b9); normalized APK entries, runtime inventory, SPDX-2.3 SBOM and recorded toolchain inputs matched. The SBOM contains the app plus two resolved runtime artifacts. Provenance explicitly says release_ready=false and provenance_signed=false. This validates this exact unsigned build pair only. It does not complete M1 or M8; independent supervisor approval, signed reproducible release, physical Pixel validation and remaining product gates are still outstanding.


## CI-003 exact-head acceptance and CI-004 hardening — 2026-11-05

The branch reached `d5eaf80e39571e0aeaef6013c0af049151e1f77b`. Exact-head Phase 1 push/PR checks passed (runs 42014876703 and 42014883122); the Python policy job executed 370 tests. CI-003 push/PR checks passed (42014876770 and 42014883313), including two independent unsigned builders and the verifier. QA-005 emulator run 42014883226 completed successfully. QA-011 only confirmed TalkBack availability and reported the service disabled; QA-012 was a structural audit, not spoken navigation.

CI-003 verified byte-identical unsigned APKs across two independent GitHub-hosted runner jobs, matching normalized APK entries, runtime dependency inventory, SPDX-2.3 runtime SBOM, recorded toolchain and source commit. The unsigned artifact remains `release_ready=false`; the runtime SBOM is not a complete build-environment SBOM.

**CI-004** pins all GitHub Actions used by the three repository workflows to full commit SHAs resolved from official action tag refs; checkout credential persistence is disabled; workflow permissions remain `contents: read`; runner labels are explicit `ubuntu-24.04`. A standard-library regression suite guards these invariants. See [CI-004](CI-004-ACTION-PINNING.md).

**Milestone state:** M1 remains IN PROGRESS pending immutable workflow hardening CI, complete dependency verification, independent supervisor approval and reviewed release governance. M2 remains IN PROGRESS; spoken TalkBack and physical-device validation are open. M3 remains PARTIAL with no integrated executor. M4 and M5 remain NOT STARTED. M6 remains IN PROGRESS pending production trust provisioning and independent security review. M7 remains BLOCKED by Pixel 9 Pro access. M8 remains BLOCKED.

## Next bounded engineering task — CI-005 dependency verification

Add Gradle dependency verification metadata for the Android plugin, buildscript and runtime/test dependency graphs. Generate SHA-256 verification metadata in a controlled CI process, commit only reviewed checksums and trusted repository identities, enable strict verification in all Android workflows, and add a negative test proving a modified dependency artifact fails before compilation. Preserve the pinned Gradle distribution checksum and keep CI artifacts unsigned/non-release. Do not generate production signing keys or alter release status.


## CI-005 Gradle dependency verification — implementation pending exact-head CI (2026-11-05)

A temporary bootstrap workflow generated candidate Gradle SHA-256 dependency-verification metadata on two independent jobs for source commit `c4de864f784afab71419f568acad7011b472e451`. Push run 42019671946 and PR run 42019677930 both succeeded and produced byte-identical metadata (249 components, 441 artifacts/checksums; SHA-256 `1650f08eb3d1006045efc9ea32507245a5464e8126fba10d6e915343876da2ec`). The candidate was structurally inspected before inclusion; the temporary bootstrap workflow is removed in the implementation commit.

The implementation adds `android/gradle/verification-metadata.xml`, strict Gradle dependency verification to all three Android workflows, a disposable local-Maven positive/negative tampering test, and standard-library metadata/workflow regression tests. This is checksum verification, not publisher-signature verification; the generated file does not bind artifacts to repository URLs. Exact-head CI acceptance is pending. Keep M1 IN PROGRESS and M8 BLOCKED.


## CI-005 exact-head acceptance — 2026-11-05

CI-005 is **IMPLEMENTED AND EXACT-HEAD CI-PASSING** on `0cf420e8f40580a6a75efbd4bc1de11d0e72db91`. Phase 1 push/PR runs 42020767479 and 42020774162 passed; both Python policy jobs ran 380 tests, and both Android jobs passed strict dependency verification, unit tests, debug assembly, repeat APK comparison and the tampered-artifact negative control. CI-003 push/PR runs 42020767603 and 42020774161 passed both independent builders, their negative controls, unsigned release assembly, SPDX runtime SBOM and the independent artifact verifier. QA-005 PR run 42020774153 passed the strict-verification negative control and emulator checks QA-005 through QA-010 and QA-013. QA-011 reported TalkBack service disabled; QA-012 was structural semantics only.

The candidate metadata was independently generated and compared from two bootstrap runners (249 components, 441 artifact checksums; SHA-256 `1650f08eb3d1006045efc9ea32507245a5464e8126fba10d6e915343876da2ec`). It is checksum verification, not PGP publisher-signature verification, and does not bind artifact coordinates to repository URLs. No production signing or release readiness is implied.

**Next bounded security task — SEC-020:** define and implement the offline enrollment-authority public-key provisioning and first-install trust ceremony, including owner-visible fingerprint confirmation, anti-rollback generation handling, rotation/recovery, synthetic failure-injection tests and explicit no-network/no-execution boundaries. Keep the executor disconnected until the independent security gate passes.

**Milestone state remains unchanged:** M1 IN PROGRESS, M2 IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M6 IN PROGRESS, M7 BLOCKED by physical Pixel access, M8 BLOCKED. No milestone is COMPLETE; independent supervisor/security approval remains pending.


## SEC-020A exact-head verification — 2026-11-05

SEC-020A policy implementation source commit: b4b6dad184d48055753bda2087e28292a1a2a008.

All five final exact-head GitHub Actions workflows passed:

| Workflow | Event | Run | Result |
| --- | --- | --- | --- |
| Phase 1 checks | push | [42024219462](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42024219462) | success |
| Phase 1 checks | pull request | [42024226415](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42024226415) | success |
| CI-003 unsigned reproducibility | push | [42024219429](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42024219429) | success |
| CI-003 unsigned reproducibility | pull request | [42024226462](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42024226462) | success |
| QA-005 disposable emulator | pull request | [42024226407](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42024226407) | success |

Evidence:
- Phase 1 push and PR each ran 380 Python tests; both passed Python compilation, Android source/manifest gates, Gradle debug unit tests, debug assembly, strict dependency verification and the modified-artifact negative control.
- The new OwnerAuthorityTrustCeremonyTest JVM cases were included in the successful Gradle testDebugUnitTest task on both push and PR.
- CI-003 push and PR each passed both independent builders and the independent verifier. Release unit tests, unsigned release assembly, strict dependency verification, tampered-artifact negative control, runtime inventory, SPDX-2.3 runtime SBOM and provenance generation passed.
- Both independent runners produced byte-identical unsigned APKs: 2,133,809 bytes, 13 ZIP entries, SHA-256 972cc506d948a34321351785f51129022be0eb0d7b54ed4ae18b9d53bd8f7993. Normalized APK-entry digest: 60cc97ce7e864018ef273ab5180f81328e4edf77565adade460a7eda020ca41c.
- Runtime inventory SHA-256: a8a1b16dd1cefb90d14426c477e924a3710c7a160def52a2ece3a6d55c266e44. SPDX runtime SBOM SHA-256: 330c5e77bb72bbf5283b2370d1bd39c63a1d645860439b488484ac068fbe6610.
- Recorded toolchain: ubuntu-24.04, Temurin/OpenJDK 17.0.13, Gradle 8.9 with the committed distribution checksum, AGP 8.7.3, Kotlin 2.0.21, Android platform 35, build-tools 35.0.0 and sdkmanager 12.0.
- QA-005 booted a disposable x86_64 emulator. Launcher/recovery, 200% font, HOME cancellation/acceptance, stock-launcher restore, keyboard accessibility and insecure-enrollment denial passed. QA-011 reported blocked_service_disabled; QA-012 was structural semantics only, not spoken TalkBack acceptance. Emulator evidence artifact: [13413117195](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42024226407/artifacts/13413117195).

SEC-020A is accepted as a policy slice only. It does not provision or persist an authority key, implement a user interface, create Android Keystore markers, perform StrongBox runtime validation or connect an enrollment service. No agent executor is connected. The independent security/supervisor gate remains PENDING. M1–M8 milestone states remain unchanged.

**Next bounded task — SEC-020B:** implement the Android Keystore-backed generation watermark and encrypted active-anchor store, then an owner-visible offline import/first-install/rotation/recovery ceremony. The store must fail closed on missing or mismatched markers, survive interrupted commits safely, and be covered by failure-injection tests. Keep all enrollment and execution paths disconnected until independent security approval.


## SEC-020B1 — Android authority trust-store transaction boundary (2026-11-05)

Implemented a bounded storage layer beneath SEC-020A. `OwnerAuthorityTrustStore` serializes transitions, checks first-install/rotation/recovery generation rules, creates the generation marker before encryption/persistence, uses authenticated generation-bound record encryption, atomically replaces the active record, then reopens and verifies it. `AndroidAuthorityTrustCrypto` requests StrongBox-backed HMAC-SHA256 marker keys and AES-256-GCM storage keys and checks `KeyInfo.securityLevel`; no TEE/software fallback is allowed. `AndroidAtomicAuthorityRecordPersistence` uses bounded `AtomicFile` storage in `noBackupFilesDir`. Old marker aliases are retained. If a marker advances but record persistence fails, the old record is not loaded; state becomes recovery-required and the next accepted recovery must advance beyond the marker. Missing marker with an existing record, unavailable Keystore or storage I/O failure fail closed.

This is a storage primitive only. It is not connected to the owner enrollment Activity, does not establish that SEC-020A's confirmation boolean came from a fresh system-credential result, does not provision a production authority, and does not connect enrollment, permission grants or command execution. Marker aliases detect rollback of app-private record data only while the Android Keystore aliases remain; they are not a hardware monotonic counter and do not survive uninstall/factory reset or a compromised OS. Pure-JVM tests use synthetic keys; Android Keystore/StrongBox and Pixel behavior remain unverified. Exact-head CI and independent security review are pending. Keep M1/M6 in progress and all other milestones unchanged; no milestone is complete.

**Next bounded task:** after CI acceptance, SEC-020B2 owner-visible offline import/first-install/rotation/recovery UI, binding the fingerprint comparison to a fresh Android system-credential result. Keep the executor disconnected.


## SEC-020B1 verification update — 2026-11-05

Implementation source head: `e530187404a07425a2e8dc066e024f4b8d982daf`.

**Exact-head workflows:** Phase 1 push `42028301394` PASS; Phase 1 PR `42028312778` PASS; CI-003 push `42028301428` PASS; CI-003 PR `42028312691` PASS; QA-005 PR `42028312811` PASS. Phase 1 reported 380 Python tests passed. The Android Gradle debug unit-test task and debug assembly passed; the workflow log does not publish a per-class JUnit count. The CI-003 independent verifier reported byte-identical unsigned APKs (2,166,373 bytes, 13 entries), APK SHA-256 `b055d54e57717db3f620dbdf997a2960d0a087746107089f3fc470bf70452adf`, normalized entries SHA-256 `b2e594bbc4b8087011de32e3aa6a47275614f699893cf137afbe630ba0fb4c70`, identical runtime inventory SHA-256 `a8a1b16dd1cefb90d14426c477e924a3710c7a160def52a2ece3a6d55c266e44`, and identical SPDX runtime SBOM SHA-256 `d4ea7332864facde8875fbee65ddc68bc1de940c19609760beca147c41e035f6`. Provenance remains `release_ready=false`.

QA-005 passed the disposable x86_64 emulator launcher/recovery, 200% font, HOME consent/cancel, stock-launcher restoration, keyboard focus, structural accessibility and insecure owner-enrollment denial checks. QA-011 reported `blocked_service_disabled`; QA-012 did not test spoken TalkBack. Evidence artifact: `13415725749`. This is emulator validation only, not Pixel 9 Pro hardware validation.

The initial implementation commits exposed two Kotlin compilation issues; these were corrected in follow-up commits before the final `e530187` exact-head workflows passed. The failed intermediate workflow attempts remain in Actions history. Independent security review remains pending. SEC-020B1 is a compiled and CI-tested storage primitive, not a hardware-validated or production-approved trust store. Keep M1/M6 in progress; M7/M8 blocked; no milestone is complete.

**Next gate:** independent security review of marker lifecycle, StrongBox assumptions, AtomicFile semantics, uninstall/rollback boundaries and the unconnected owner-confirmation/execution paths before SEC-020B2 UI integration.


## SEC-020B2 owner-visible offline authority trust ceremony (2026-11-05)

Implemented a bounded Android UI layer over SEC-020A and SEC-020B1:
- Non-exported OwnerAuthorityTrustActivity with no new Android permission.
- Strict canonical Base64 parsing for Ed25519 SPKI DER and optional 64-byte rotation signatures; positive canonical decimal generations; exact uppercase SHA-256 fingerprint comparison.
- Candidate fingerprint preview and explicit owner attestation that the value was compared through a separate trusted out-of-band channel.
- One-shot 30-second monotonic confirmation state bound to the mode, trust-store snapshot and digest of all imported fields.
- Fresh Android system-credential prompt, post-return safety recheck, field reparse, trust-store reinspection and binding comparison before creating a SEC-020A Ready proposal and invoking SEC-020B1 commit.
- Cancellation, Activity destruction, expiry, changed input/state, unavailable/corrupt trust state and failed credential all refuse.
- No network, Android permission grant, remote enrollment, executor, screen capture or device action is connected.

JVM tests use synthetic Ed25519 keys and a fake clock; Python source tests enforce the manifest and code boundaries. These do not prove real Keyguard behavior, StrongBox hardware, AtomicFile crash recovery, TalkBack speech or Pixel 9 Pro compatibility. The checkbox is an owner attestation, not cryptographic proof of the independent fingerprint channel. The Activity currently performs bounded trust-store I/O synchronously; evaluate lifecycle-safe serialized background I/O before production integration.

The exact-head CI gate, emulator QA and independent security review are separate acceptance requirements. M1, M2 and M6 remain IN PROGRESS; M3 remains PARTIAL; M4, M5 and M7 remain NOT STARTED/BLOCKED; M8 remains BLOCKED. No milestone is complete. The upstream shared SKILL.md remains unverified and is not claimed as installed.

## QA-020B2 — owner authority trust UI runtime validation (2026-11-05)

The SEC-020B2 owner-facing Activity was already reachable from MainActivity, but the existing QA-005 emulator workflow did not open it. Added an emulator-only runtime gate that navigates through the launcher, checks the five authority import labels and editable fields, verifies empty-input fingerprint preview refusal, exercises the insecure-device credential preflight (and cancels an unexpected system credential screen without entering credentials), verifies Cancel clears all fields while preserving the trust-state label, and returns to the launcher.

The helper rejects malformed/duplicate/invisible hierarchy targets, unsupported trust states and changed post-cancel state. The script refuses non-emulator serials and requires ro.kernel.qemu=1. It never enters keys, fingerprints, signatures or credentials; never grants permissions or changes the HOME role; and never attempts a successful credential confirmation or trust-store commit.

Exact-head CI/emulator evidence is pending. This is UI runtime coverage only, not StrongBox, Keyguard-success, Pixel 9 Pro, TalkBack speech or independent security acceptance. Keep M1/M2/M6 in progress and all other milestones at their existing verified states; no milestone is complete.


### QA-020B2 runtime harness correction

The first exact-head emulator run reached the owner trust Activity but failed its initial hierarchy assertion because the initial status TextView is below the ScrollView viewport. The captured hierarchy verified the title, trust-state label, all five labels and five edit fields. The helper no longer requires that below-fold status node at initial render; it continues to assert the status after the relevant button actions and checks unchanged trust state after cancellation. A fresh exact-head emulator run is pending.


## QA-020B2 populated-field cancellation correction — 2026-11-05

At branch head 2600e33abb42bdb6ee6361056539c4e6af0f00ca, Phase 1 push/PR and CI-003 push/PR checks passed. QA-005 run 42047955324 passed its launcher, large-font, HOME consent/recovery, keyboard, structural accessibility and insecure-enrollment steps, then failed in QA-020B2's Cancel assertion. The uploaded hierarchy artifact 13425996691 showed that UIAutomator exposes an empty EditText's hint as its text attribute and that only the bottom three fields were in the post-cancel viewport. The Activity source's cancelPending(true) explicitly clears all five fields; no app defect was established.

The corrected emulator harness enters only five fixed invalid dummy strings, verifies all five before Cancel, then scrolls to the top and verifies all five empty-field hints plus unchanged trust state. It does not submit the dummy values to preview/confirmation or trust-store code. Exact-head CI rerun is required. QA-011 remains service-disabled preflight, QA-012 remains structural only, and no physical Pixel/TalkBack speech acceptance is claimed. No milestone is complete; M1/M2/M6 remain IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7 BLOCKED and M8 BLOCKED. Independent security review remains PENDING.


### QA-020B2 snapshot split

The corrected smoke harness captures the Cancel result immediately while the lower status TextView is visible, then scrolls to the top for the five empty-field hints and trust-state comparison. These assertions use separate hierarchy snapshots because the status and all five fields do not share a single scroll viewport.


## Exact-head QA-020B2 acceptance — 2026-11-05

The final QA-020B2 correction at source/test head 9eb814c3a2176f9be552372c5d6f078774edb7dd passed the complete exact-head validation set:

- Phase 1 push run 42051143160 and PR run 42051155411: PASS. Both reported 416 Python tests passed; Android manifest security gate passed; Gradle :app:testDebugUnitTest and :app:assembleDebug passed; repeat debug APK was byte-identical within each runner; strict dependency verification and the modified-artifact negative control passed.
- CI-003 push run 42051143237 and PR run 42051155321: PASS. Independent runners produced byte-identical unsigned APKs (2,196,905 bytes, 13 entries; SHA-256 c58ac03288ff210c03036645ee26e5c70925972b4b7356567c3021b6e6031d1e), identical normalized contents (b11c9f6ab88743d690dfa556f4f086126bbd8a1165aaa02f29c5c81cf718b396), runtime inventory (a8a1b16dd1cefb90d14426c477e924a3710c7a160def52a2ece3a6d55c266e44) and SPDX runtime SBOM (c4d577f316439ed5445e5fd553a01c4eea0c54c135420b416792bbaad07a1b3d). Both verifiers reported reproducible=true and release_ready=false.
- QA-005 disposable x86_64 emulator PR run 42051155383: PASS. QA-005, QA-006 through QA-010, QA-013 and QA-020B2 passed. QA-011 reported blocked_service_disabled (not TalkBack acceptance); QA-012 passed structural semantics only (not spoken TalkBack). QA-020B2 artifact 13426024605 contains the five synthetic invalid field values, separate Cancel-status snapshot and post-cancel empty-hint snapshot. The log records: all five fixed invalid dummy fields were cleared; trust state unchanged; launcher restored.

The original QA-020B2 failure at run 42047955324 was a hierarchy-harness defect, not an application defect: empty EditText nodes expose hints as their UIAutomator text and the lower viewport contained only three fields. The corrected test proved all five fields were populated with fixed invalid test strings, then cleared by Cancel. It did not preview or confirm those values, enter credentials, mutate the trust store, grant permissions or invoke an executor.

This evidence is disposable-emulator-only. It does not establish Pixel 9 Pro StrongBox/Keyguard behavior, physical crash recovery, spoken TalkBack, independent security approval or production readiness. No milestone is complete; M1/M2/M6 remain IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7 BLOCKED and M8 BLOCKED. The upstream shared SKILL.md remains unverified and is not claimed as installed.


## SEC-020B3 — credential-only platform prompt modernization (2026-11-05)

The SEC-020B2 owner confirmation path is being migrated from the deprecated
`createConfirmDeviceCredentialIntent` / Activity-result flow to platform
`BiometricPrompt` with `DEVICE_CREDENTIAL` as the sole allowed authenticator.
API 30+ is required; API 29 fails closed. Callback acceptance checks the
platform-reported authentication type and repeats the device-safety check.
Explicit cancellation and Activity destruction revoke the one-shot binding
before canceling the prompt signal, making late callbacks inert.

Implementation files:
- `OwnerAuthorityTrustActivity.kt`: platform credential-only prompt, callback
  result-type check, CancellationSignal lifecycle.
- `OwnerCredentialAuthenticationPolicy.kt`: pure API/result fail-closed policy.
- `OwnerCredentialAuthenticationPolicyTest.kt`: API/result boundary tests.
- `tests/test_owner_authority_trust_activity_source.py`: source gates for
  credential-only configuration, removal of deprecated flow and cancellation order.
- `docs/SEC-020B3-CREDENTIAL-AUTH.md`: implementation and acceptance contract.

This uses the Android platform API rather than adding AndroidX, so the pinned
Gradle dependency-verification metadata is unchanged. Exact-head CI/emulator
verification is pending. A successful credential prompt is not exercised by
the unsecured disposable emulator. No Pixel 9 Pro, StrongBox or physical
credential test is claimed. Independent security review remains pending.
Keep M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED;
M7 BLOCKED on physical hardware; M8 BLOCKED. No milestone is complete.


## QA-020B3 — device-credential prompt runtime probe (2026-11-05)

The SEC-020B3 production Activity and a debug-only QA probe now share one OwnerCredentialPromptFactory, preventing the test prompt configuration from drifting from production. The probe is protected by android.permission.DUMP, exists only in src/debug, and has no trust-store, permission-grant or executor path. QA-020B3 uses a fixed test-only PIN on the disposable API 35 x86_64 AVD, checks system prompt visibility, cancellation denial and a successful platform-reported DEVICE_CREDENTIAL callback, then clears the PIN in cleanup. It uses ordinary adb shell UID 2000; no root or physical device is involved.

This is not a successful SEC-020B1 StrongBox-backed trust commit and does not prove Pixel 9 Pro compatibility. Exact-head CI and emulator evidence are required. Independent security review remains pending.


## QA-020B3 emulator cancellation correction — 2026-11-05

At source/test head d33b17ca5a35329889ed82f9dfde7bda402dd4b4, Phase 1 push/PR and CI-003 push/PR workflows passed. The Phase 1 PR Python policy suite reported 428 passing tests; Android manifest gate, Gradle unit tests, debug assembly, repeat APK comparison, strict dependency verification and negative control passed. CI-003's two independent release builders and verifier passed. QA-005 emulator run 42067990751 passed all earlier emulator gates and QA-020B2 but failed at QA-020B3 cancellation. The captured hierarchy shows KEYCODE_BACK left SystemUI's credential prompt visible; the test-PIN cleanup succeeded.

The QA-020B3 helper and smoke script now use SystemUI's explicit accessible Tap to cancel authentication background surface. The parser derives a point above the credential panel and refuses ambiguous or unsafe hierarchies. Three regression tests cover safe-point selection and fail-closed cases. Local focused Python tests: 14 passed; shell syntax and Python compilation passed; the captured failure artifact resolves to 540 31. Exact-head GitHub emulator rerun is pending; no runtime pass is claimed.

The earlier QA-020B3 success path did not execute because cancellation failed first. Successful DEVICE_CREDENTIAL callback validation remains unverified until the corrected emulator run passes. No StrongBox-backed trust commit or Pixel 9 Pro validation is established. Independent security review remains pending; no milestone is complete.


## QA-020B3 cancellation-harness correction — 2026-11-06

Audit head: `c92fad5dd8fea0fd5029cd01d14a36fd59924d6d`. Phase 1 push/PR and CI-003 push/PR passed. QA-005 run 42084901826 failed only in QA-020B3 cancellation after a bottom-margin tap at (540,1494) entered one character into the hidden SystemUI keypad; artifact 13442612292 records a bullet in `lockPassword`. The fixed test PIN was not submitted and cleanup succeeded. The old bottom-margin target is withdrawn.

The corrected harness derives a side-gutter point from the actual `lockPassword` field bounds (captured fixture: 133,1033), rejects overlap with clickable SystemUI controls, and verifies that cancellation either dismisses the prompt or leaves the credential field empty. The bottom-margin tap and secure-screen screenshots are removed. Python/parser and shell checks are pending execution; exact-head QA-005 must pass cancellation and successful DEVICE_CREDENTIAL callback before runtime acceptance. M1/M2/M6 remain IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7 BLOCKED, M8 BLOCKED. No milestone is complete.


## QA-020B3 cancellation-signal harness correction — 2026-11-06

At audited branch head 8b875fd23d86df525f17d942b74d684682064de2, Phase 1 push/PR and CI-003 push/PR passed; QA-005 failed only in QA-020B3 cancellation. The credential prompt was visible, but the geometry-derived side-gutter tap did not trigger the prompt-error callback. The post-tap field remained empty and the disposable test PIN cleanup succeeded.

The harness now uses a debug-only DUMP-protected receiver to cancel the probe's active CancellationSignal, then verifies the prompt-error callback, prompt disappearance and subsequent successful test-only DEVICE_CREDENTIAL result. This does not claim a user SystemUI outside-tap interaction test. The receiver is excluded from the main/release manifest and has no trust-store, permission-grant or executor capability. Exact-head emulator rerun remains required. No milestone is complete; M1/M2/M6 remain IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7 BLOCKED and M8 BLOCKED.


## 2026-11-06 — QA-020B3 exact-head acceptance

At branch head 60a7a8162c71a04fb6cc90af7afc68ee33f3f46b, Phase 1 push/PR and CI-003 push/PR all passed. Phase 1 Python policy jobs reported 433 tests passed on each event; Android manifest security, Gradle unit tests, debug assembly, repeat-build comparison, strict dependency verification and modified-artifact negative control passed. CI-003 independent builders and cross-runner verifier passed with reproducible=true and release_ready=false.

QA-005 PR run [42099903280](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42099903280) passed the complete disposable API 35 x86_64 emulator workflow, including QA-020B2 and QA-020B3. The log confirms the debug-only DUMP-protected CancellationSignal receiver produced a prompt-error callback, the subsequent synthetic test PIN returned DEVICE_CREDENTIAL_ACCEPTED, and cleanup completed. QA-011 was blocked_service_disabled; QA-012 was structural only, not spoken TalkBack. This is emulator prompt-runtime evidence, not a trust-store commit, StrongBox test or Pixel 9 Pro validation.

## SEC-020B4 — lifecycle-safe serialized trust-store I/O

OwnerAuthorityTrustActivity now submits all Android Keystore/AtomicFile inspect and commit operations to a process-wide single-thread executor. The main thread captures immutable import material, performs the credential callback and one-shot confirmation check, then posts state updates through a main Handler. The worker reinspects the store, recomputes the snapshot binding and Ready proposal, performs a final application-context device-safety check, and claims a synchronized commit boundary immediately before commit.

The operation gate allows one active transaction, invalidates queued work on cancel or Activity destruction, and rejects a commit claim after invalidation. An already-claimed atomic transaction is allowed to finish; Activity destruction suppresses its UI callback but cannot promise rollback of a transaction that has started. The Cancel/Clear and Return controls do not falsely claim cancellation after this boundary. The executor remains disconnected from permissions and agent execution.

JVM gate tests cover one-operation admission, cancellation-before-commit, destruction-before-commit, claimed-commit semantics, callback suppression and concurrent admission. Python source gates assert off-main serialized I/O and commit-boundary ordering. Exact-head Phase 1/CI-003/QA-005 results are pending for this SEC-020B4 commit.

Milestones remain: M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Independent security review, Pixel 9 Pro StrongBox/Keyguard validation, physical AtomicFile interruption/recovery, spoken TalkBack, permission-bound agent execution, signed OTA and production release evidence remain outstanding.


## 2026-11-06 — SEC-020B4A worker serialization and race coverage

Audit baseline: `feat/phase1-agentic-phone` at `e03abc313ce322d02767a1c3edba181a4503f5d0`; complete recursive tree contained 254 entries and was not truncated. The branch history, all six open PRs, PR #1 metadata/reviews/threads, architecture, CI workflows and local factory instructions were inspected. `PROJECT-ADAPTER.md` and this roadmap exist; no repository `SKILL.md` was found. The upstream shared factory package remains unverified and is not claimed as installed.

At the audit baseline, exact-head Phase 1 push/PR runs [42106200791](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42106200791) and [42106210110](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42106210110) passed. Both Python policy jobs reported 434 passing tests; both Android jobs passed `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat debug APK comparison, strict dependency verification and the modified-dependency negative control. CI-003 push/PR [42106200917](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42106200917) and [42106210057](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42106210057) passed on two independent builders plus the cross-runner verifier. QA-005 PR [42106210007](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42106210007) passed its API 35 x86_64 emulator suite through QA-020B2 and QA-020B3; it does not exercise SEC-020B4 trust-store I/O. QA-011 remains availability-only and QA-012 structural-only, not spoken TalkBack acceptance.

SEC-020B4A adds a dedicated-worker serialization test, a cancel-versus-commit-claim race test and stale-token isolation coverage. These are JVM-level tests; they do not prove Android Keystore/StrongBox behavior, Activity instrumentation or physical crash recovery. Exact-head validation for the new commit must be read from its own Actions runs before acceptance.

Milestones remain M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Independent security review, Pixel 9 Pro hardware validation, spoken TalkBack, supervised permission-bound execution, signed OTA and production release remain open.


## 2026-11-06 — SEC-020B4B static capability-boundary gates

Audit baseline: `feat/phase1-agentic-phone` at `9fb8cd96fb5f1702efde0a5822a9c527e5a62189`. The complete recursive Git tree contained 255 entries and was not truncated. The latest 12 commits, all six open PRs (#1 and #3–#7), PR #1 base/head/draft metadata, review submissions, inline threads, current Actions runs, Android architecture, tests and factory instructions were inspected. `PROJECT-ADAPTER.md` and this roadmap are present; no repository `SKILL.md` exists. The upstream shared factory package remains unverified and is not claimed as installed.

At this head, Phase 1 push/PR runs [42114572656](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42114572656) and [42114577672](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42114577672) passed both Android and Python-policy jobs. CI-003 push/PR runs [42114570655](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42114570655) and [42114577773](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42114577773) passed both independent builders and the cross-runner verifier. QA-005 PR run [42114577671](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42114577671) passed its disposable API 35 x86_64 emulator workflow, including launcher/recovery, QA-006–QA-013, SEC-020B2 and QA-020B3. The log confirms QA-020B2 cleared all five fixed invalid dummy fields without changing trust state and QA-020B3 observed cancellation callback plus a test-only DEVICE_CREDENTIAL result. QA-005 does not exercise SEC-020B4 Android worker/Activity lifecycle. QA-011 is availability-only; QA-012 is structural-only, not spoken TalkBack acceptance.

SEC-020B4B extends the existing SEC-020B3/B4 source gate rather than duplicating it. It checks the complete owner trust I/O path for direct agent/command routing, permission-grant, screen/accessibility, device-control, telephony, camera/microphone, network and arbitrary process-execution APIs. It also verifies that the debug credential probe and cancellation receiver are absent from the main manifest and are the only debug components, each explicitly protected by `android.permission.DUMP`. No production capability, permission, executor connection, trust mutation or device integration is added.

PR #1 remains open and draft against `main`; the base remains `f3c9a701d2a337de8ef393ac14df044a79843d60`. It has no submitted review or inline review threads. The branch object reports unprotected; the explicit branch-protection endpoint is not accessible to this integration (HTTP 403), and the repository rulesets endpoint returned an empty list. Other worker PRs/branches remain untouched.

Milestones remain M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Independent security review, Pixel 9 Pro StrongBox/Keyguard, physical AtomicFile recovery, spoken TalkBack, permission-bound agent execution, signed OTA and production release evidence remain outstanding.


## CI-004 Gradle-merged release manifest security gate — 2026-11-06

The source-manifest policy and debug-manifest regression tests did not prove the actual release variant's merged manifest. CI-003 now runs scripts/release_manifest_gate.py after :app:assembleRelease on both independent builders. The gate fails closed on missing/ambiguous AGP output; checks reviewed permissions, backup/cleartext/debug flags, exported components, MAIN/HOME/DEFAULT and MAIN/LAUNCHER filters, shared UID, instrumentation and debug credential probe leakage; emits a deterministic manifest SHA-256 report; and compares that report across runner A and B.

Sixteen focused local unit tests passed before submission, including negative controls and a workflow-order regression. The checked-in main source manifest also passes the existing source gate. Exact-head CI-003 is still required to prove the selected AGP 8.7.3 output path and actual merged release manifest. This does not decode the final binary APK manifest, establish runtime capability absence, sign an artifact or establish release readiness. Keep M1/M6 in progress and M8 blocked; no milestone is complete. Independent security review remains pending.


## 2026-11-06 — CI-004B packaged APK binary manifest verification

Audit baseline: feat/phase1-agentic-phone at bfa3c8c1801c39ee48ac72d82c03a36c04d02d74. The complete recursive tree contained 258 entries and was not truncated. The latest 12 commits, all six open PRs, PR #1 metadata/reviews/threads, exact-head Actions runs, architecture, tests, CI-003, CI-004 and factory instructions were inspected. The local project adapter and roadmap exist; no repository SKILL.md exists. The upstream shared factory package remains unverified and is not claimed as installed.

The CI-004 baseline is accepted at bfa3c8c1: Phase 1 push/PR both passed with 452 Python tests each and Android unit/build/dependency checks; CI-003 push/PR passed both independent release builders and the cross-runner verifier; QA-005 PR passed its disposable API 35 x86_64 emulator suite through QA-020B3. The merged release manifest policy passed on both CI-003 builders with SHA-256 ae826c71392597b85c6c412dc6bcfa8c549c846f5be074b1eb5a5bb65129c071. QA-011 and QA-012 are not spoken TalkBack acceptance. No physical Pixel 9 Pro test occurred.

CI-004B adds a second release-manifest gate after :app:assembleRelease. It decodes the binary manifest from the final unsigned APK using the SDK Command-Line Tools apkanalyzer manifest print, validates the packaged application ID, re-runs the release policy against merged and packaged XML, and compares a deterministic security projection (permissions, package identity, SDK bounds, application/component access attributes, intent filters, queries and provider access rules). Relative class names are normalized; presentation-only labels/icons/themes are excluded. The report records raw and policy hashes plus decoder revision, is included in both CI-003 artifacts and SHA256SUMS, and is byte-compared across independent runners. The existing CI-004 policy now rejects unknown uses-permission-* declaration forms.

New tests cover identical manifests, class-name normalization, presentation-only changes, injected permissions/components, intent-filter and cleartext changes, package mismatch/missing package, malformed XML, deterministic reports and workflow ordering. The existing CI-004 tests add an unsupported permission-tag negative control. Exact-head Phase 1/CI-003/QA-005 runs are required before acceptance. This does not inspect DEX/native runtime capability, validate actual permission behavior, test Pixel hardware, sign artifacts or establish release readiness.

PR #1 remains open/draft/unreviewed against main. No other worker PR or branch was modified. No app behavior, runtime permission, trust record, device setting, signing key, agent executor or physical device was changed. Independent security review remains pending. Milestones remain M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete.


### CI-004B first exact-head test correction — 2026-11-06

The first exact-head Phase 1 push and PR Python-policy jobs each discovered 466 tests: 465 passed and one workflow-source assertion errored. The assertion searched for the literal text "apkanalyzer manifest print", while the workflow correctly invokes the pinned-path variable as "$APKANALYZER" manifest print "$APK". The Android source/build jobs and CI-003 release builders were still running at the time of diagnosis; no APK decoder result is claimed from that attempt. The test was corrected to assert the actual explicit variable invocation and its APK argument. Exact-head reruns are required. This was a test expectation mismatch, not a release-manifest or application-code failure.


## Audit and implementation update — 2026-11-06, CI-004C Gradle-derived release identity

The authorized branch was audited at `1b4909e54b56cbf3c6573abf03c6de6002fb1fb3`. The complete recursive tree contained 261 entries and was not truncated. The latest 12 commits, six open PRs (#1 and #3–#7), PR #1 metadata/reviews/threads, exact-head Actions runs, Android/Kotlin/Python architecture, Gradle configuration, CI-003 workflow, CI-004/CI-004B gates, tests and factory instructions were inspected. `PROJECT-ADAPTER.md` and this roadmap are present; no repository `SKILL.md` exists. The authorized Library search recorded earlier found no upstream shared package; it remains unverified and is not claimed as installed.

At `1b4909e5`, Phase 1 push/PR, CI-003 push/PR and QA-005 PR all completed successfully. Phase 1 reported 466 Python tests on push and PR, Android debug unit/build and dependency-verification checks passed, CI-003 produced matching unsigned APK/SBOM/provenance and merged/packaged manifest reports across two builders, and QA-005 passed on a disposable API 35 x86_64 emulator. The CI-004B first attempt at `f645323e` had one Python workflow-source assertion mismatch (465/466); the assertion was corrected in `1b4909e5`, whose exact-head runs all passed. The prior CI-004B workflow links are recorded in the section above.

CI-004C removes the hard-coded `tech.mrnothing.os` expectation from the release workflow. AGP's Android Components API selects the single release variant and writes deterministic `release-variant-metadata.json` using the resolved `variant.applicationId`. The Gradle task fails closed if more than one release variant appears or the selected variant is not the unflavored `release` variant. A strict Python reader rejects missing, symlinked, oversized, malformed, duplicate-key, unknown-field, invalid-package and non-release metadata. The packaged APK gate validates both merged and packaged manifest package IDs against this Gradle-derived identity. CI-003 includes the metadata in each runner artifact and checksum inventory, records its identity and SHA-256 in provenance schema v2, validates the metadata against provenance on both bundles, and byte-compares it across independent runners. Negative controls cover a mismatched Gradle-derived ID, non-release variant, invalid ID, duplicate metadata keys and metadata tampering after provenance generation.

This is a build identity/provenance gate only. It does not change the application ID or Android runtime behavior, sign the APK, inspect DEX/native runtime capabilities, validate hardware-backed keys, test a physical Pixel 9 Pro or establish production readiness. Exact-head Phase 1, CI-003 and QA-005 workflows remain the acceptance gates for this commit. PR #1 remains open/draft/unreviewed against main. No other worker PR/branch was modified; main is unchanged; no force-push, merge, physical flashing, root escalation, production signing or deployment occurred.

Milestones remain M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Independent security review, Pixel 9 Pro StrongBox/Keyguard and physical recovery, spoken TalkBack, supervised permission-bound execution, signed OTA and production release remain open.

## 2026-11-06 — CI-006 scoped build-environment SBOM (implementation submitted)

Audit baseline: `feat/phase1-agentic-phone` at `851c98c160565146952663a19c1418a4a007303a`. The complete recursive tree contained 263 entries and was not truncated. The latest 12 commits, all six open PRs (#1 and #3–#7), PR #1 base/head/draft metadata and review submissions, current exact-head check runs, CI workflow definitions, Android/Gradle architecture, Python test suite, CI-003 runtime SBOM/provenance and factory instructions were inspected. `PROJECT-ADAPTER.md` and this roadmap are present; root `SKILL.md` returns 404. The upstream shared factory package remains unverified and is not claimed as installed.

At the audit baseline, Phase 1 push [42144929657](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42144929657) and PR [42144935781](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42144935781) both passed. Each Python-policy job ran 472 tests; Android unit tests, debug assembly, repeat-build comparison, strict dependency verification and modified-dependency negative control passed. CI-003 push [42144929615](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42144929615) and PR [42144935837](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42144935837) passed both independent release builders and cross-runner verification. QA-005 PR [42144935779](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42144935779) completed its API 35 x86_64 emulator smoke workflow, including launcher/recovery, large font, HOME consent/cancel/restore, keyboard focus, read-only TalkBack availability, structural accessibility, insecure enrollment denial, QA-020B2 trust UI and QA-020B3 credential prompt. QA-011 is availability-only and QA-012 structural-only; neither is spoken TalkBack acceptance. No physical Pixel 9 Pro test occurred.

CI-003's existing SPDX-2.3 SBOM inventories only `releaseRuntimeClasspath`; provenance records selected top-level toolchain values but does not provide a package-level build-environment SBOM. This run adds `scripts/build_environment_sbom.py`, `tests/test_build_environment_sbom.py` (17 tests), and `docs/CI-006-BUILD-ENVIRONMENT-SBOM.md`. The script inventories installed dpkg packages, pip packages, Android SDK packages, the checksum-verified Gradle distribution, actual JDK/Python runtime versions, direct AGP/Kotlin plugin declarations, and immutable GitHub Action commit references. It captures hosted runner image identity and OS release metadata. It emits deterministic inventory JSON plus SPDX-2.3; the SPDX namespace binds the inventory SHA-256. Provenance v2 is extended with inventory/SBOM filenames and digests. A negative control proves that a mutable GitHub Action tag is rejected. The CI-003 verifier checks both runner bundles and requires byte-identical inventory/SBOM plus matching runner and toolchain identities.

**Scope limitation:** this is a scoped build-environment SBOM, not a complete hosted-runner image SBOM. It does not enumerate every GitHub toolcache file, every transitive Gradle plugin-resolution dependency or every file in each Android SDK package. The runtime SBOM remains separate. Exact-head Phase 1/CI-003 results for the new implementation are pending; do not mark CI-006 accepted until both push/PR paths and the independent verifier pass.

This change modifies CI inventory, provenance and tests only. It does not change Android runtime behavior, permissions, owner trust state, agent execution, device settings or release signing. PR #1 remains open/draft/unreviewed against `main`; no other worker PR/branch is modified. No production signing, deployment, root escalation, flashing, bootloader unlock or merge occurs.

Milestones remain M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Independent security review, spoken TalkBack, physical Pixel 9 Pro/StrongBox/Keyguard and recovery validation, permission-bound agent execution, signed OTA and production release evidence remain outstanding.


## 2026-11-06 — CI-006A canonical SPDX integrity gate

Audit baseline: feat/phase1-agentic-phone at 43a8aab3be49f0bbb8ecc602f47472b694f28181; the complete recursive tree contained 266 entries and was not truncated. The 12 latest feature-branch commits, all six open PRs (#1 and #3–#7), PR #1 head/base/draft metadata and review state, exact-head Actions runs, CI-003 workflow/artifacts, build-environment inventory generator/tests, Gradle configuration, Android architecture and factory instructions were inspected. PROJECT-ADAPTER.md and this roadmap are present; no repository SKILL.md exists. The upstream shared factory package remains unverified and is not claimed as installed.

At the audit baseline, Phase 1 push [42153225573](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42153225573) and PR [42153231220](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42153231220) passed. Both Python-policy jobs ran 490 tests; Android unit tests, debug assembly, repeat-build comparison, strict dependency verification and the modified-dependency negative control passed. CI-003 push [42153225473](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42153225473) and PR [42153231137](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42153231137) passed both independent release builders and the verifier. Each builder inventoried 1,260 components; the inventory SHA-256 was 8a63fef27a510d79ecd58828c9962397d6faf7bfd4c47fe034437cf787cfa790, and the SPDX SHA-256 was d9a39f72e0eda71c2844a7320d954f6e18570e962c648ba0b2aa28f2fd4c818b. The verifier reported build_environment_identical=true, with inventory, SPDX, runner identity and toolchain checks all true. The unsigned APK remained reproducible and release_ready=false.

QA-005 PR [42153231120](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42153231120) had booted the disposable API 35 x86_64 emulator and passed launcher/recovery, QA-006 through QA-011 at the latest inspection; QA-012, QA-013 and QA-020B2/B3 were still running. No complete QA-005 pass is claimed from this run. QA-011 is availability-only and QA-012 structural-only, not spoken TalkBack acceptance.

The independent source review of CI-006 found that the previous validator compared package-URL sets and selected checksums but did not require a one-to-one canonical SPDX package/relationship graph. A duplicate package record or tampered package name/version/relationship could therefore survive the set comparison. CI-006A hardens validate_inventory_and_sbom: validates component records, unique package URLs, lowercase digest shape, canonical ordering and exact counts, then regenerates the canonical SPDX document from the inventory and requires full JSON object equality. Five adversarial regression tests cover duplicate SPDX packages, package metadata tampering, relationship tampering, duplicate inventory PURLs and inconsistent counts. The generator and existing inventory scope are unchanged.

Acceptance status: CI-006 build-environment inventory/SBOM and two-runner equality are verified at the audit baseline. CI-006A implementation is submitted at the new commit; its exact-head Phase 1 and CI-003 push/PR workflows are pending and must pass before CI-006A is accepted. Independent security review remains pending. PR #1 remains open/draft against unchanged main, with zero reviews and zero inline threads. No other worker branch was modified. No physical Pixel 9 Pro, StrongBox, spoken TalkBack, production signing, OTA, deployment, root escalation or main merge is claimed or performed.

Milestones remain M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete.


### CI-006A fixture correction

The first submitted CI-006A commit over-escaped the Python date-regex and JSON fixture newline literals while generating the patch. The follow-up corrects the date regex to match the canonical UTC timestamp and writes real newline terminators in all five adversarial fixtures. No generator, inventory schema, workflow or Android runtime behavior changed. The corrected exact-head Phase 1/CI-003 runs are the acceptance evidence.


### CI-006A assertion correction

The first exact-head CI-006A run executed 495 tests and exposed one stale assertion message in the existing tampered-inventory test. The canonical SPDX validator rejected the modified inventory before the old namespace/hash-specific assertion text, so the implementation failed closed but the test expected only the previous wording. The assertion now accepts the new canonical-document rejection message as well. No production code or policy was weakened.


## 2026-11-06 — SEC-020B4C Android Activity lifecycle instrumentation

Audit baseline: `feat/phase1-agentic-phone` at `1aa9d1247a46d8542a0f6c97828b151b2362b945`. The complete recursive tree contained 266 entries and was not truncated. The latest 12 feature-branch commits, all six open PRs (#1 and #3–#7), PR #1 metadata/reviews/threads, exact-head push/PR workflows, Android/Kotlin/Python architecture, QA-005 harness, CI-003, CI-004/004B/004C, CI-006/006A, tests and factory instructions were inspected. `PROJECT-ADAPTER.md` and this roadmap exist; repository `SKILL.md` is absent (404). The upstream shared package remains unverified and is not claimed as installed.

At the audit head, Phase 1 push [42154563471](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42154563471) and PR [42154570681](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42154570681) passed; each Python-policy job ran 495 tests and Android unit/build/dependency checks passed. CI-003 push [42154563436](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42154563436) and PR [42154570509](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42154570509) passed both independent builders and the cross-runner verifier. QA-005 PR [42154570639](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42154570639) completed successfully on a disposable API 35 x86_64 emulator, including launcher/recovery, QA-006–QA-013 and QA-020B2/B3. QA-011 remains availability-only and QA-012 structural-only, not spoken TalkBack acceptance. No physical Pixel 9 Pro was tested.

The existing SEC-020B4 JVM tests verified the operation gate and dedicated single-thread worker in isolation, but QA-005 did not exercise the real Activity `onDestroy()` hook while initial trust inspection was queued. This run adds `android/app/src/androidTest/java/tech/mrnothing/os/OwnerAuthorityTrustActivityLifecycleTest.kt`, configures the platform `android.test.InstrumentationTestRunner`, and inserts `:app:connectedDebugAndroidTest` into QA-005 after emulator boot. The test occupies the I/O worker with a bounded latch, launches the actual non-exported owner trust Activity, reads its active operation token, finishes the Activity on the main thread, verifies `onDestroy()` invalidates and makes the token non-deliverable, releases the worker, and waits for a FIFO sentinel. The queued trust inspection must return at its initial active-token guard before creating/inspecting the Android trust store.

No external test dependency, production capability, Android permission, manifest component, owner credential, trust mutation, executor connection or device integration is added. The test uses reflection only to read private lifecycle-gate state. It exercises queued-work invalidation on the emulator, not an in-flight StrongBox/AtomicFile commit, physical Pixel 9 Pro behavior, actual Keyguard cancellation, crash recovery or spoken TalkBack. Exact-head Phase 1, CI-003 and QA-005 workflows are required before acceptance. Independent security review remains pending.

PR #1 remains open/draft against unchanged main; no submitted reviews or inline threads exist. PRs #3–#7 remain open/draft on their existing branches and were not modified. No root escalation, physical flashing, production signing, deployment, force-push or merge occurred.

Milestones remain M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete.


### SEC-020B4C exact-head compile failure and correction

At implementation head `dc04fd0ef7ff7dfead94f858a1ea0f7ba272ccca`, Phase 1 push [42157621224](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42157621224) and PR [42157629227](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42157629227) both passed. Each Python-policy job ran 495 tests; Android unit tests, debug assembly, repeat APK comparison, strict dependency verification and the modified-dependency negative control passed. CI-003 push [42157621114](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42157621114) and PR [42157629260](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42157629260) both passed independent builders and cross-runner verification. Both builders produced byte-identical unsigned APKs (2,208,505 bytes; SHA-256 `1a1212a717ed35fb014726f5446871eb179efb5f73bc6fb7caa7d2c8d37a0ce7`), identical runtime inventory and SPDX SBOM, and identical scoped build-environment inventory (1,260 components). CI-003 reports `reproducible=true` and `release_ready=false`.

QA-005 PR [42157629137](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42157629137) successfully built the debug APK, passed the modified-dependency negative control, and booted the disposable API 35 x86_64 emulator. It then failed at `:app:compileDebugAndroidTestKotlin`: the optional `android.test` package was not on the default compile classpath, producing unresolved references to `InstrumentationTestCase`, assertions and `getInstrumentation()`. No instrumentation test executed. This is a test-classpath failure; the Android application debug build and CI-003 release builders passed.

The correction adds API-35 SDK optional `android.test.base.jar` and `android.test.runner.jar` as `androidTestCompileOnly` files with explicit presence checks. They are not packaged into the app or test APK; no external Maven dependency or main/release manifest entry is added. Two Python regression tests now enforce the QA step ordering and compile-only boundary. Exact-head push/PR and QA-005 reruns are required before SEC-020B4C acceptance.


### SEC-020B4C lifecycle assertion correction — 2026-11-06

At `554d19ff7e2055b3d621eada78272ed4cf919e21`, Phase 1 push [42158210891](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42158210891) and PR [42158216850](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42158216850) both passed: each Python-policy suite ran 497 tests; Android unit tests, debug assembly, repeat debug APK comparison, strict dependency verification and modified-dependency negative control passed. CI-003 push [42158210851](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42158210851) and PR [42158216867](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42158216867) both passed independent builders and cross-runner verification. Both verifiers reported byte-identical unsigned APKs, `reproducible=true`, `release_ready=false`, and identical scoped 1,260-component build-environment inventories.

QA-005 PR [42158217053](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42158217053) built the debug APK, passed the modified-dependency negative control, booted the API 35 x86_64 emulator, compiled the instrumentation test using compile-only platform test jars, and launched `OwnerAuthorityTrustActivityLifecycleTest`. The test failed because it asserted `Activity.isDestroyed` immediately after calling `finish()`; Android dispatches destruction asynchronously. The test did not demonstrate a production defect. It is corrected to wait up to five seconds for `Application.ActivityLifecycleCallbacks.onActivityDestroyed` on the exact Activity instance, then assert destroyed state and gate invalidation. The observer and worker are cleaned up in `finally`. Exact-head QA-005 rerun remains required; SEC-020B4C is not yet accepted.


## SEC-020B4D — in-flight trust transaction lifecycle (2026-11-06)

Added API-35 emulator instrumentation for the actual OwnerAuthorityTrustActivity commit boundary using a debug-only non-exported host and an in-memory fake OwnerAuthorityTrustStorePort:

- Destruction during final trust-state inspection, before `claimCommit()`, must prevent any fake-store mutation.
- Destruction while fake `commit()` is blocked after `claimCommit()` must not pretend to roll back the already-authorized transaction; exactly one fake commit may finish, while the destroyed Activity receives no result callback.
- Each case uses a synthetic Ed25519 authority and reuses a disposable emulator-only PIN provisioned and cleared by the QA-005 workflow's ordinary ADB-shell cleanup trap to exercise the platform DEVICE_CREDENTIAL callback. No real trust material, Keystore/StrongBox, AtomicFile, permissions, agent execution or physical device is involved.

This is a lifecycle-boundary test, not evidence of physical StrongBox/AtomicFile crash consistency. Exact-head CI and emulator results are required before acceptance; independent security review remains pending.


## SEC-020B4D — Android Ed25519 provider compatibility correction (2026-11-06)

The API-35 emulator exposed that the platform-default Ed25519 KeyFactory did not import the external synthetic owner SPKI. The first SEC-020B4D attempt therefore failed before its commit-boundary assertions; it is not accepted. The correction pins Bouncy Castle `bcprov-jdk18on:1.86`, records JAR/POM SHA-256 values in Gradle dependency verification, and passes an explicit provider instance to Ed25519 KeyFactory and Signature. No process-wide provider registration is permitted. The JVM regression test covers an RFC 8032 public-key fingerprint, provider-registry invariance, and existing cross-provider rotation-signature tests. Exact-head CI and emulator reruns are required before acceptance. This provider is software cryptography, not Android Keystore or StrongBox.



## SEC-020B4D — emulator interactive/unlocked preflight correction (2026-11-06)

At audited head `30fea42e61330b7ec283a5aa6bbc346e6e44213b`, Phase 1 push/PR passed (505 Python tests each; Android unit tests, debug assembly, repeat debug APK comparison, strict dependency verification and dependency negative control passed). CI-003 push/PR passed both independent release builders and cross-runner verification. QA-005 run [42167072675](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42167072675) booted the API-35 x86_64 emulator and compiled the instrumentation suite, but both SEC-020B4D tests failed before commit-boundary assertions with `credential confirmation was not initiated`; all later QA steps were skipped. This is a failed QA gate, not a pass.

The test harness now explicitly wakes the disposable emulator and checks the real KeyguardManager, UserManager and PowerManager state before launching the Activity. If the device is actually locked, it requires the visible `com.android.systemui:id/lockPassword` field before entering only the synthetic emulator PIN. It then waits for `OwnerCredentialSafetyGate.isSafe` (secure, unlocked, user-unlocked and interactive). If confirmation still does not begin, the failure reports the Activity status and device-credential availability plus safety signals. It does not call a keyguard-dismiss bypass or enter credentials into app-owned controls. The production DEVICE_CREDENTIAL-only BiometricPrompt factory remains unchanged.

Exact-head Phase 1, CI-003 and QA-005 reruns are required. SEC-020B4D remains unaccepted until both commit-boundary tests pass. No real trust material, production credential, StrongBox, AtomicFile, permission, executor, physical Pixel, production signing or deployment is involved. Independent human security review remains pending; upstream shared `SKILL.md` remains unverified.


## SEC-020B4D exact-head QA failure analysis and diagnostic correction — 2026-11-06

At branch head 2299b723621f654bb3782f8fa0371a13f8b37122, Phase 1 push [42168597642](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168597642) and PR [42168602224](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168602224) passed; each Python suite ran 506 tests, and Android debug unit/build/dependency checks passed. CI-003 push [42168597742](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168597742) and PR [42168602103](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168602103) passed independent builders and cross-runner verification. QA-005 [42168602258](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168602258) booted the disposable API 35 emulator, compiled instrumentation, and began the after-commit-claim test; that test failed, and later QA steps were skipped. The uploaded diagnostics did not include the AndroidJUnitRunner XML/HTML result bundle, and the 300-line logcat tail did not expose the assertion cause. SEC-020B4D remains unaccepted.

The next correction broadens credential UI detection to inspect accessible Android windows and recognize the known auth_credential_input and lockPassword fields only when hosted by com.android.systemui or com.android.settings. The test now waits for the Activity's explicit final-revalidation status after submitting the synthetic emulator PIN, then reports the Activity status and both boundary latch states if the fake backend is not reached. This narrows the failure signal between system credential UI detection, credential callback acceptance and the trust I/O boundary; it does not relax credential-only authentication or the device safety gate.

The QA-005 always-run evidence step now preserves Android connected-test XML/HTML reports from both Gradle report/output locations and captures a larger 2,000-line all-buffer logcat tail. These diagnostics are needed to distinguish a test assertion from an instrumentation-process crash. No production credential, trust mutation, Android permission, agent execution, privileged shell, physical device or production release is involved. Exact-head Phase 1, CI-003 and QA-005 reruns remain required; upstream shared SKILL.md remains unverified and is not claimed as installed.


## SEC-020B4D — Android 15 Keyguard PIN selector correction

Audit baseline: `23993daed4e213b95cda115ca8700b4b92211174`; recursive tree 276 entries, not truncated; 15 latest branch commits and all six open PRs inspected. `PROJECT-ADAPTER.md` and roadmap exist; repository `SKILL.md` absent; upstream shared package remains unverified.

**Failure evidence:** QA-005 [42174961897](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42174961897) built the debug APK, passed the dependency negative control, booted API 35 emulator and compiled instrumentation. Both SEC-020B4D cases then failed before trust transaction boundaries because the lockscreen PIN field was not recognized. The assertion's safety signals were secure=true, deviceLocked=true, keyguardLocked=true, userUnlocked=true, interactive=true and deviceCredentialCanAuthenticate=0. Subsequent QA steps were skipped. This was a selector mismatch, not evidence that the trust-store commit gate itself failed.

**Verified root cause:** Android 15 AOSP `keyguard_pin_view.xml` declares `pinEntry` as `com.android.keyguard.PasswordTextView`, not EditText; `keyguard_password_view.xml` declares `passwordEntry` as EditText. The previous detector knew only the BiometricPrompt-oriented IDs and required EditText for every candidate.

**Implementation:** add exact SystemUI selectors for `pinEntry/PasswordTextView` and `passwordEntry/EditText`, retaining `auth_credential_input/EditText` and `lockPassword/EditText`. Continue requiring visible nodes in `com.android.systemui` or `com.android.settings`. Add a Python source regression for the exact ID/class pairs and package restriction. No app-owned input or Keyguard bypass is allowed.

**Acceptance:** both SEC-020B4D instrumentation tests must reach their intended pre-claim and post-claim boundaries; both Phase 1 push/PR and CI-003 push/PR must pass at the same commit; QA-005 must complete all remaining checks; synthetic PIN cleanup must succeed. Until then SEC-020B4D is NOT ACCEPTED. No real trust mutation, StrongBox/AtomicFile hardware claim, physical Pixel 9 Pro, production signing or deployment is claimed. Independent human security review remains pending.

Milestones unchanged: M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED.


## SEC-020B4D — API 35 lockscreen PIN-pad reveal correction (2026-11-06)

**Audit baseline:** feature branch head `e8d255c24db2670adec78d5dc3d505acedc9c29c`; recursive tree 276 entries, not truncated; 12 latest branch commits and six open PRs (#1, #3–#7) inspected. Project adapter and roadmap exist; repository SKILL.md absent; upstream shared package unverified.

**Exact-head evidence:** Phase 1 push/PR [42181487968](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181487968) / [42181494281](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181494281) passed; each Python policy suite ran 508 tests, Android jobs passed. CI-003 push/PR [42181488047](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181488047) / [42181494488](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181494488) passed both builders and independent verification. QA-005 [42181494325](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181494325) failed both SEC-020B4D commit-boundary tests before prompt display; the queued-inspection lifecycle test passed. JUnit evidence reports secure=true, deviceLocked=true, keyguardLocked=true, interactive=true, deviceCredentialCanAuthenticate=0 and no visible SystemUI PIN field. The synthetic PIN cleanup succeeded. Later QA steps were skipped.

**Implementation:** the lockscreen preflight previously woke the emulator and immediately searched for the credential input. Add a bounded, display-relative swipe-up using UiAutomation only when Keyguard is locked and the exact SystemUI credential field is not already visible. Continue requiring the exact system package, resource ID, visible state and expected Android view class before entering the synthetic PIN. Inject ACTION_CANCEL on a partial gesture failure. This is a test-only gesture to reveal the platform PIN pad, not a Keyguard dismissal or authentication bypass.

**Acceptance:** both SEC-020B4D commit-boundary tests and the complete QA-005 sequence must pass on the new exact head; synthetic PIN cleanup must succeed. Exact-head Phase 1 push/PR and CI-003 push/PR must pass. SEC-020B4D remains NOT ACCEPTED until then. M1/M2/M6 remain in progress; M3 partial; M4 not started; M5 not accepted; M7/M8 blocked. No physical Pixel 9 Pro, StrongBox, production signing, deployment or independent security approval is claimed.


## SEC-020B4D — Android input-utility swipe correction (2026-11-06)

**Baseline:** commit `34b34e1da3158c5c0497142de92391295f8b31a7`; recursive tree 276 entries, complete. Phase 1 push/PR [42183555613](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183555613) / [42183562415](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183562415) passed (509 Python tests each; Android unit/build passed). CI-003 push/PR [42183555609](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183555609) / [42183562507](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183562507) passed independent reproducibility. Unsigned APK SHA-256 `3c09c4b4c7956cb7e2a90fdc96c9ab909f53f4526c8439ed25b0aae78c49f1ea`; normalized-entry SHA-256 `9e6c4b9489af0f8b07f1d5fdae1d2ac6746041686d84fded9c0cecd4ddbc97d1`; scoped environment inventory 1,260 components; release_ready=false.

**Failure:** QA-005 [42183562453](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183562453) passed emulator boot and the queued-Activity lifecycle test, but both commit-boundary cases failed before prompt display. A display-relative `UiAutomation.injectInputEvent` swipe was accepted yet no visible SystemUI PIN field appeared. Synthetic PIN cleanup succeeded; later QA steps were skipped. Artifact [13486851509](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183562453/artifacts/13486851509).

**Correction:** use the Android `input swipe` utility only after verifying the test shell identity is `uid=2000(shell)`; calculate coordinates from display metrics; swipe only when Keyguard is locked and no exact SystemUI credential field is already visible. Keep exact package/resource-ID/class/visibility validation before synthetic PIN entry. This is an unprivileged user-gesture simulation, not Keyguard dismissal or authentication.

**Acceptance:** exact-head Phase 1, CI-003 and full QA-005 must pass; both commit-boundary cases must reach their fake-store assertions; synthetic PIN cleanup must succeed. SEC-020B4D remains NOT ACCEPTED. Milestones unchanged: M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7/M8 BLOCKED. No physical Pixel 9 Pro, production signing, deployment or independent human security approval is claimed.


## SEC-020B4D — bounded credential UI diagnostics (2026-11-06)

**Baseline:** `e5a313ac6c942b982739294e097daa90c6eadcf4`. Phase 1 push/PR [42184476741](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184476741) / [42184482244](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482244) passed (509 Python tests each; Android checks passed). CI-003 push/PR [42184476880](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184476880) / [42184482249](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482249) passed independent reproducibility.

**Failure:** QA-005 [42184482208](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482208) passed emulator boot and queued-Activity destruction, but both commit-boundary tests failed before prompt display after an unprivileged shell swipe. PIN cleanup succeeded; later QA steps were skipped. Artifact [13487605359](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482208/artifacts/13487605359).

**Next task:** diagnostics only. Capture a bounded UiAutomation window/accessibility node snapshot (80 nodes/9 KB), filtered `dumpsys window windows` focus summary, and shell identity/display/swipe coordinates on failure. Recycle all AccessibilityNodeInfo instances. Do not add further input gestures until evidence shows whether the lockscreen root is visible and what window owns focus. SEC-020B4D remains NOT ACCEPTED; all prior milestone states remain unchanged.


## Engineering Factory update — QA-005 startup ANR and source-gate correction (2026-11-06)

**Audit baseline:** branch `feat/phase1-agentic-phone`, commit `a8b38e9cd84c5f396251b0acbd7e7895327567fb`; recursive Git tree `4d75266fa9c959f8325af4f1e8546c462c65d950` is complete (276 entries, not truncated). The PR audit found six open PRs (#1 and #3–#7). `PROJECT-ADAPTER.md` and the roadmap are present; repository `SKILL.md` is absent; the upstream shared package remains unverified and is not claimed as installed.

**Exact-head CI:** Phase 1 push [42185639666](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42185639666) and PR [42185644593](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42185644593) both had Android jobs pass, but Python policy failed one of 510 tests: the source gate expected an inline `shell("input swipe …")` call while the implementation intentionally constructs a command variable and passes it to `shell(command)`. The other 509 Python tests passed. CI-003 push [42185639250](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42185639250) and PR [42185644451](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42185644451) passed independent builders and cross-runner verification.

**QA-005 failure:** PR run [42185644441](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42185644441) built the APK, passed the dependency negative control and booted the API 35 x86_64 emulator. The instrumentation runner then started zero tests because the app process `tech.mrnothing.os` hit an ActivityManager startup ANR (`failed to complete startup`). The captured system sample showed 98% total CPU use and CPU-pressure `some avg10=87.71%`; emulator meminfo showed about 1.1 GiB available of 2.4 GiB. This supports CPU contention as a plausible environmental contributor but does not prove the root cause. It was not a trust assertion failure. The workflow cleared the synthetic PIN. Artifact [13488060665](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42185644441/artifacts/13488060665), SHA-256 `839dfb5ca6a3920650665021c0d28ebb524cc9c8f54724ef2d00f64a76f50189`.

**Bounded correction:** (1) make the Python source gate verify the command variable and `shell(command)` call instead of requiring a particular inline spelling; (2) give the disposable emulator 4 vCPUs and 3 GiB RAM to reduce startup contention; (3) capture read-only `dumpsys activity lastanr` and app-process `dumpsys meminfo` in the always-run QA artifact. No production Android source, trust-store semantics, credential policy, manifest permission, agent execution path or physical-device operation is changed.

**Acceptance:** exact-head Phase 1 push/PR, CI-003 push/PR and full QA-005 must be rerun. SEC-020B4D remains NOT ACCEPTED until both commit-boundary instrumentation tests execute and pass, the complete QA sequence passes, and synthetic PIN cleanup succeeds. No emulator test result is inferred from build success. No physical Pixel 9 Pro, StrongBox, spoken TalkBack, production signing, deployment or independent human security approval is claimed. PR #1 remains draft/unmerged; PRs #3–#7 are untouched. Milestones remain M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7/M8 BLOCKED.


## Engineering Factory update — QA-005 credential-surface evidence capture (2026-11-06)

**Audit baseline:** authorized branch `feat/phase1-agentic-phone`, exact remote head `39e0fdb5a22128d9e73a32e8db789cad468cea5c`; complete recursive tree `ea05c9409fb76dc3585044362cf2832a32940ae8` contains 276 entries and is not truncated. `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` are present. No repository `SKILL.md` is present; the upstream shared package remains unverified and is not claimed as installed. Six PRs are open (#1, #3–#7). PR #1 targets `main`, is draft, and tracks this branch. The branch endpoint reports protection disabled and no required status checks.

**Exact-head CI:** Phase 1 push [42187262230](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42187262230) and PR [42187269406](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42187269406) passed; each Python policy job ran 512 tests and each Android job passed unit/build, repeat debug-APK comparison and dependency-verification negative control. CI-003 push [42187262218](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42187262218) and PR [42187269334](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42187269334) passed both independent unsigned builders and the cross-runner verifier.

**QA-005 failure:** PR run [42187269323](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42187269323) built both APKs, passed the dependency negative control, booted API 35 x86_64 and executed three instrumentation tests. The queued-Activity destruction test passed. Both SEC-020B4D commit-boundary tests failed inside `prepareInteractiveUnlockedEmulator()` before the owner Activity prompt, credential callback or fake-store boundary. The state snapshot was secure=true, deviceLocked=true, keyguardLocked=true, userUnlocked=true, interactive=true and `canAuthenticate(DEVICE_CREDENTIAL)=0`. The unprivileged `uid=2000(shell)` swipe returned no shell error, but the exact SystemUI credential field was not exposed. The bounded accessibility snapshot showed one SystemUI root and no accessible window; its earlier string rendering truncated node detail. `dumpsys activity lastanr` reported no ANR since boot; app meminfo found no running process after instrumentation teardown. The workflow logged successful synthetic PIN cleanup. JUnit: 3 tests, 1 passed, 2 failed. Evidence artifact [13488950213](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42187269323/artifacts/13488950213), SHA-256 `b2c240d7526f23786f62f2644214b095a9d904515423e9804ef44f6b5e145544`.

**Bounded correction:** this commit changes only the instrumentation and QA evidence path. On missing-credential-surface failure, the test now captures a PNG of the disposable emulator screen into the debug target's private files directory; the always-run workflow extracts only that known file with `adb exec-out run-as tech.mrnothing.os`, without root or storage permissions. The accessibility snapshot now records bounded resource IDs, view classes, bounds and interaction state, but deliberately omits lockscreen text/content descriptions to reduce incidental data collection. No further swipe or credential behavior is changed; no production Kotlin, trust-store, manifest permission, agent executor or device-control path is modified.

**Acceptance:** exact-head Phase 1 push/PR, CI-003 push/PR and full QA-005 rerun are required. SEC-020B4D remains NOT ACCEPTED until both commit-boundary tests pass and the complete QA sequence passes with synthetic PIN cleanup. The screenshot is diagnostic evidence only, not an acceptance result. No physical Pixel 9 Pro, StrongBox, spoken TalkBack, production signing, deployment or independent human security approval is claimed. Milestones M1/M2/M6 remain IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7/M8 BLOCKED.


## Engineering Factory update — QA-005 diagnostic source-gate alignment (2026-11-06)

At commit `fa382c55ff90fe8b7d6b2f2f7218b18c4f8fe65d`, the new QA-005 instrumentation diagnostics changed the accessibility snapshot bound from 80 nodes/9 KB to 96 nodes/14 KB and added a failure-only screenshot plus structured resource-ID/class/bounds metadata. Both exact-head Phase 1 Python-policy runs (push [42189133391](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42189133391), PR [42189139278](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42189139278)) ran 514 tests and failed one existing source assertion that still expected `visited < 80`; the other 513 tests passed. This was a stale test expectation, not a production Android or runtime test failure.

The source regression test now pins the new 96-node/14-KB bound, resource-ID and bounds metadata, screenshot capture, and exact failure-path invocation. The Kotlin KDoc is aligned with the implementation. The current-head Android build, CI-003 and QA-005 workflows were still running when this follow-up was prepared; no result from those in-progress runs is treated as a pass. A superseding commit may cancel their PR-scoped QA run; exact-head workflows must be inspected again.

No production Android source, trust behavior, credential gate, permission, executor, OTA, physical-device operation or release configuration changes. SEC-020B4D remains NOT ACCEPTED until the exact SystemUI credential surface is understood and both commit-boundary tests plus the complete QA-005 sequence pass.


## Engineering Factory update — bound QA-005 failure capture (2026-11-06)

The current-head run 42189523839 on 6ee44980abcdd108a334eeb74b9df4acd3e26ae3 remained in the SEC-020B4D instrumentation step at the time of this audit; no conclusion is inferred. The prior fa382c5 run did complete all three instrumentation tests successfully (3/3) and logged successful synthetic PIN cleanup, but it was cancelled before the remaining QA sequence after a superseding commit.

The failure screenshot mechanism is now bounded at the workflow layer rather than calling UiAutomation.takeScreenshot() from the instrumentation thread. The test runner is limited to 180 seconds. If Gradle instrumentation exits nonzero while the synthetic PIN is configured, the shell EXIT trap captures adb exec-out screencap -p with a 10-second timeout before clearing the synthetic PIN; the artifact upload already runs under if: always(). A missing/empty screenshot is removed and does not mask the original failure. No root, storage permission, app-private file extraction or production screenshot API is used. Structural accessibility metadata remains bounded to 96 nodes/14 KB and excludes text/content descriptions.

The QA source gates now enforce the timeout, screenshot-before-cleanup ordering and absence of root. No production Android trust logic, consent, permission, executor, OTA, device-control path or release signing changes. SEC-020B4D remains NOT ACCEPTED until exact-head instrumentation and the complete QA-005 sequence pass.


## Engineering Factory update — QA-005 source-gate alignment for bounded capture (2026-11-06)

At commit 74daa54a8722107d9e1a743b477839967dfe15ae, the screenshot capture moved from instrumentation-thread UiAutomation to a bounded workflow EXIT-trap ADB screencap before synthetic PIN cleanup, with a 180-second instrumentation timeout and a 10-second screenshot timeout. The exact-head Phase 1 Python-policy push [42190320518](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42190320518) and PR [42190328138](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42190328138) each ran 514 tests and failed two stale source assertions that still expected the removed instrumentation screenshot helper. The other 512 tests passed. No Android runtime or production-code failure was indicated by those Python-only failures.

The two static gates now verify the actual architecture: bounded structural accessibility metadata remains in instrumentation, no UiAutomation screenshot call exists, and the workflow captures the disposable emulator screen before clearing its synthetic PIN. The workflow test also verifies the 180-second test timeout and 10-second screenshot timeout. The exact-head Android, CI-003 and QA-005 workflows at 74daa54a were still in progress at this note; no results are inferred.

No production trust logic, permissions, agent execution, OTA, physical-device operations or release signing changed. SEC-020B4D remains NOT ACCEPTED until current-head instrumentation and the complete QA-005 sequence pass.

## Engineering Factory update — API 35 lockscreen entry-control diagnosis (2026-11-06)

**Audit baseline:** authorized branch `feat/phase1-agentic-phone`, exact head `b9c5bf04699fb5402496738988466198048eaa70`; recursive tree is complete (276 entries, not truncated). `PROJECT-ADAPTER.md` and the milestone roadmap are present; repository `SKILL.md` is absent. The upstream shared package remains unverified and is not claimed as installed. Six PRs remain open (#1 and #3–#7); PR #1 is the draft umbrella against `main`. PR #1 has no submitted reviews or inline review threads. Repository rulesets returned an empty list; branch-protection read returned HTTP 403, so protection requirements cannot be independently confirmed. Other PR branches were not modified.

**Exact-head CI:** Phase 1 push [42190596086](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42190596086) and PR [42190602792](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42190602792) both passed Python policy (514 tests) and Android build/unit-test jobs. CI-003 push [42190596083](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42190596083) and PR [42190602831](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42190602831) passed both independent builders and the independent verifier.

**QA-005 failure:** PR run [42190602809](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42190602809) built the debug APK, passed the dependency negative control, booted the API 35 x86_64 emulator and ran all three lifecycle instrumentation tests. The queued-Activity destruction test passed; both SEC-020B4D commit-boundary tests failed in the emulator credential preflight before the owner Activity/prompt or fake-store boundary. JUnit reported 3 tests, 1 passed and 2 failed. The screen was secure, awake and keyguard-locked. The unprivileged `uid=2000(shell)` swipe returned without a shell error but did not reveal the PIN pad. The failure hierarchy identified the exact clickable SystemUI control: `com.android.systemui:id/device_entry_icon_view`, class `android.widget.FrameLayout`, visible/enabled/clickable, bounds `Rect(446,1538 - 634,1726)`. The pre-cleanup screenshot shows the clock/lockscreen still visible. No ANR was reported. The synthetic emulator PIN cleanup completed. Evidence artifact [13489153468](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42190602809/artifacts/13489153468), SHA-256 `757f74756340e3c9afe89a4e4bf048a289b9596bddb0016488bb45511b8ddce2`.

**Bounded correction:** replace the ineffective swipe in the debug instrumentation only with a tap at the center of that exact SystemUI device-entry node. Before tapping, require the root package, exact resource ID, exact FrameLayout class, visible/enabled/clickable state, non-empty on-screen bounds and ordinary shell UID 2000. Then wait for the existing exact SystemUI credential package/resource-ID/class selector before typing the synthetic PIN. This does not dismiss Keyguard, guess coordinates, enter app-owned fields, use root, change production trust logic, add permissions or connect an executor. Python source gates now enforce the new tap boundary and preserve the existing no-bypass checks.

**Acceptance:** rerun exact-head Phase 1 push/PR, CI-003 push/PR and the complete QA-005 workflow. SEC-020B4D remains NOT ACCEPTED until both commit-boundary cases reach and pass their fake-store assertions, the complete QA-005 sequence passes, and synthetic PIN cleanup is evidenced. No physical Pixel 9 Pro, StrongBox, spoken TalkBack, independent human security approval, production signing or deployment is claimed. Milestones remain M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7/M8 BLOCKED.

## SEC-020B4D exact-head emulator acceptance — 2026-11-06

**Acceptance commit:** `7f35638135ea72691d36a852fce726510ea3d4a4` on `feat/phase1-agentic-phone`. This entry supersedes the preceding pending-acceptance note: SEC-020B4D is accepted for the tested API 35 x86_64 disposable-emulator lifecycle path only.

**Phase 1:** push [42196955293](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42196955293) and PR [42196960787](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42196960787) both completed successfully. Each Python-policy job ran 514 tests. Android jobs passed `:app:testDebugUnitTest`, `:app:assembleDebug`, same-run repeat debug-APK byte identity, strict Gradle dependency verification and the modified-dependency negative control. The manifest security gate and static compilation passed.

**CI-003:** push [42196955307](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42196955307) and PR [42196961064](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42196961064) both completed successfully. Independent runners produced byte-identical unsigned release APKs (7,829,060 bytes, 21 ZIP entries), SHA-256 `3c09c4b4c7956cb7e2a90fdc96c9ab909f53f4526c8439ed25b0aae78c49f1ea`; normalized entry SHA-256 `9e6c4b9489af0f8b07f1d5fdae1d2ac6746041686d84fded9c0cecd4ddbc97d1`. Runtime SPDX SBOM SHA-256 `4a80dbb0025f0f0f59121f321b894d05eab896572ef609852eecd982ddb76b58` and scoped CI-006 build-environment inventory (1,260 components) matched. The inventory is not a complete hosted-runner image SBOM. Provenance retains `release_ready=false`; these are unsigned artifacts.

**QA-005:** PR run [42196960708](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42196960708) completed successfully. JUnit recorded 3 lifecycle tests, 0 failures, 0 errors and 0 skipped. Both commit-boundary cases passed, as did launcher runtime/recovery, QA-006 through QA-010, QA-013, QA-020B2 and QA-020B3. The exact SystemUI device-entry tap revealed the credential surface; the PIN was entered only after the existing exact package/resource-ID/class check. Synthetic emulator PIN cleanup artifact reports `Lock credential cleared`. QA evidence artifact [13493371286](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42196960708/artifacts/13493371286).

**Accessibility limitation:** QA-011 found TalkBack installed but its service disabled (`blocked_service_disabled`). QA-012 passed structural hierarchy/label/order/bounds checks only. Spoken TalkBack navigation is NOT accepted. This does not complete M2.

**Remaining governance and product limits:** PR #1 remains open/draft/unmerged with no submitted reviews or inline review threads. Repository rulesets are empty; the branch-protection endpoint is inaccessible to this integration (HTTP 403), so enforcement is not verified. Independent human security approval remains pending. No physical Pixel 9 Pro or StrongBox validation, production signing, OTA, deployment, connected device executor or production readiness is claimed. Milestones remain M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4/M5 NOT STARTED; M7 BLOCKED by hardware access; M8 BLOCKED. No milestone is complete.


## QA-005 exact-head follow-up — Android 15 PIN bouncer selector

On `02774f1732baae7c99f51a0ec4ecd8ba65949a05`, exact-head Phase 1 push/PR and CI-003 push/PR passed. QA-005 [42198706537](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42198706537) failed its instrumentation step: JUnit reported 3 tests, 2 failures, 0 errors and 0 skipped. The failure artifact [13492968682](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42198706537/artifacts/13492968682) shows the SystemUI PIN bouncer was visible, but Android 15 did not expose the expected `pinEntry` accessibility node. The hierarchy did expose `keyguard_pin_view`, `pin_container`, `bouncer_primary_message_area` and the ten clickable digit controls. The second lifecycle test then found the entry icon hidden because the first test had already revealed the PIN pad.

The bounded instrumentation correction recognizes only that complete exact SystemUI keypad structure and checks ordinary shell UID 2000 again immediately before sending the synthetic PIN. It does not alter production trust behavior. Exact-head CI/QA and independent review remain pending. Keep SEC-020B4D unaccepted on the new head until both commit-boundary cases and the full QA-005 workflow pass.


### Exact-head Python source-gate alignment

At `f68dd47591379a4fae52eba260bc928c703dc5df`, the Phase 1 Python-policy jobs ran 515 tests with 1 failure: a source assertion still expected the previous inline package check, while the implementation uses a local `packageName` variable before the same allowlist decision. The other 514 tests passed. The source gate was updated to assert the variable, allowlist check and SystemUI-specific keypad branch. The QA-005 run at that head had not reached instrumentation when superseded; it is not counted as a runtime result. Re-run all exact-head gates on the corrective commit.


## 2026-11-06 — SEC-020B4D exact-head acceptance and SEC-020B5

### SEC-020B4D acceptance at `ceebf9fb24d46c2156d584a1b8995e8a5bbc0745`

Exact-head Phase 1 push [42200088688](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200088688) and PR [42200100036](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200100036) passed. Both Python-policy jobs ran 515 tests; Android unit tests, debug assembly, repeat debug APK comparison, strict dependency verification, modified-dependency negative control and source-manifest security gate passed.

Exact-head CI-003 push [42200088574](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200088574) and PR [42200100017](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200100017) passed independent-runner verification. Unsigned release APKs were byte-identical (7,829,060 bytes; SHA-256 `3c09c4b4c7956cb7e2a90fdc96c9ab909f53f4526c8439ed25b0aae78c49f1ea`; normalized-entry SHA-256 `9e6c4b9489af0f8b07f1d5fdae1d2ac6746041686d84fded9c0cecd4ddbc97d1`). Runtime inventory and SPDX runtime SBOM matched. Provenance retains `release_ready=false`.

QA-005 PR [42200100094](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200100094) completed with all workflow steps successful. The API 35 x86_64 emulator ran the three SEC-020B4D lifecycle instrumentation tests, launcher/recovery and QA-006 through QA-013, plus QA-020B2/B3; the synthetic PIN cleanup reported `Lock credential cleared`. Evidence artifact [13493729544](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200100094/artifacts/13493729544). QA-011 remains only a read-only service-availability preflight (`blocked_service_disabled`); QA-012 is structural semantics, not spoken TalkBack.

**Gate decision:** SEC-020B4D is accepted for this API 35 x86_64 disposable-emulator lifecycle path only. This does not establish StrongBox/Pixel hardware behavior, physical crash recovery, spoken TalkBack or independent security approval.

### SEC-020B5 — Android AtomicFile interruption/recovery instrumentation

A new instrumentation suite uses a ContextWrapper with an isolated temporary no-backup directory and the real `AndroidAtomicAuthorityRecordPersistence` adapter. It covers write/read and replacement, interrupted replacement backup restoration through `AtomicFile.openRead()`, interrupted first-write classification (partial data is not a fresh-install `Missing` result), oversized stored-record rejection, and invalid write-bound preservation.

The interrupted replacement is simulated by closing an unfinished `AtomicFile.startWrite()` stream without calling `finishWrite()` or `failWrite()`. This tests the deterministic backup-recovery window; it is not a process-kill, power-loss, filesystem-corruption or Pixel hardware test. No production backend, credential, trust authority, permission or executor behavior changes.

**Current acceptance:** source/test committed; exact-head Phase 1, CI-003 and QA-005 workflows pending. Keep SEC-020B5 IN PROGRESS until the new instrumentation suite passes on the disposable emulator and independent review examines the test's AtomicFile assumptions.

**Next after SEC-020B5:** add isolated Android Keystore behavior tests that prove StrongBox absence and alias/metadata failures refuse without TEE/software fallback, then reserve actual StrongBox durability and recovery acceptance for supervised Pixel 9 Pro M7 hardware validation. Do not treat emulator Keystore as StrongBox evidence.


## Engineering Factory update — SEC-020B5 first-write recovery assertion (2026-11-06)

Current audited head before correction: 67252b5d4418bd5419a70dafea943d04f8d91c11. The complete recursive tree contained 278 entries; PROJECT-ADAPTER.md and this roadmap are present; repository SKILL.md and verified upstream shared package are absent/unverified. Six open PRs (#1, #3, #4, #5, #6, #7) were inspected. PR #1 remains draft and unmerged.

Exact-head CI before correction:
- Phase 1 push [42203138765](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42203138765): success.
- Phase 1 PR [42203152527](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42203152527): success.
- CI-003 push [42203138732](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42203138732): success.
- CI-003 PR [42203152420](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42203152420): success.
- QA-005 PR [42203152698](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42203152698): failed in the Android instrumentation step. The test log identifies one failure in testInterruptedFirstWriteIsNotReportedAsMissing; the other seven instrumentation tests completed without reported failure. Later QA steps were skipped. The synthetic emulator PIN cleanup succeeded.

The failed assertion expected an unfinished first AtomicFile write to remain Present. That is not Android's atomic staging contract when no prior base/backup exists: the staging file is discarded and openRead() reports Missing. The corrected test asserts Missing at the persistence layer, then injects a synthetic generation high-water marker and requires the trust-store coordinator to return RecoveryRequired(ACTIVE_RECORD_MISSING), never Empty. This validates the marker-first fail-closed behavior without changing production trust code.

SEC-020B5 remains IN PROGRESS until the corrected exact-head instrumentation, full QA-005 sequence and current-head CI pass. No process-kill, kernel-crash, power-loss, filesystem durability, StrongBox or physical Pixel 9 Pro evidence is claimed. No milestone is complete; independent human security review remains pending.


## Engineering Factory run — SEC-020B5 accepted; SEC-020B6 started (2026-11-06)

**Audit baseline:** `feat/phase1-agentic-phone` at `c80634ec871516e829fb18025de8af732fee422f`; recursive tree has 279 entries and is not truncated. `PROJECT-ADAPTER.md` and this roadmap are present. No repository `SKILL.md` exists; the upstream shared package remains unverified and is not claimed as installed. Six PRs are open (#1, #3, #4, #5, #6 and #7). PR #1 remains open/draft, head `c80634ec871516e829fb18025de8af732fee422f`, base `main`, with zero submitted reviews and zero inline review threads. No other PR branch was modified.

### SEC-020B5 exact-head acceptance

- Phase 1 push [42210823960](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210823960) and PR [42210832289](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210832289) passed. Both Python-policy jobs ran **518 tests**. Both Android jobs passed `:app:testDebugUnitTest`, `:app:assembleDebug`, same-run repeat debug-APK byte comparison, strict dependency verification and the modified-dependency negative control. Android source-manifest security checks passed.
- CI-003 push [42210824198](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210824198) and PR [42210832148](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210832148) passed both builders and independent verification. Unsigned APKs were byte-identical (7,829,060 bytes; SHA-256 `3c09c4b4c7956cb7e2a90fdc96c9ab909f53f4526c8439ed25b0aae78c49f1ea`; normalized-entry SHA-256 `9e6c4b9489af0f8b07f1d5fdae1d2ac6746041686d84fded9c0cecd4ddbc97d1`). Runtime inventory, SPDX runtime SBOM and scoped 1,260-component CI-006 build-environment inventory matched. The inventory is not a complete hosted-runner image SBOM. Provenance reports `reproducible=true`, `release_ready=false`.
- QA-005 [42210832208](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210832208) passed all 21 workflow steps on a disposable API 35 x86_64 emulator. The instrumentation log reports 8 tests started and 8 finished, then `BUILD SUCCESSFUL`; this includes three SEC-020B4D lifecycle tests and five SEC-020B5 AtomicFile tests. QA-006 through QA-013 and QA-020B2/B3 completed, and the synthetic PIN cleanup reported `Lock credential cleared`. Evidence artifact [13498728651](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210832208/artifacts/13498728651).
- SEC-020B5 is accepted for this API 35 x86_64 emulator AtomicFile path only. It does not prove process-kill, kernel-crash, power-loss, filesystem-corruption, StrongBox or Pixel 9 Pro durability. QA-011 is service availability only (`blocked_service_disabled`); QA-012 is structural semantics, not spoken TalkBack.

### SEC-020B6 implementation

A test-only alias namespace was added to `AndroidAuthorityTrustCrypto`; default production aliases and no-argument production construction remain unchanged. New API 35 instrumentation covers StrongBox-required generation with no TEE fallback, missing marker proof, malformed/non-canonical/zero marker aliases, TEE-only marker rejection, AES alias without a generation marker, and wrong key type under the marker prefix. A Python source-policy test protects default aliases, both StrongBox requirements and the security-level comparison.

SEC-020B6 is **IN PROGRESS** until exact-head Phase 1, CI-003 and QA-005 pass on the new commit. Emulator results do not establish StrongBox hardware. KeyInfo-provider exception injection and actual Pixel 9 Pro M7 validation remain open.

**Current milestone status:** M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED by physical-device access; M8 BLOCKED. No milestone is COMPLETE. Independent human security review, spoken TalkBack acceptance, physical Pixel 9 Pro/StrongBox validation, signed release, OTA rollback and production deployment remain outstanding.

**Next task after SEC-020B6 exact-head acceptance:** add a deterministic KeyInfo/Keystore failure-injection seam for provider exceptions and missing AES-key-with-valid-marker states, without weakening StrongBox policy; then reserve real StrongBox and reboot/recovery acceptance for supervised Pixel 9 Pro M7 hardware validation.


## SEC-020B6 first emulator run — fixture correction (2026-11-06)

At head `28065d7416c2aa89ffc17ed3dcf4614f2a34e733`, Phase 1 push [42220210875](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42220210875) and PR [42220218289](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42220218289) passed; each Python-policy job ran **524 tests** and both Android jobs passed unit tests, debug assembly, same-run repeat APK comparison, strict dependency verification and modified-dependency negative control. CI-003 push [42220210790](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42220210790) and PR [42220218370](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42220218370) both passed independent verification. The unsigned APKs were byte-identical at 7,829,728 bytes, SHA-256 `09623ce52db112aab99a23b08196b260e9fab02456e76a41d970c14edbc69510`, normalized-entry SHA-256 `97c70391d2c258e19a7cd4080e04bc852472b4c622320bea760ef56fea6c0027`; verifier reported `reproducible=true`, `release_ready=false`.

QA-005 [42220218287](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42220218287) compiled and started all 16 instrumentation tests. Two SEC-020B6 test cases failed in the synthetic Ed25519 record helper before their crypto assertions because default provider selection resolved to the AndroidKeyStore key-pair generator, which was not initialized. The other 14 tests reported no failures. Later QA-006 through QA-020B3 steps were skipped by fail-fast behavior. Diagnostics uploaded; log records `Lock credential cleared`.

The fixture is corrected to instantiate Bouncy Castle explicitly for the in-memory synthetic Ed25519 key pair, consistent with the ceremony's provider-isolation design. This is test-only; no production trust or key-generation policy changed. SEC-020B6 remains **IN PROGRESS** pending exact-head Phase 1, CI-003 and QA-005 rerun.


## Engineering Factory run — SEC-020B6 acceptance and SEC-020B6A implementation (2026-11-06)

**Audit baseline:** branch `feat/phase1-agentic-phone` at `83a3aa2e90e89b29bae4f9c2b14cd402f084ebc7`; complete recursive tree has **282 entries**, not truncated. The latest 20 commits were inspected. `PROJECT-ADAPTER.md` and this roadmap are present; repository `SKILL.md` is absent. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. Six PRs (#1, #3, #4, #5, #6, #7) are open/draft. PR #1 targets `main`, head is the authorized branch, and has no submitted reviews or inline review threads. Branch API reports `protected=false`; repository rulesets are empty. Other PR branches were not modified.

### SEC-020B6 exact-head acceptance

- Phase 1 push [42221148919](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221148919) and PR [42221159695](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221159695) passed. The push Python-policy job ran **524 tests**. Both Android jobs passed `:app:testDebugUnitTest`, `:app:assembleDebug`, same-run repeat debug-APK comparison, strict Gradle dependency verification, modified-dependency negative control and Android manifest security checks.
- CI-003 push [42221148873](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221148873) and PR [42221159954](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221159954) passed both independent builders and verifier. Unsigned release APKs were byte-identical (7,829,728 bytes; SHA-256 `09623ce52db112aab99a23b08196b260e9fab02456e76a41d970c14edbc69510`; normalized-entry SHA-256 `97c70391d2c258e19a7cd4080e04bc852472b4c622320bea760ef56fea6c0027`). Runtime inventory, SPDX runtime SBOM, release variant and toolchain matched. Verifier reports `reproducible=true`, `release_ready=false`; CI-006's 1,260-component inventory is scoped, not a complete runner-image SBOM.
- QA-005 [42221159692](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221159692) passed all workflow steps on a disposable API 35 x86_64 emulator. The instrumentation log reports **16 tests started, 16 finished, 0 skipped, 0 failed**: three SEC-020B4D, five SEC-020B5 and eight SEC-020B6. QA-006 through QA-013 and QA-020B2/B3 passed; synthetic emulator PIN cleanup succeeded. Evidence artifact [13504760131](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221159692/artifacts/13504760131), digest `sha256:4012f7db4d37504a9080fd49bb57eff1cc9780803733e56f4a19f4346b0eb519`.
- QA-011 is a read-only TalkBack service-availability preflight and found the service disabled. QA-012 is structural semantics, not spoken TalkBack acceptance.

SEC-020B6 is accepted only for the tested API 35 x86_64 emulator negative-path scope. It does not prove StrongBox hardware, Pixel 9 Pro behavior, Keystore persistence across reboot/reset, spoken TalkBack, independent human security approval or production readiness.

### SEC-020B6A — KeyInfo/provider failure injection

A narrow internal `AndroidAuthorityKeyInfoReader` seam was added to `AndroidAuthorityTrustCrypto`. The production default is `PlatformAndroidAuthorityKeyInfoReader`, which preserves the existing AndroidKeyStore SecretKeyFactory and KeyInfo.securityLevel query. Production construction remains no-argument with unchanged aliases.

Three new isolated instrumentation cases cover:
1. GeneralSecurityException from KeyInfo inspection -> `Unavailable`.
2. Runtime provider exception from KeyInfo inspection -> `Unavailable`.
3. Missing AES alias with a generation marker and valid envelope -> `RecoveryRequired(ACTIVE_RECORD_UNREADABLE)`, never `Empty`.

The third test uses a metadata-only test double and a disposable TEE test alias to reach the coordinator state on an emulator; it is not StrongBox evidence. No process-wide JCA provider registration, production alias, key, authority, permission, trust transition or executor was changed.

**SEC-020B6A status:** implementation committed; exact-head Phase 1, CI-003 and QA-005 reruns pending.

**Current milestone status:** M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED by physical Pixel 9 Pro access; M8 BLOCKED. No milestone is COMPLETE. Independent human security review, spoken TalkBack acceptance, physical StrongBox/reboot recovery, signed release, OTA rollback and production deployment remain outstanding.

**Next bounded task after SEC-020B6A acceptance:** add deterministic Keystore load/alias-enumeration failure injection, then stop emulator-only claims and reserve real StrongBox, reboot and recovery acceptance for supervised Pixel 9 Pro M7 hardware validation.


## Engineering Factory run — 2026-11-06, SEC-020B6A acceptance and SEC-020B6B

**Audit head:** `f6e4099ae991eba9b7e8a56a674b08efd479c7ed`. The recursive tree contained 282 entries and was not truncated. `PROJECT-ADAPTER.md` and this roadmap are present; no repository `SKILL.md` exists. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. Six PRs (#1, #3, #4, #5, #6, #7) are open/draft. PR #1 targets `main`, its head matches the authorized branch and it has no submitted reviews or inline review threads. The rulesets endpoint returned an empty list; the branch-protection endpoint returned 403 for this integration, so current branch-protection settings are not independently verified. Other PR branches were not modified.

### SEC-020B6A exact-head acceptance

- Phase 1 push [42223971396](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223971396) and PR [42223981107](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223981107) passed. Python policy: **526 tests passed**. Android unit tests, debug assembly, repeat debug-APK comparison, strict dependency verification, modified-dependency negative control and Android manifest gate passed.
- CI-003 push [42223971449](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223971449) and PR [42223981151](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223981151) passed both independent builders and verifier. Unsigned APKs were byte-identical (7,830,680 bytes; SHA-256 `60f0df5a92ebed50e1ddf1885e56e5b12ceb25c19263f8910943d832d53fb53f`; normalized-entry SHA-256 `1c08ed89586bad608133bbcc4521c440895e10bef1dc78f4cc757501e5228405`). Runtime inventory, SPDX runtime SBOM and scoped CI-006 inventory matched; the verifier reports `reproducible=true`, `release_ready=false`.
- QA-005 PR [42223981189](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223981189) passed all steps on an API 35 x86_64 disposable emulator. Downloaded JUnit XML confirms **19/19 instrumentation tests passed**, 0 failures/errors/skips: three SEC-020B4D, five SEC-020B5 and eleven SEC-020B6/B6A. QA-006 through QA-013 and QA-020B2/B3 passed; synthetic PIN cleanup succeeded. Artifact [13505691330](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223981189/artifacts/13505691330).
- QA-011 found TalkBack disabled; QA-012 is structural semantics only, not spoken TalkBack acceptance.

SEC-020B6A is accepted only for the API 35 x86_64 emulator negative-path scope. No physical StrongBox, Pixel 9 Pro, reboot/reset persistence, spoken TalkBack, independent human security approval or production readiness is implied.

### SEC-020B6B implementation

A narrow internal `AndroidAuthorityKeyStoreReader` seam preserves the production platform default while allowing deterministic load/alias-enumeration failure injection. Five new instrumentation cases cover GeneralSecurityException, IOException and runtime failure during KeyStore load, plus GeneralSecurityException and runtime failure during marker-alias enumeration. Each requires `Unavailable`, refusal to create a generation marker and no test marker/AES alias mutation. Tests use UUID-scoped aliases and do not register global JCA providers.

**SEC-020B6B:** implementation committed; exact-head Phase 1, CI-003 and QA-005 validation pending.

**Milestones:** M1/M2/M6 remain IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED pending supervised Pixel 9 Pro access; M8 BLOCKED. No milestone is complete. Independent human security review, spoken TalkBack, physical StrongBox/reboot recovery, signed releases, OTA rollback and production deployment remain outstanding.

**Next bounded task after SEC-020B6B acceptance:** add deterministic KeyStore key-retrieval failure injection for marker/AES aliases, then reserve actual StrongBox, reboot and recovery acceptance for supervised Pixel 9 Pro M7 hardware validation.


## Engineering Factory run — 2026-11-06, SEC-020B6B acceptance and SEC-020B6C

**Audit baseline:** `feat/phase1-agentic-phone` at `83bb54904e7f9db15ac42a532f96dbededc91bca`. The recursive Git tree contains 282 entries and is not truncated. The latest 20 branch commits were inspected; the branch is 223 commits ahead of `main` and 0 behind at this baseline. `PROJECT-ADAPTER.md` and this roadmap are present; repository `SKILL.md` is absent. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. Six PRs (#1, #3, #4, #5, #6, #7) are open/draft. PR #1 targets `main`, has 223 commits/218 changed files, matches the authorized branch head, and has zero submitted reviews and zero inline review threads. Other PR branches were not modified. The branch API reports `protected=false`; repository rulesets are empty.

### SEC-020B6B exact-head acceptance

- Phase 1 push [42226887109](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42226887109) and PR [42226898225](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42226898225) passed. Each Python-policy job ran **528 tests**. Android debug unit tests/build, same-run repeat debug APK comparison, strict Gradle dependency verification, modified-dependency negative control and Android manifest security gate passed.
- CI-003 push [42226887105](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42226887105) and PR [42226897830](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42226897830) passed both independent builders and verifier. Unsigned release APKs were byte-identical (7,831,748 bytes; SHA-256 `3008fcdc6a737aaa9b200565f5535abe84ad2dcd0731f8cd0811c73a4a16627f`; normalized-entry SHA-256 `600e753c6aebf12cc8b8b6774910a30ee57cfe44f389acd473be4c433c7acf15`). Runtime inventory SHA-256 `9b06a5f81611e6fcbf8264ab0793543a02e29a8a7b9ef3c8aa8994b3a32afe8b`; SPDX runtime SBOM SHA-256 `51ad4b95bd8326c3a0fe2b66372329b4e9b166df5eb7c78561fddf304fb2eb31`. The verifier reported `reproducible=true`, `release_ready=false`. The 1,260-component CI-006 inventory is scoped and is not a complete hosted-runner image SBOM.
- QA-005 [42226897923](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42226897923), attempt 2, passed its emulator-smoke job and all workflow steps on a disposable API 35 x86_64 emulator. The first attempt failed in the existing SEC-020B4D lifecycle callback test; the failed-job-only retry succeeded without source changes. Evidence artifact [13511926456](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42226897923/artifacts/13511926456), digest `sha256:6f7261289126bf0358afd93ae113e1bc636c6daa20834eccadda4a4be5f52ab0`. QA-011 reports `blocked_service_disabled` (not TalkBack acceptance); QA-012 is structural semantics only, not spoken TalkBack.
- SEC-020B6B is accepted only for the tested API 35 x86_64 emulator Keystore-load and alias-enumeration failure paths. It does not establish physical StrongBox or Pixel 9 Pro behavior.

### SEC-020B6C — KeyStore key-retrieval failure injection

A narrow `AndroidAuthorityKeyStoreReader.getKey(store, alias)` seam routes production marker/AES retrieval through the platform default, which delegates directly to `KeyStore.getKey(alias, null)`. Production aliases and no-argument `AndroidAuthorityTrustCrypto()` construction remain unchanged.

Four isolated instrumentation cases inject:
1. `UnrecoverableKeyException` while reading a generation-marker key.
2. `ProviderException` while reading a generation-marker key.
3. `UnrecoverableKeyException` while reading an existing AES record key.
4. `ProviderException` while reading an existing AES record key.

Marker retrieval failures must make the trust store `Unavailable`, make marker verification false, and refuse generation advancement. AES retrieval failures must make encrypt/decrypt fail closed and map a present record to `RecoveryRequired(ACTIVE_RECORD_UNREADABLE)`, never `Empty` or `Active`. Existing test aliases must remain untouched; no fallback key or marker is created. The tests use unique disposable aliases and a metadata-only KeyInfo test double for emulator state classification; this is not StrongBox hardware evidence.

**SEC-020B6C:** implementation committed in the current audit run; exact-head Phase 1, CI-003 and QA-005 validation are pending.

**Milestones:** M1/M2/M6 remain IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED pending supervised physical Pixel 9 Pro access; M8 BLOCKED. No milestone is complete. Independent human security review, spoken TalkBack acceptance, physical StrongBox/reboot recovery, signed release, OTA rollback and production deployment remain outstanding.

**SEC-020B6C exact-head acceptance:** completed at `893b8cdadab035439eefe62aeb4d42409b6d47ef`; see `docs/SEC-020B6-ANDROID-KEYSTORE-FAIL-CLOSED.md`. The next unblocked task is to prepare the supervised Pixel 9 Pro M7 validation protocol, then execute it only when an exact Pixel 9 Pro (`caiman`) and explicit operator consent are available. TalkBack spoken-navigation acceptance remains a separate consented gate.


## Engineering Factory run — 2026-11-06, SEC-020B6C exact-head acceptance and M7 preparation

**Audit:** `feat/phase1-agentic-phone` at `893b8cdadab035439eefe62aeb4d42409b6d47ef`; recursive tree 282 entries, not truncated; latest 20 commits inspected; 224 commits ahead of `main`, 0 behind. `PROJECT-ADAPTER.md` and this roadmap are present. Repository `SKILL.md` is absent; upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. Six PRs (#1, #3, #4, #5, #6, #7) are open/draft. PR #1 targets `main`, has 224 commits/218 changed files, matches the authorized head and has no submitted reviews or inline review threads. No other PR branch was changed. Repository rulesets collection is empty.

### SEC-020B6B/B6C exact-head verification

- Phase 1 push [42244248208](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244248208) and PR [42244257688](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244257688): both passed; each Python policy job ran 530 tests. Android debug unit tests/build, repeat debug APK comparison, dependency verification and negative control, manifest gate and provenance passed.
- CI-003 push [42244248205](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244248205) and PR [42244257705](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244257705): both independent builders and verifiers passed. Unsigned APKs were byte-identical (7,831,964 bytes; SHA-256 `a8acfc839d7de40d21cf6452989056953060e24eb8dd12f766408f3b029e30f9`; normalized entries `4cc2150f1d66384508ab181236d233b7abec5eeebcbeed855a45b43be3aab8b4`). Runtime inventory and SPDX runtime SBOM matched; `reproducible=true`, `release_ready=false`.
- CI-006 matched its scoped 1,260-component build-environment inventory/SBOM; it is not a complete hosted-runner image SBOM.
- QA-005 [42244257673](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244257673) passed every step on API 35 x86_64. Downloaded JUnit XML: 28 tests, 0 failures, 0 errors, 0 skipped. This includes 3 lifecycle, 5 AtomicFile and 20 SEC-020B6-family cases, including all four B6C key-retrieval tests. Artifact [13516679629](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244257673/artifacts/13516679629), digest `sha256:57dfa4349aef3a1db93a8f523f240d6b0589ded6c11cf27051405fbd0a3940b9`.
- QA-011 remains blocked because the TalkBack service is disabled; QA-012 verifies structural semantics only, not speech or spoken navigation.

**SEC-020B6B and SEC-020B6C are accepted for emulator-injected failure behavior only.** No physical Pixel 9 Pro, StrongBox durability, reboot persistence, spoken TalkBack or signed production release is claimed.

### Next bounded task — M7 validation protocol

The previous emulator-only trust-store failure-injection slice is closed. The next unblocked task is a detailed, non-executing Pixel 9 Pro hardware validation protocol. It must define exact-model/boot-state preflight, reviewed test-artifact provenance, StrongBox feature and `KeyInfo.securityLevel` checks, disposable-alias key operations, process-death/reboot persistence, marker-first recovery, owner-credential prompt/cancellation, HOME-role recovery, accessibility/TalkBack, SIM/VoLTE/Wi-Fi/Bluetooth, battery/thermal observation, privacy-redacted evidence and independent signoff. The protocol is prepared at `docs/M7-PIXEL9PRO-HARDWARE-VALIDATION.md`; actual hardware execution remains BLOCKED until the exact device and explicit operator consent are available.

**Milestones:** M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED pending physical Pixel 9 Pro; M8 BLOCKED. No milestone is complete. Human security review, spoken TalkBack, physical StrongBox/reboot recovery, signed release, OTA rollback and production deployment remain outstanding.


## Engineering Factory run — 2026-11-06, M7 offline Pixel 9 Pro preflight utility

**Audit baseline:** `feat/phase1-agentic-phone` at `520686472371c3e1ae609911bd78eae687b2b8a7`; recursive tree 283 entries, not truncated; latest 20 commits inspected; six open PRs (#1, #3, #4, #5, #6, #7); PR #1 remains open/draft against `main` and matches the authorized head. `PROJECT-ADAPTER.md` and this roadmap are present; repository `SKILL.md` is absent; upstream shared factory package remains unverified. Branch API reports `protected=false`; repository rulesets are empty; branch-protection detail returned 403 to this integration. No other PR branch was modified.

### Exact-head baseline before this change

- Phase 1 push [42253179947](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42253179947) and PR [42253188165](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42253188165): both passed Python policy and Android debug build/unit/repeat-build/dependency-negative-control/manifest gates.
- CI-003 push [42253179969](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42253179969) and PR [42253188174](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42253188174): both independent builders and independent verifier passed unsigned APK, normalized contents, runtime inventory, SBOM and provenance checks.
- QA-005 [42253188203](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42253188203): disposable API 35 x86_64 emulator smoke workflow passed. QA-011 is a read-only TalkBack service preflight; QA-012 is structural semantics only. Neither establishes spoken TalkBack acceptance.
- Combined commit status endpoint returned no legacy status rows; Actions workflow/job conclusions above are the CI evidence.

### Implementation

Added `scripts/m7_pixel9pro_preflight.py`, an offline validator for a manually captured, redacted ADB snapshot, and `tests/test_m7_pixel9pro_preflight.py`. Existing QA-011 covers TalkBack service readiness and SEC-014D covers an in-app device-lock/credential preview; neither duplicates this M7 model/boot-state/StrongBox-feature preflight. The new validator checks exact Google Pixel 9 Pro / `caiman` identity, API >=34, connected/authorized ADB state, locked bootloader, green Verified Boot, locked vbmeta, non-emulator indication and the StrongBox PackageManager feature. It never invokes ADB, shell or fastboot, never changes device state, and emits no serial/IMEI/phone/SIM/network/account identifiers or raw build fingerprint. A passing report remains preflight-only; `acceptance_passed=false` and `strongbox_key_security_level_verified=false`.

The M7 protocol now documents the redacted JSON schema and offline command. Its example is synthetic. Device collection still requires separate explicit owner approval; no device was connected.

### Tests and acceptance

Local command executed in a clean temporary test workspace: `python3 -m unittest -v tests/test_m7_pixel9pro_preflight.py` — **18 tests passed**. These are synthetic parser/CLI/safety tests, not Android, emulator or hardware tests. The new test module is discovered automatically by `scripts/phase1-preflight.sh` through `unittest discover -s tests -p 'test_*.py'`. Exact-head Phase 1 and CI-003 push/PR runs for the new commit are pending at commit creation and must be checked before accepting this slice. QA-005 is not expected to trigger because no Android/QA workflow paths changed.

**Milestones:** M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED pending supervised physical Pixel 9 Pro access and independent review; M8 BLOCKED. No milestone is complete. StrongBox key-level proof, reboot persistence, spoken TalkBack, human security review, signed release, OTA rollback and production readiness remain outstanding.

**Next task:** after exact-head CI passes, prepare the supervised M7 device session only when the exact `caiman` device, owner/operator approval for each stage and an independent reviewer are available. Do not run ADB against a physical device without that approval.


## Engineering Factory audit and implementation — 2026-11-06, M7 emulator-marker semantics hardening

**Audit head:** 93687c2178a4499188dc432e0fa3109c0efb37f6 on feat/phase1-agentic-phone. The complete recursive tree contained 285 entries and was not truncated. The latest 20 branch commits, all six open PRs (#1, #3, #4, #5, #6, #7), exact-head Actions runs, Android/Python architecture, adapter, roadmap and M7 protocol were inspected. PROJECT-ADAPTER.md is present; no repository SKILL.md exists. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. PR #1 remains open/draft against main and matches the authorized branch. No other PR branch was modified.

**Exact-head CI before this patch:** Phase 1 push [42264047574](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42264047574) and PR [42264057860](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42264057860) passed; both Python-policy jobs ran 548 tests. Android unit/build/repeat-build/dependency-negative-control and manifest checks passed. CI-003 push [42264047758](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42264047758) and PR [42264057822](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42264057822) passed independent-runner verification with byte-identical unsigned APKs (7,831,964 bytes; SHA-256 a8acfc839d7de40d21cf6452989056953060e24eb8dd12f766408f3b029e30f9); reproducible=true, release_ready=false.

**QA-005:** PR emulator run [42264057828](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42264057828) initially failed at SEC-020B4D testDestroyBeforeCommitClaimPreventsFakeStoreMutation; the credential callback did not reach final trust revalidation, and later QA steps were skipped. A failed-job-only retry was started; its result must be checked separately. This failure is not attributed to the M7 utility or SEC-020B6C.

**Independent source review refinement:** An initial candidate patch required ro.kernel.qemu=0. AOSP init source review showed that emulator boot imports the qemu kernel parameter as ro.kernel.qemu, while physical Android builds may omit that property. Requiring 0 would risk rejecting genuine Pixel hardware. The final rule accepts only an absent/blank marker or exact 0, rejects 1 and any other non-empty/unrecognized value, and explicitly states that absence is not proof of physical hardware. The validator emits the marker state but remains preflight-only. Three synthetic cases cover absent, unknown and noncanonical values; the existing positive emulator case remains blocked. The result always keeps acceptance_passed=false and strongbox_key_security_level_verified=false.

**Validation boundary:** The 548-test audit-head suite passed before this patch. The three added regression tests and full suite must pass on the new exact head. No local test execution is claimed because the container could not resolve github.com; exact-head GitHub Actions is the available reproducible test environment. No physical device or ADB connection was used; no installation, permission change, reboot, root, flashing or device mutation occurred.

**Milestones:** M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED pending supervised physical Pixel 9 Pro evidence and independent review; M8 BLOCKED. No milestone is complete.



## Engineering Factory run — 2026-11-07, M7 evidence-bundle validator

**Audit baseline:** `feat/phase1-agentic-phone` at `cdd35777796e9933e2fd85c8f878286bb7c17bb7`. Recursive tree: 285 entries, not truncated. Latest 20 commits inspected. Six open PRs (#1, #3, #4, #5, #6, #7); PR #1 remains open/draft against `main`, head matches the authorized branch, 227 commits ahead/0 behind, 221 changed files, and no submitted reviews or inline review threads. `PROJECT-ADAPTER.md` and this roadmap exist; repository `SKILL.md` is absent. The authorized shared-library folder is empty and Library title search found no upstream package. The upstream shared factory package remains unverified and is not claimed as installed. No other PR branch was modified.

### Exact-head CI accepted at audit head

- Phase 1 push [42266632947](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42266632947) and PR [42266642211](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42266642211): PASS. Both Python policy jobs ran **551 tests**, Python compilation/static checks and Android source-manifest security gate passed. Android `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat debug-APK byte comparison, strict Gradle dependency verification, modified-dependency negative control and debug artifact provenance passed.
- CI-003 push [42266632949](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42266632949) and PR [42266642177](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42266642177): PASS. Both independent builders completed release unit tests, unsigned release APK assembly, merged/packaged manifest security gates, dependency negative control, SPDX runtime SBOM/provenance and independent-runner APK/normalized-content/SBOM/toolchain verification.
- QA-005 disposable API 35 x86_64 emulator PR [42266642270](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42266642270): PASS. All workflow steps passed, including launcher/stock recovery, large text, HOME consent, keyboard, QA-020B2 owner-authority UI and QA-020B3 debug credential-prompt probe. Evidence artifact [13527891460](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42266642270/artifacts/13527891460). QA-011 is still only a read-only TalkBack service preflight; QA-012 is structural semantics only. Neither proves spoken TalkBack navigation.
- No physical Pixel 9 Pro was accessed. No StrongBox key-level hardware proof, reboot persistence, signed release or production readiness is claimed.

### Implementation

Added `scripts/m7_pixel9pro_evidence.py` and `tests/test_m7_pixel9pro_evidence.py`. The offline validator checks the M7 evidence schema, exact device/boot identity, test APK provenance, owner consent for every disruptive stage, exact StrongBox security levels, process-death/reboot persistence, marker-first recovery classifications, system credential prompt, launcher restoration, spoken TalkBack, connectivity, battery/thermal limits, disposable alias cleanup and absence of stop conditions/deviations.

The manifest requires 14 redacted evidence categories and verifies every artifact SHA-256 from a bounded evidence directory. It rejects unknown fields, duplicate JSON keys, non-finite values, excessive JSON depth/size, symlinks, raw alias values, incorrect device/security results and reviewer self-approval. Independent review uses Ed25519 over a canonicalized bundle; the public-key fingerprint must be supplied and pinned out of band. A complete bundle remains `evidence_bundle_verified_pending_supervisor`; the validator hardcodes `m7_milestone_complete=false` because it cannot prove the truth of observations or replace the human supervisor.

No device access, ADB, shell, installation, permission grant, reboot, root, flashing, production key handling or network listener was added. No new dependency was introduced; `cryptography==50.0.2` was already pinned for CI.

### Local validation before commit

- `python -m py_compile scripts/m7_pixel9pro_evidence.py tests/test_m7_pixel9pro_evidence.py`: PASS.
- `python -m unittest discover -s tests -p 'test_*.py' -v` in an isolated test workspace containing the new module/test: **30 tests passed**. These are synthetic validator tests, including Ed25519 signature verification, reviewer-key pin mismatch, self-review rejection, evidence hash tampering/missing/symlink cases, consent/security/StrongBox/recovery/accessibility/connectivity/thermal negatives, duplicate JSON keys, non-finite numbers, depth limits and offline CLI behavior.
- The repository-wide suite and Android workflows must pass again on the new exact commit before this slice is accepted.

**Next bounded task:** exact-head CI for this validator, then prepare a synthetic M7 bundle template/generator that emits only schema-approved fields and opaque artifact IDs. Physical M7 remains BLOCKED until exact Pixel 9 Pro access, separate owner consent for each disruptive stage and an independent reviewer are available.

**Milestones:** M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED. No milestone is complete.



## QA-005 regression — exact SystemUI PIN-key interaction (2026-11-07)

The exact-head QA-005 run [42278932746](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42278932746) executed 28 instrumentation tests: 27 passed and `testDestroyBeforeCommitClaimPreventsFakeStoreMutation` failed. The failure was in the test harness's synthetic credential entry, not the production trust backend. SystemUI logged `AuthController.showAuthenticationDialog`; the final diagnostic showed the emulator remained secure/interactive, but the Activity never received the credential callback. The captured pre-cleanup screen was the launcher, confirming that the prompt had already disappeared. The workflow successfully cleared its disposable emulator PIN.

The test helper previously sent `input text 2468` and `KEYCODE_ENTER` after recognizing the Android 15 SystemUI PIN keypad. That input-text path is ambiguous for a custom keypad. The test now taps only the exact visible, enabled, clickable SystemUI resource IDs `key0`–`key9` and `key_enter`, using bounds returned by AccessibilityNodeInfo and ordinary UID 2000 shell input. It refuses app-owned nodes, missing nodes, non-clickable controls, zero-sized bounds and non-shell execution. It does not bypass Keyguard, use root, or alter production code. Failure diagnostics now include the bounded resource-ID/class/bounds-only UI snapshot; no credential text or PIN digits are logged.

The keypad resource IDs and `key_enter` control correspond to the AOSP Keyguard PIN view hierarchy. This is a test-harness correction only. Exact-head QA-005 must pass before the credential lifecycle gate is accepted; no result is assumed from this patch.



### SEC-020B4D test-harness update — 2026-11-07

The first exact-head run after replacing IME text injection with visible SystemUI keypad taps exposed three stale Python source-gate assertions: two searched for the removed `shell("input text $TEST_PIN")` call and one expected the old method boundary. The application tests did not run in that Python job; the failure was in static test expectations. Updated `tests/test_sec020b4d_lifecycle_instrumentation.py` to require the new `key0`–`key9` and `key_enter` resource-ID path, ordinary UID 2000, exact SystemUI package/resource checks, visible/enabled/clickable nodes, non-zero bounds, and node/root recycling. The obsolete input-text expectation is now explicitly rejected. A new static regression test covers the helper.

The corresponding Android instrumentation patch is commit `c43985a87cd7dfc2efe12dff8f3b4f0ae3afd2b8`. The Python policy workflow on that commit reported 581 tests with 1 failure and 2 errors, all three in the stale SEC-020B4D source-gate assertions. The updated static suite must pass on the next exact head; QA-005's Android credential callback result is still pending and must not be inferred from the static checks.


## QA-005 Android-test compilation correction — 2026-11-07

**Audit head:** `f0a336fac4ee5cbfc0f492608d92175236ffab93` on `feat/phase1-agentic-phone`. The recursive tree contained 287 entries and was not truncated. PR #1 is open/draft against `main` with 230 commits and 223 changed files; PRs #3–#7 are also open/draft and were left untouched. `PROJECT-ADAPTER.md` and this roadmap are present. Repository `SKILL.md` is absent; the upstream shared engineering-factory package remains unverified and is not claimed as installed.

**Exact-head CI evidence before correction:**
- Phase 1 push [42280766994](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42280766994) and PR [42280778174](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42280778174): passed. Android debug unit tests/build, repeat debug-APK comparison, strict dependency verification and dependency negative control passed; Python policy/static and manifest gates passed.
- CI-003 push [42280766995](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42280766995) and PR [42280778316](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42280778316): passed. Both independent builders and the independent APK/SBOM/toolchain verifier passed.
- QA-005 PR [42280778208](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42280778208): failed before instrumentation execution at `:app:compileDebugAndroidTestKotlin`. Kotlin reported an unterminated string at line 650 in `OwnerAuthorityTrustActivityCommitLifecycleTest.kt`, inside failure-only diagnostics. The emulator setup and debug APK build passed; the disposable synthetic PIN was cleared by the workflow cleanup. Downstream emulator tests were skipped. This is a test-harness compile defect, not evidence of a production app failure.

**Correction:** Close the diagnostic interpolation string after `credentialUiSnapshot()` as part of the concatenation (without a statement terminator). No production Android source, manifest permission, credential logic, device setting or executor is changed. The Python source gates had passed, but they do not parse Kotlin; exact-head QA-005 must recompile and execute instrumentation before this test slice is accepted.

**Local execution:** No local Gradle/Kotlin or emulator tests were run in this environment. Acceptance depends on exact-head GitHub Actions. No physical Pixel 9 Pro was accessed. No milestone is complete; M7 remains blocked on supervised physical-device access and M8 remains blocked.


## QA-005 credential-surface correction — 2026-11-07

**Audit head:** `51a7ddf45597fdeb0189f0ba3938cfd86eca6c63`. The complete recursive tree contains 287 entries and is not truncated. `PROJECT-ADAPTER.md` and this roadmap are present; repository `SKILL.md` is absent. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. PR #1 is open/draft at this head; PRs #3–#7 remain open/draft and were not modified. The latest PR #1 head matches the authorized branch. No independent reviews or inline review threads are present.

**Exact-head CI at `51a7ddf45597fdeb0189f0ba3938cfd86eca6c63`:**
- Phase 1 push [42282581254](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42282581254) and PR [42282592492](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42282592492): passed. Both Python policy jobs reported 582 tests passed. Android Gradle unit tests, debug APK assembly, repeat-build comparison, strict dependency verification and the modified-dependency negative control passed.
- CI-003 push [42282581332](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42282581332) and PR [42282592392](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42282592392): passed; both independent builders and the independent verifier passed.
- QA-005 PR [42282592683](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42282592683): Kotlin instrumentation compilation succeeded and 28 tests executed; 26 passed and two credential-lifecycle cases failed at `exact clickable SystemUI PIN key was not available: key2`. The workflow cleared its disposable emulator PIN. Evidence artifact [13535069923](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42282592683/artifacts/13535069923), including JUnit XML and a pre-cleanup screenshot. No physical device was used.

**Root cause established from the failed test and Android 15 AOSP source:** the test conflated two distinct platform surfaces. The lockscreen Keyguard uses a `KeyguardPINView` with `NumPadKey` controls. Android 15's BiometricPrompt credential view instead contains `auth_credential_input` (a FrameLayout) with a focused `android.widget.ImeAwareEditText` at `lockPassword`; its binder requests focus and handles IME submit/Enter. The previous generic detector accepted an underlying Keyguard `pinEntry` while the BiometricPrompt dialog was active, then incorrectly searched the prompt for a `key2` numpad control that does not exist. This is a test-harness targeting defect, not a production trust-backend failure.

AOSP references used to ground the correction:
- [Android 15 BiometricPrompt credential layout](https://android.googlesource.com/platform/frameworks/base/+/android15-tests-dev/packages/SystemUI/res/layout/auth_credential_password_view.xml)
- [Android 15 BiometricPrompt credential input container and lockPassword field](https://android.googlesource.com/platform/frameworks/base/+/android15-tests-dev/packages/SystemUI/res/layout/auth_credential_password_pin_content_view.xml)
- [CredentialPasswordView focus and input behavior](https://android.googlesource.com/platform/frameworks/base/+/01d329349864f78f7f1b4c774341514e8719eb9c/packages/SystemUI/src/com/android/systemui/biometrics/ui/CredentialPasswordView.kt)
- [CredentialPasswordView IME/Enter submission handler](https://android.googlesource.com/platform/frameworks/base/+/89f6bfea0750a84654cb3a7c80d3dff191a9814c/packages/SystemUI/src/com/android/systemui/biometrics/ui/binder/CredentialPasswordViewBinder.kt)

**Correction on this commit:** split emulator-unlock Keyguard PIN handling from BiometricPrompt credential handling. The Keyguard path requires the complete visible SystemUI PIN pad and exact AOSP `NumPadKey`/`NumPadButton` nodes. The BiometricPrompt path requires a SystemUI root, the exact `auth_credential_input` FrameLayout, and its visible, enabled, focused, password-marked `android.widget.ImeAwareEditText` child with resource ID `lockPassword`. Only after those checks and ordinary ADB shell UID 2000 verification does the harness send the workflow's synthetic PIN through normal input text plus Enter. The value is excluded from diagnostics. No app-owned field, credential bypass, root, Keyguard dismissal API, production app source, permission, trust-store behavior or executor is changed.

The new source gates enforce that the two platform surfaces cannot be confused. Exact-head GitHub Actions must recompile and execute instrumentation before accepting the credential-lifecycle gate. Local Gradle/emulator execution was not performed in this environment.

**Milestones:** M1/M2/M6 remain IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED on supervised physical Pixel 9 Pro validation; M8 BLOCKED. No milestone is complete. Independent human security review remains pending.


## QA-005 static-gate follow-up — 2026-11-07

The first exact-head run for `8b3d10a2dc073ad698b8304bcbffb2fd62f0b451` exposed two stale static-test range markers after the credential helpers were split:
- `test_sec020b4d_lifecycle_instrumentation.py` searched for the Keyguard helper after the BiometricPrompt helper even though the source intentionally defines them separately.
- `test_qa005_workflow_gate.py` still referenced the removed generic `awaitSystemCredentialUi` / `hasVisibleSystemCredentialInput` helpers.

The run executed 583 Python tests; 581 passed and these two source-gate tests errored before assertions. Android build, CI-003 and QA-005 were still in progress at the time of this correction. This commit only aligns the static test boundaries with the two distinct credential surfaces and requires both bounded diagnostic helpers to retain structural evidence. No Kotlin runtime source or production application code changes in this follow-up. Exact-head CI must rerun before acceptance.


## QA-005 static range boundary correction — 2026-11-07

The follow-up exact-head run exposed one further static-test boundary assumption: `awaitKeyguardPinPad` is defined after the `hasVisibleKeyguardPinPad` detector, so using the detector as the end marker produced a reversed range. The QA-005 source gate now locates the next Kotlin helper declaration after each bounded diagnostic function instead of assuming helper declaration order. This is a test-only correction; the runtime credential-surface separation is unchanged. The current-head Python suite must pass before this gate is accepted.


## QA-005 BiometricPrompt accessibility-class correction — 2026-11-07

**Audit head:** `44b7eb22b08de81f19ea1d7f77f8c6dbc9d83436` on `feat/phase1-agentic-phone`. The complete recursive tree contained 287 entries and was not truncated. PR #1 is open/draft against `main`, at the same head, 235 commits ahead and zero behind; PRs #3–#7 remain open/draft on their separate workstreams. `PROJECT-ADAPTER.md` and this roadmap are present. Repository `SKILL.md` is absent; the upstream shared factory package remains unverified and is not claimed as installed. PR #1 has no submitted reviews or inline review threads.

**Exact-head CI at `44b7eb22b08de81f19ea1d7f77f8c6dbc9d83436`:**
- Phase 1 push [42289696231](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42289696231) and PR [42289704965](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42289704965): PASS. Both Python policy jobs reported 583 tests passed; Android Gradle unit tests, debug APK assembly, repeat-build comparison, strict dependency verification and the modified-dependency negative control passed.
- CI-003 push [42289696349](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42289696349) and PR [42289704956](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42289704956): PASS. Both independent builders and the independent-runner verifier passed.
- QA-005 PR [42289704912](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42289704912): instrumentation compilation succeeded and all 28 tests executed; 26 passed and two SEC-020B4D lifecycle tests failed while waiting for the BiometricPrompt credential field. The workflow's cleanup cleared the disposable emulator PIN. Evidence artifact [13538419469](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42289704912/artifacts/13538419469).

**Root cause from the actual API 35 Google APIs emulator evidence:** the prompt did appear. SystemUI logged `AuthController.showAuthenticationDialog`, and the bounded accessibility snapshot contained the exact `com.android.systemui:id/auth_credential_input` FrameLayout and focused, enabled, visible, password-marked `com.android.systemui:id/lockPassword` field. However, UIAutomator reported the field class as `android.widget.EditText`, not `android.widget.ImeAwareEditText`. The test helper's class equality check therefore rejected the real focused system credential field. The failure is a test-harness class-name normalization mismatch, not evidence that the prompt was absent or that production trust persistence failed.

**Correction:** the debug instrumentation now accepts only the two exact observed/platform class names, `android.widget.ImeAwareEditText` and `android.widget.EditText`, while retaining every other constraint: SystemUI package, exact `auth_credential_input` FrameLayout, exact `lockPassword` resource ID, visible/enabled/focusable/focused/password state, positive bounds and node recycling. It does not accept app-owned inputs, arbitrary EditText nodes, Keyguard PIN nodes or Settings fields. A new Python source-gate regression test asserts this narrow allowlist. No production Android source, manifest, permission, credential policy, trust-store, device setting or executor is changed.

**Acceptance boundary:** this correction has not yet been tested on a new exact head. The full Python suite, Android Gradle checks, CI-003 independent reproducibility and QA-005 28-test emulator workflow must rerun. No successful credential lifecycle result is claimed until both previously failing tests pass and the disposable credential cleanup is confirmed. No local Gradle/emulator execution is claimed. No physical Pixel 9 Pro was accessed.

**Milestones:** M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED pending supervised physical Pixel 9 Pro validation; M8 BLOCKED. No milestone is complete. Independent human security review remains pending.


## QA-005 API 35 Keyguard accessibility hierarchy correction — 2026-11-07

**Audit head:** `0b2dd77cdbe1a5e53907a66cb29330ddb0a30542` on `feat/phase1-agentic-phone`. The complete recursive tree contains 287 entries and is not truncated. `PROJECT-ADAPTER.md` and this roadmap are present; repository `SKILL.md` is absent. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. PR #1 is open/draft against `main` at the audited head (236 commits ahead, zero behind); PRs #3–#7 remain open/draft on separate workstreams and were not modified. PR #1 has no submitted reviews or inline review threads.

**Exact-head CI at `0b2dd77cdbe1a5e53907a66cb29330ddb0a30542`:**
- Phase 1 push [42297079971](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42297079971) and PR [42297087138](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42297087138): PASS. Both Python policy jobs executed 584 tests and reported `OK`; launcher source accessibility/recovery and Android source-manifest security gates passed. Android `:app:testDebugUnitTest`, debug APK assembly, repeat debug-APK comparison, strict Gradle dependency verification and modified-dependency negative control passed.
- CI-003 push [42297079986](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42297079986) and PR [42297086999](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42297086999): PASS. Both independent release builders and the independent verifier passed. The unsigned release APKs were byte-identical (7,831,964 bytes, 21 entries; SHA-256 `a8acfc839d7de40d21cf6452989056953060e24eb8dd12f766408f3b029e30f9`); normalized APK content, runtime inventory, SPDX runtime SBOM, release variant and recorded toolchain matched. The verifier correctly reports `release_ready=false`; this is reproducibility evidence, not a signed production release.
- QA-005 PR [42297086987](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42297086987): Kotlin instrumentation compilation succeeded and 28 tests executed; 26 passed and two SEC-020B4D lifecycle tests failed before the trust-transaction scenarios could complete. Artifact [13542627208](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42297086987/artifacts/13542627208) contains JUnit output, logcat and a pre-cleanup screenshot. The screenshot shows the SystemUI PIN bouncer already visible. The accessibility snapshot reports `keyguard_pin_view` as `android.widget.LinearLayout`, `pin_container` as `android.view.ViewGroup`, and digit resource nodes as `android.view.ViewGroup`. The old detector required custom AOSP class names and therefore rejected the real visible bouncer, then attempted to find a device-entry icon that was not visible on that bouncer. Workflow cleanup logged `Lock credential cleared`; the disposable synthetic PIN was removed.

**Correction implemented on the next commit:** replace custom Java class-name equality with exact SystemUI package/resource identity and ancestry: visible `keyguard_pin_view`, nested visible `pin_container`, and the ten digit resource IDs plus `key_enter`. Every target must be a visible, enabled, clickable descendant with positive, on-screen bounds. Taps use only the matching descendant's accessibility bounds and ordinary ADB shell UID 2000. This is instrumentation-only; production Android code, manifest permissions, owner-authentication policy, trust persistence and device execution remain unchanged. The separate BiometricPrompt `auth_credential_input/lockPassword` validation remains intact.

**Acceptance boundary:** the correction is not yet accepted until exact-head Phase 1 push/PR, CI-003 independent reproducibility and QA-005 all 28 instrumentation tests plus downstream launcher/recovery/accessibility steps complete. No physical Pixel 9 Pro was accessed. No StrongBox hardware result, spoken TalkBack acceptance, signed production release, OTA rollback or production readiness is claimed. Independent human security review remains pending.

**Milestones:** M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED pending supervised physical Pixel 9 Pro validation; M8 BLOCKED. No milestone is complete.


### QA-005 source-gate formatting follow-up — 2026-11-07

The first exact-head Phase 1 push/PR Python-policy runs for `b9689cf7031b830a9779860e0ad7a66c194c67b7` each executed 584 tests and failed one source-gate assertion. The failure expected the SystemUI tap command as a single-line `shell("input tap...")` expression, while the implementation intentionally formatted the same `shell("input tap ...")` call across multiple lines. This was a brittle static-test formatting assertion, not a Kotlin compile or emulator result. The source gate now verifies the `shell(` invocation and the exact bounded `input tap` expression independently. A short comment documents that the device-entry icon is only a fallback when the PIN bouncer is not already visible. Runtime behavior is unchanged. The b9689cf QA-005 emulator run was still in SDK setup and is superseded by this source-only/test-comment follow-up; it is not acceptance evidence. New exact-head CI and emulator validation are required.


## Engineering Factory run — 2026-11-07, QA-005 exact-head acceptance and emulator concurrency hardening

**Audit baseline:** feat/phase1-agentic-phone at 818f20b1bc5cc2b2c59854d5e7c4d6567f7f341d. The recursive Git tree contained 287 entries and was not truncated. The latest 20 commits, all six open PRs (#1, #3, #4, #5, #6 and #7), PR #1 head/base/draft/review state, exact-head Actions runs, architecture, tests, PROJECT-ADAPTER.md and this roadmap were inspected. The branch is 238 commits ahead of main and zero behind; main remains f3c9a701d2a337de8ef393ac14df044a79843d60. PR #1 is open/draft and has no submitted reviews. PRs #3–#7 were not modified. Repository SKILL.md is absent from the complete tree. The authorized Library search found no matching upstream shared factory package; the upstream SKILL.md remains unverified and is not claimed as installed. The local PROJECT-ADAPTER.md remains the project-specific adapter.

**Exact-head validation at 818f20b1bc5cc2b2c59854d5e7c4d6567f7f341d: all five workflows passed.**
- Phase 1 push [42305429126](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42305429126) and PR [42305436577](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42305436577): PASS. Each Python policy job ran 584 tests and reported OK; Android :app:testDebugUnitTest, :app:assembleDebug, byte-identical repeat debug APK comparison, strict Gradle dependency verification, modified-dependency negative control, manifest gate and artifact generation passed. The unsigned debug APK SHA-256 was bcbc5d72d3fd0a420d3e0f9be5ac3bee94ee2eecf6e61b44386f55a34ee388f6; it is explicitly not for release.
- CI-003 push [42305428984](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42305428984) and PR [42305436571](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42305436571): PASS. Both independent release builders and the cross-runner verifier passed. Unsigned release APKs were byte-identical: 7,831,964 bytes, 21 entries, SHA-256 a8acfc839d7de40d21cf6452989056953060e24eb8dd12f766408f3b029e30f9; normalized entries SHA-256 4cc2150f1d66384508ab181236d233b7abec5eeebcbeed855a45b43be3aab8b4. Runtime inventory and SPDX runtime SBOM matched. The scoped CI-006 build-environment inventory covered 1,260 components and matched across builders; it is not a complete hosted-runner image SBOM. The verifier explicitly returned release_ready=false; this is unsigned reproducibility evidence, not a signed release.
- QA-005 PR [42305436588](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42305436588): PASS on a disposable API 35 x86_64 emulator. Kotlin instrumentation compilation succeeded; all 28 instrumentation tests passed with zero failures, errors or skips. Both SEC-020B4D commit-boundary tests passed. The workflow confirmed Lock credential cleared. QA-005 through QA-010 passed, QA-013 passed, and QA-020B2/B3 passed. QA-011 correctly remained blocked_service_disabled and is not spoken TalkBack acceptance; QA-012 passed structural semantics only and did not test speech. Evidence artifact [13546453156](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42305436588/artifacts/13546453156), uploaded artifact digest 371825ef72182202805af01c285d904ea8a65d790c3afb7bbb614cc5d693639d.

**Bounded CI reliability correction in this run:** the QA-005 workflow previously used cancel-in-progress: true. Repeated PR-head updates could terminate an active emulator run while its cleanup trap was responsible for removing the disposable synthetic lock PIN. Change the workflow to cancel-in-progress: false, retaining the existing per-PR concurrency group. An active run now completes its cleanup; GitHub keeps a single pending slot for the group, so newer pending PR work supersedes older pending work without interrupting the active emulator. Add a Python source regression test to prevent reintroducing active-run cancellation. No Android application behavior, permission, trust record, emulator credential, physical device or production artifact is changed by this workflow-only slice.

**New commit acceptance:** exact-head Phase 1 and QA-005 reruns are required for the concurrency change. The CI runs above validate the parent 818f20b1bc5cc2b2c59854d5e7c4d6567f7f341d, not the new workflow commit. Do not treat the parent CI as evidence for the new head.

**Milestones remain:** M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete. No physical Pixel 9 Pro was accessed; no physical StrongBox level, spoken TalkBack, signed release, OTA rollback or production readiness is claimed. Independent human security review remains pending.

**Next engineering task:** after the new exact-head CI passes, perform a bounded M3 legacy-agent boundary audit. Keep agents/hermes/agent.py and its unrestricted Termux shell command path explicitly outside the Android app packaging and supervised HERMES executor. Add a deterministic packaging/invocation exclusion gate only if the current build graph does not already prove that boundary. Do not connect shell execution or introduce a real device executor. TalkBack spoken acceptance and physical M7 remain gated on deliberate owner/operator consent and independent review.


## Exact-head acceptance — QA-005 concurrency hardening commit b46082442391f8a11069274c252997d9c294e1d8

All five exact-head workflows for b46082442391f8a11069274c252997d9c294e1d8 completed successfully:

- Phase 1 push [42313258544](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42313258544) and PR [42313265112](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42313265112): PASS. Both Python policy jobs ran 585 tests and reported OK. Both Android jobs passed :app:testDebugUnitTest, :app:assembleDebug, byte-identical repeat debug APK comparison, strict Gradle dependency verification, modified-dependency negative control and artifact generation. The Python suite includes the new regression that rejects cancel-in-progress=true for QA-005.

- CI-003 push [42313258538](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42313258538) and PR [42313265123](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42313265123): PASS. Both independent release builders and both cross-runner verifiers passed. The unsigned release APKs were byte-identical: 7,831,964 bytes, 21 entries, SHA-256 a8acfc839d7de40d21cf6452989056953060e24eb8dd12f766408f3b029e30f9; normalized entries SHA-256 4cc2150f1d66384508ab181236d233b7abec5eeebcbeed855a45b43be3aab8b4. Runtime inventory SHA-256 9b06a5f81611e6fcbf8264ab0793543a02e29a8a7b9ef3c8aa8994b3a32afe8b and SPDX runtime SBOM SHA-256 2631f799c724c8fb61a8fd7791eb37366301e904c49fca04598bfd5228145878 matched. CI-006's scoped build-environment inventory covered 1,260 components and matched across runners; it is not a complete hosted-runner image SBOM. The verifier explicitly reported reproducible=true and release_ready=false. No signed release is claimed.

- QA-005 PR [42313265098](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42313265098): PASS on the disposable API 35 x86_64 emulator. The JUnit report records 28 tests, zero failures, zero errors and zero skips. Both SEC-020B4D lifecycle tests passed. The run log confirms Lock credential cleared. QA-005 through QA-010, QA-013, QA-020B2 and QA-020B3 passed. QA-011 remained blocked_service_disabled and is not spoken TalkBack acceptance. QA-012 passed structural semantics only; spoken navigation was not tested. Evidence artifact [13548769096](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42313265098/artifacts/13548769096).

**QA-005 concurrency hardening is accepted for the workflow/static-policy scope:** cancel-in-progress is false for the existing per-PR concurrency group, the new regression test passed in both 585-test Python jobs, and the active emulator run completed its full workflow and cleanup. The run did not test simultaneous PR updates, so queue replacement behavior is not separately stress-tested.

The previous statement that exact-head acceptance was pending is superseded by these five successful runs. This acceptance applies to the exact source/workflow head b46082442391f8a11069274c252997d9c294e1d8. This addendum is documentation-only and does not change Android code, the QA workflow or test sources.

Milestones remain M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete. No physical Pixel 9 Pro was accessed, no physical StrongBox level was established, no spoken TalkBack acceptance was performed, and no signed production release or OTA rollback was tested. Independent human security review remains pending.

Next task: audit and enforce the boundary between legacy Termux shell-based agents and the Android app/supervised HERMES path. First prove whether the current Gradle source/resource graph can package or invoke agents/hermes/agent.py. Add a deterministic exclusion gate only if no existing gate already establishes the boundary. Do not connect arbitrary shell execution or introduce a real device executor.


## Engineering Factory audit — 2026-11-07, legacy-agent boundary and M3 execution contract

**Audit baseline:** `feat/phase1-agentic-phone` at `dc175f388e780b041bcc398b96047ae1719099d6`. The GitHub recursive tree returned 287 entries with `truncated=false`; the latest 20 branch commits were inspected. PR #1 is open/draft, base `main`, head `dc175f388e780b041bcc398b96047ae1719099d6`, 240 commits and 223 changed files. PRs #3–#7 remain open and were not modified. PR #1 has no submitted reviews or inline review threads. Repository rulesets returned an empty list; branch-protection enforcement was not independently established. `PROJECT-ADAPTER.md` and this roadmap are present. Repository `SKILL.md` is absent (GitHub contents API returned 404); the Library shared-with-me listing was empty and semantic search found no authorized upstream package. The upstream shared `SKILL.md` remains unverified and is not claimed as installed.

**Exact-head CI at `dc175f388e780b041bcc398b96047ae1719099d6`: all five push/PR workflows passed.**
- Phase 1 push [42314340133](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42314340133) and PR [42314347627](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42314347627): PASS. Each Python policy job ran 585 tests and reported OK. Android `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat debug APK byte comparison, strict dependency verification and the modified-dependency negative control passed. The Android source-manifest security gate passed.
- CI-003 push [42314340202](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42314340202) and PR [42314347897](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42314347897): PASS. Two independent builders produced byte-identical unsigned release APKs: 7,831,964 bytes, 21 entries, SHA-256 `a8acfc839d7de40d21cf6452989056953060e24eb8dd12f766408f3b029e30f9`; normalized entries SHA-256 `4cc2150f1d66384508ab181236d233b7abec5eeebcbeed855a45b43be3aab8b4`. Runtime inventory and SPDX runtime SBOM matched. CI-006's 1,260-component inventory is scoped, not a complete hosted-runner image SBOM. The verifier explicitly returned `reproducible=true`, `release_ready=false`.
- QA-005 PR [42314347960](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42314347960): PASS on a disposable API 35 x86_64 emulator. Job logs show 28 instrumentation tests started and finished, zero failures and zero skips; the workflow completed successfully and confirmed `Lock credential cleared`. QA-005 through QA-010, QA-013, QA-020B2 and QA-020B3 passed. QA-011 remained `blocked_service_disabled` (not spoken TalkBack acceptance); QA-012 was structural semantics only (no spoken navigation).

**Legacy-agent boundary decision:** the native Android module includes only `:app`; the root Gradle build declares Android/Kotlin plugins only; the app build has no Python plugin/runtime, external source-set inclusion or Termux dependency. All 32 Android main/debug Kotlin source files were inspected for process-launch/shell/Termux/legacy-agent references; no such invocation path was found. The main manifest contains no agent service or shell bridge. The separate Termux Python runtime does contain `shell=True` in `agents/hermes/agent.py` and `agents/openclaw/agent.py`, and `core/main.py` starts agent scripts using `subprocess.Popen`. These remain outside the native app. Because the current build/source graph already proves the present separation, no duplicate packaging gate was added. Revisit if Python runtime/plugin, external source set, agent assets, IPC bridge or process-launch API is introduced.

**M3 design deliverable:** added [M3-SUPERVISED-EXECUTION-CONTRACT.md](M3-SUPERVISED-EXECUTION-CONTRACT.md). It documents the current Boolean-authentication prototype limitations, transport/consent/Android-permission separation, typed action registry, idempotency/cancellation state machine, redacted audit requirements and 14 adversarial acceptance cases. Design only: no listener, executor, permission grant, shell bridge or device action was connected.

**Milestones:** M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete. No physical Pixel 9 Pro/StrongBox validation, spoken TalkBack acceptance, signed release, OTA rollback or production readiness is claimed. Independent human security review remains pending.

**Next bounded task:** implement the M3 verified-session/capability admission contract as a pure JVM/Python testable boundary with a fake/no-op executor only. Remove the production-facing Boolean authentication parameter or ensure no production call path can reach it. Add adversarial tests for identity binding, consent digest, expiry, replay, idempotency, permission revocation, cancellation and audit failure. Keep network listener, real Android executor and device integrations disconnected until independent security review.


## Engineering Factory run — 2026-11-07, CI-003 reproducibility concurrency hardening

**Audit baseline:** `feat/phase1-agentic-phone` at `61423daa199f45ad58a063b86043b0575154ecab`. The recursive Git tree contains 288 entries and is not truncated. The branch is 241 commits ahead of `main` and zero behind (merge base `f3c9a701d2a337de8ef393ac14df044a79843d60`). The latest 20 commits, six open PRs (#1 and #3–#7), PR #1 head/base/draft/review state, current-head Actions runs, adapter, roadmap, M3 contract, Android manifest/build graph and Python/Android admission prototypes were inspected. PR #1 is open/draft and its head matches the authorized branch; its long description contains an older “Current head” line and needs a fresh evidence comment. PRs #3–#7 were not modified. The complete tree contains `PROJECT-ADAPTER.md` and no `SKILL.md`; the upstream shared factory package remains unverified and is not claimed as installed.

**Baseline exact-head validation at `61423daa199f45ad58a063b86043b0575154ecab`:** Phase 1 push [42321787036](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42321787036) and PR [42321790688](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42321790688), CI-003 push [42321787132](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42321787132) and PR [42321790692](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42321790692), and QA-005 PR [42321790666](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42321790666) all completed successfully. The Python jobs reported 585 tests passed each; Android debug/release unit/build/dependency-verification gates passed; CI-003 independent unsigned release builds and verifier passed; QA-005 completed 28 instrumentation tests on a disposable API 35 x86_64 emulator. QA-011 remained service-disabled and QA-012 remained structural-only, not spoken TalkBack. The emulator is not a physical Pixel 9 Pro.

**Finding:** QA-005 already uses `cancel-in-progress: false` so a new PR head cannot interrupt an active emulator run whose EXIT cleanup clears a disposable synthetic PIN. CI-003 still used `cancel-in-progress: true` for its per-PR/ref concurrency group. A new commit could therefore cancel one or both independent release builders or the cross-runner evidence verifier before they finish. This loses reproducibility evidence and can leave an incomplete run presented alongside newer work. CI-003 already pins checkout to the exact PR head SHA or push SHA and has `fail-fast: false` for its two-builder matrix.

**Bounded correction:** change only CI-003 concurrency to `cancel-in-progress: false`, preserving its existing group key and exact-head checkout. An active run can finish; GitHub retains one pending run per group, with newer pending work replacing older pending work. Add `tests/test_ci003_workflow_gate.py` with regression assertions for the group key, non-cancellation, independent matrix behavior and exact event-SHA checkout. The existing `scripts/phase1-preflight.sh` uses unittest discovery, so no duplicate test runner or workflow is introduced. No Android app, permission, owner trust, transport, signing key, executor or device behavior is changed.

**Acceptance status at commit submission:** the source/static regression is added but exact-head Python/Gradle, independent release reproducibility and QA-005 reruns for the new commit are PENDING. The successful baseline runs above are parent-head evidence only. Do not claim acceptance until new-head CI completes.

**M3 security finding retained:** `core/command_admission.py` still exposes the prototype `transport_authenticated: bool`; Android `CommandRouter.execute` still accepts `authenticatedByTransport: Boolean`. The mTLS owner-consent adapter has a stronger live-socket verifier, but its `AuthenticatedOwnerSession` data class explicitly says it is not proof when constructed by arbitrary Python callers. The next M3 task must introduce a verifier-originated capability boundary and keep the executor fake/no-op. Do not treat a typed wrapper around a caller-created identity snapshot as authentication. No listener, shell bridge, production transport or real device executor is authorized.

**Milestones:** M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete. Independent human security review, spoken TalkBack, physical Pixel 9 Pro/StrongBox, signed release, OTA rollback and production readiness remain unverified.

**Next task:** after exact-head CI-003 hardening passes, implement the narrow M3 verified-session/capability admission boundary. The verifier must own session construction and revalidate live transport/enrollment; caller-populated identity structures and Booleans must not authorize admission. Add adversarial tests and a fake/no-op executor only. Keep the network listener, Android permission grants and device integrations disconnected.


## Engineering Factory run — 2026-11-07: M3 opaque capability and no-op harness

**Audit baseline:** branch feat/phase1-agentic-phone at d391efe042c3d3fc0d2aa82a91fa317fa567f26c. The complete recursive tree contains 292 entries (truncated=false). The latest 20 commits and all six open PRs (#1, #3–#7) were inspected. PR #1 is open/draft, targets main, is mergeable, and its head matches the authorized branch. The branch reports protected=false; repository rulesets are empty. PROJECT-ADAPTER.md and this roadmap exist; no repository SKILL.md exists. The authorized upstream shared factory package remains unverified and is not claimed as installed. No active Actions runs were present before implementation.

**Exact-head baseline CI:** Phase 1 push 42330061428 and PR 42330066165, CI-003 push 42330061350 and PR 42330066357, and QA-005 emulator PR 42330066251 all completed successfully. Each Phase 1 Python job ran 592 tests and passed; Android debug unit tests/build, repeat debug APK comparison, strict dependency verification and tampered-dependency negative control passed. Both CI-003 independent release builders and the verifier passed. QA-005 completed 28 instrumentation tests on a disposable API 35 x86_64 emulator and confirmed credential cleanup. The earlier parent commit 16637d15 had one stale source-string assertion failure; commit d391efe corrected the assertion to the new risk-only API, and the current exact-head jobs passed. These results do not establish physical Pixel 9 Pro or spoken TalkBack acceptance.

**Bounded M3 implementation:** the mTLS adapter now mints an opaque one-use VerifiedOwnerActionCapability only after live-socket transport verification and owner-signature/nonce consumption. To avoid pretending v1 signs arguments, the capability path is limited to read_screen with an exactly empty argument object. It stores a domain-separated argument digest and adapter-private object identity, then rechecks live TLS peer, transport enrollment/generation, owner/device enrollment, consent-key digest and monotonic expiry before one-use consumption. A new core/noop_action_executor.py consumes the capability and reports SIMULATED_ONLY; it never performs a device action. Tests cover caller-constructed handles, action/argument mismatch, socket transfer, replay, transport revocation, consent-key rotation, enrollment revocation, expiry and registry outage/retry.

**Safety boundary:** no v1 non-empty action arguments are admitted; navigate and scroll are not supported by the new capability path. The Python capability is an in-process trusted-host object, not protection against arbitrary malicious code in that interpreter. No Android permission query, listener, shell bridge, Android executor, screen capture, call/message, device action, physical hardware operation, firmware flash, OTA or signed release was added. Android CommandRouter remains fail-closed. Independent human security review remains pending.

**Milestones:** M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete.

**Next bounded task:** define protocol v2 with a canonical, signed digest of non-empty action arguments and an owner-visible Android preview that renders those exact arguments before per-use signing. Add shared Kotlin/Python fixtures and mutation tests. Keep actual device execution disabled until the verifier capability is mirrored into the JVM boundary and Android runtime permissions are revalidated.

## Independent review correction — M3 capability provenance

A follow-up security review of the opaque no-op capability found and corrected two TOCTOU/context issues before acceptance: the verifier result now returns the digest of the exact consent public key used for signature verification and nonce consumption, and capability minting refuses if the registry key has changed since that verification. Consumption now also checks the current transport registry owner/device mapping and credential generation against the captured capability context, and verifies challenge owner/device identity. Three new adversarial tests cover post-consumption key rotation, owner/device remapping and generation change. These corrections remain admission/no-op only; a real executor still needs an atomic durable final authorization/idempotency reservation.

## CI fixture correction — deterministic nonce uniqueness

The first exact-head run of f0341bef exposed one Python test-fixture failure: the owner/device-remapping test iterated twice while its deterministic nonce factory returned the same fixed nonce, so the second independent fixture correctly hit the replay ledger. Production admission behavior was not the failing assertion. The test now uses distinct deterministic nonce values for each loop case, preserving replay protection and making the two remapping cases independent. The f0341bef Python jobs ran 605 tests with one fixture failure; CI-003 push and PR passed, while Phase 1 and QA-005 exact-head results were still being evaluated at the time of this correction.



## 2026-11-07 — AGENT-004G argument-bound consent protocol v2 (submitted)

Audit baseline: feat/phase1-agentic-phone at 58acdf4c116af4a316bc3d356d9a01823bedbcf1. The complete recursive tree contained 294 entries and was not truncated. The latest 20 feature-branch commits and all six open PRs (#1, #3–#7) were inspected. PR #1 is open/draft and points at the authorized branch; PRs #3–#7 remain open/draft on their own branches and were not modified. The branch reports protected=false. PROJECT-ADAPTER.md and this roadmap are present; no repository SKILL.md exists. An authorized Library search for SKILL.md and PROJECT-ADAPTER.md returned no result; the upstream shared factory package remains unverified and is not claimed as installed.

At the audit head, Phase 1 push/PR runs 42333362219 and 42333366598 passed; CI-003 push/PR runs 42333362255 and 42333366527 passed. QA-005 PR run 42333366480 was still in progress at the time of implementation; its result is not substituted for exact-head evidence. The current branch was 247 commits ahead of main and zero behind, with merge base f3c9a701d2a337de8ef393ac14df044a79843d60.

AGENT-004G adds protocol v2 signed argument binding. Python defines strict canonical JSON and domain-separated SHA-256 for read_screen (empty object), navigate (exact target_package), and scroll (exact direction plus bounded distance_dp). Host challenge issuance selects v1 when arguments are omitted and v2 when an explicit argument object is supplied. The Python verifier accepts exact version-specific payload key sets and checks the signed argument digest against the host-issued challenge before atomic nonce consumption. Kotlin has a matching closed typed argument model, canonical JSON/digest and shared v2 fixture. OwnerConsentSigner now places the exact canonical argument JSON in the owner-visible BiometricPrompt description before signing.

The mTLS adapter can issue and verify v2 challenges, but it explicitly refuses to mint a v2 action capability with V2_CAPABILITY_NOT_INTEGRATED. The existing v1 no-op capability remains read_screen/empty-arguments only. This is admission-only: no Android executor, runtime permission grant, listener, screen capture, navigation, scrolling, shell bridge or production caller was connected. Synthetic mTLS and JVM tests do not establish physical StrongBox or Pixel 9 Pro behavior.

New/updated tests cover the shared v2 fixture, strict argument schemas, signed digest, tamper rejection without nonce consumption, replay, live synthetic mTLS verification, v2 capability refusal and owner-visible signer prompt source contract. Exact-head Phase 1, CI-003 and QA-005 workflows are pending. No local repository tests are claimed because the repository was not available in the execution container. Independent human security review remains pending.

Milestones remain M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete.

Next task: independently review v2 canonicalization and add v2 opaque capability minting only after the exact action/argument digest, owner-visible preview and live transport context are verified. Keep real device execution disabled; a future executor must perform atomic final authorization/idempotency reservation and fresh Android runtime-permission checks.


## 2026-11-07 — AGENT-004G v2 opaque capability admission (submitted)

Audit baseline: `1a7899c1977a0384ea9e85dd826db00e37afdf05`. The current 298-entry recursive tree is complete and not truncated. The authorized branch remains `feat/phase1-agentic-phone`, 249 commits ahead of `main` and zero behind. PR #1 remains open/draft with no submitted reviews or inline threads; PRs #3–#7 were not modified. `PROJECT-ADAPTER.md` and this roadmap exist; repository `SKILL.md` is absent and the upstream shared factory package remains unverified.

The live mTLS adapter now supports opaque one-use capabilities for protocol v2 as well as the existing v1 path. V1 remains restricted to `read_screen` with empty arguments. V2 recomputes the strict canonical action-argument digest before signature verification/nonce consumption and requires an exact match with the signed challenge. The capability records protocol version and digest; consumption recomputes the digest and checks the retained challenge version/digest plus existing live transport, peer identity, enrollment, credential generation, consent-key and monotonic-expiry bindings. Argument mismatch does not consume a valid challenge or capability. New local-mTLS tests cover `navigate` and `scroll`, altered-argument rejection, one-use consumption and no-op-only outcomes.

The only capability consumer remains `NoOpActionExecutor`; every accepted result reports `SIMULATED_ONLY` and `device_actions_executed=false`. No Android executor, listener, runtime permission grant, screen capture, navigation, scrolling, shell or other device-side effect is connected. Exact-head candidate CI is pending at submission; the five parent-head workflows had passed. Independent human security review remains pending. No physical Pixel 9 Pro, StrongBox, spoken TalkBack, signed release, OTA rollback or production readiness is claimed.

Milestones: M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete.

Next task: design and independently review durable final authorization/idempotency reservation and fresh Android runtime-permission revalidation before any real executor is considered.


## Engineering Factory run — 2026-11-07, AGENT-004H durable final-action reservation

**Audit baseline:** authorized branch feat/phase1-agentic-phone at 52e9300433a8ee45512d2249c53cbf6f9af5ec4c. The recursive tree contained 299 entries and was not truncated; the latest 20 commits, all six open PRs, PR #1 diff/reviews/threads/comments, exact-head Actions jobs, adapter, roadmap, M3 contract, transport adapter, replay ledger, Android CommandRouter and preflight test discovery were inspected. The branch is 250 commits ahead of main and zero behind. PR #1 remains open/draft against main and matches the branch. PRs #3–#7 remain separate workstreams and were not modified. Branch API reports protected=false; repository rulesets are empty. PROJECT-ADAPTER.md and this roadmap exist; repository SKILL.md is absent; the upstream shared factory package remains unverified and is not claimed as installed.

**Exact-head baseline at 52e9300433a8ee45512d2249c53cbf6f9af5ec4c:** Phase 1 push [42339345801](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42339345801) and PR [42339348528](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42339348528) passed; both Python policy jobs ran 614 tests. CI-003 push [42339345884](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42339345884) and PR [42339348497](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42339348497) passed; independent runners produced byte-identical unsigned APKs (7,835,688 bytes, 21 entries, SHA-256 1aadb8e522b976d3a3f93b40232d55f30b05185108efe6338410f6251ad2b929), matching normalized contents, runtime inventory, SPDX SBOM and scoped build-environment inventory. The verifier reported reproducible=true and release_ready=false. QA-005 emulator PR [42339348626](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42339348626) passed; the workflow completed its 28-test instrumentation suite and confirmed credential cleanup. QA-011 reported blocked_service_disabled; QA-012 was structural only, not spoken TalkBack. This was a disposable API 35 x86_64 emulator, not a Pixel 9 Pro.

**Selected bounded task:** close the durable final-action reservation gap without enabling execution. The existing DurableReplayLedger in core/command_admission.py records a generic device/command replay marker; it does not persist owner/session/capability/argument/credential binding or action lifecycle/outcome state. A separate specialized store is therefore required rather than duplicating or replacing that legacy admission prototype.

**Implementation:** add core/action_reservation.py and tests/test_action_reservation.py. The deterministic idempotency key binds owner, device, session, consent nonce/version, action, canonical argument digest, signed validity window, transport certificate, credential generation and consent public-key digest. SQLite uses a dedicated owner-only file, WAL, synchronous FULL, schema versioning, bounded capacity, BEGIN IMMEDIATE transactions and a unique owner/device/nonce constraint. Same binding is a read-only replay; changed binding conflicts. RESERVED can be claimed exactly once as DISPATCH_STARTED; cancellation or pre-dispatch denial is terminal; outcomes are redacted code/digest only. DISPATCH_STARTED is sticky across restart; it is never automatically reclaimed or blindly retried. Raw arguments and results are not stored.

**Android permission contract:** documented but not implemented. A future Android PermissionGate must query the current OS permission/role/service state after reservation and immediately before the platform API call. Planning-time/cached Boolean values are not authority. A revoked permission before dispatch records FAILED_NO_EFFECT and prevents claim. If a platform call has started and the effect is uncertain, record UNKNOWN_OUTCOME. No permission is declared, requested or granted by this change.

**Local scratch verification:** python3 -m compileall -q core tests — PASS. python3 -m unittest discover -s tests -p 'test_*.py' -v — 35 PASS. These commands ran against an isolated scratch copy containing the new module and test file only; they are not a full repository preflight. Exact-head GitHub CI and emulator reruns for the new commit are pending at submission. Independent human security review remains pending.

**Safety:** no mTLS adapter integration, Android PermissionGate, listener, shell bridge, real executor, runtime permission grant, device action, physical Pixel 9 Pro operation, firmware flash, OTA or production deployment was added. The reservation module is storage only; its public request dataclass is not proof of authorization. A trusted adapter must construct requests from its retained verified capability. A persisted reservation never reconstructs a lost live capability.

**Milestones:** M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete.

**Next task:** integrate the ledger behind an adapter-owned method that revalidates the exact live mTLS socket, enrollment, consent key/generation, argument digest and monotonic expiry before creating/claiming a reservation; then implement an Android Context-backed, action-specific PermissionGate with fresh OS queries and JVM tests. Keep CommandRouter fail-closed and the executor disconnected until independent security review.


## Engineering Factory run — 2026-11-07, AGENT-004I adapter-owned durable reservation

**Audit baseline:** PR #1 is open/draft, targets main, and its head matched feat/phase1-agentic-phone at 9ea8d92da1d42f2f6d69f82ba3b796d22e44ea57; the branch was 251 commits ahead and zero behind, with merge base f3c9a701d2a337de8ef393ac14df044a79843d60. The five other open PRs are #3–#7 and were left untouched. The current recursive Git tree endpoint is not exposed by the connected GitHub actions in this run; the latest commit's changed-file list and the project adapter, roadmap, M3 contract, mTLS adapter, reservation ledger, tests and preflight script were read directly. The current head added core/action_reservation.py, its 35-test suite and AGENT-004H documentation. PROJECT-ADAPTER.md exists; SKILL.md is absent. The authorized upstream shared factory package remains unverified and is not claimed as installed.

**Exact-head baseline at 9ea8d92da1d42f2f6d69f82ba3b796d22e44ea57:** Phase 1 run [42344382662](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42344382662) passed both android and python-policy jobs; the Python log reported 647 tests passed. Android :app:testDebugUnitTest, :app:assembleDebug, repeat debug APK comparison, strict Gradle dependency verification and the modified-dependency negative control passed. CI-003 run [42344382607](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42344382607) passed both independent builders and the verifier. The unsigned release APKs were byte-identical (7,835,688 bytes; 21 entries; SHA-256 1aadb8e522b976d3a3f93b40232d55f30b05185108efe6338410f6251ad2b929); normalized contents matched; runtime SBOM and scoped 1,260-component build-environment inventory matched. Provenance reports reproducible=true, release_ready=false. QA-005 run [42344382604](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42344382604) passed 28/28 emulator instrumentation tests, including the existing launcher/recovery, owner trust UI and credential-only debug probe. QA-011 reported blocked_service_disabled; QA-012 was structural only, not spoken TalkBack. This was a disposable API 35 x86_64 emulator, not a physical Pixel 9 Pro.

**Selected bounded task:** integrate AGENT-004H behind the verifier-owned mTLS adapter without enabling dispatch. OwnerConsentTlsAdapter now shares _validated_action_capability_locked between no-op consumption and durable reservation. The helper checks the exact live socket/TLS context/ALPN, active transport certificate, owner/device/session binding, transport credential generation, retained challenge nonce/version/action/digest, current owner enrollment and consent-key digest, and repeated monotonic/wall-clock expiry. It re-reads the transport registry and owner enrollment after the initial validation immediately before the durable operation. The adapter, not the caller, constructs ActionReservationRequest from the retained _IssuedActionCapability and _IssuedChallenge.

reserve_action_capability creates only a durable RESERVED row and consumes the in-memory capability after a definitive ledger decision. Argument mismatch does not consume it. Transport/enrollment registry outages and reservation-store errors fail closed; the short-lived capability is retained only for a bounded retry. Duplicate nonce/binding is IDEMPOTENT_REPLAY, not a second reservation. If the challenge expires during the SQLite operation, the adapter attempts a durable pre-dispatch cancellation and reports reconciliation required if cancellation cannot be proven. The method never calls claim_dispatch, never queries Android permissions and never invokes a platform API. It returns a reservation identifier for trusted host bookkeeping only; it is not a bearer authorization token.

**Regression tests added:** successful v2 reservation and exact durable binding; argument substitution denial with correct retry; transport revocation and capability discard; consent-key rotation before and between consecutive registry reads; registry outage/retry; storage exception/retry; duplicate nonce replay; monotonic expiry; and expiry during commit with durable cancellation. Ten new mTLS adapter tests are included in the existing unittest discovery; no duplicate runner or workflow was added.

**Safety and limitations:** no Android PermissionGate, listener, shell bridge, dispatch claim, executor, permission declaration/grant, screen capture, navigation, scrolling, communication, device action, physical Pixel 9 Pro operation, firmware flash, OTA or production deployment was added. A future Android coordinator must perform fresh action-specific OS permission/role/service checks after reservation and again immediately before the platform API call, and must revalidate transport/enrollment at final dispatch. The reservation store is one-host SQLite, not a distributed lock. Independent human security review remains pending.

**Milestones:** M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete.

**Next task:** implement a pure-JVM Android PermissionGate contract plus Context-backed action-specific checks for navigate, scroll and read_screen, with fake-platform tests for revocation, missing role/service, visibility and failure. Keep the gate unconnected to CommandRouter and do not claim dispatch readiness. The subsequent coordinator must atomically order durable reservation, fresh permission preflight, one-use dispatch claim and immediate pre-call permission recheck under independent security review.


## Engineering Factory run — 2026-11-07, AGENT-004J action-specific Android platform gate

**Audit baseline:** authorized branch `feat/phase1-agentic-phone` at `60ce65107c56ead9714052a5697957f915797074`. The complete recursive tree contained 302 entries and was not truncated. The latest 20 commits were inspected; compare against `main` reported 257 commits ahead and zero behind, with merge base `f3c9a701d2a337de8ef393ac14df044a79843d60`. Six PRs remain open/draft: #1 and #3–#7. PR #1 targets `main`, matched the authorized branch head, and had zero submitted reviews and zero inline review threads. Other PRs were not modified. `PROJECT-ADAPTER.md` and this roadmap exist; repository `SKILL.md` is absent. The authorized upstream shared factory package remains unverified and is not claimed as installed.

**Exact-head baseline at 60ce651:** Phase 1 push [42345869102](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42345869102) and PR [42345872893](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42345872893) passed; each Python policy job ran 657 tests, and each Android job passed debug unit tests/build, repeat debug APK comparison and strict dependency verification. CI-003 push [42345869044](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42345869044) and PR [42345872908](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42345872908) passed both independent builders and the verifier. QA-005 PR [42345872872](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42345872872) completed 28/28 API 35 x86_64 emulator instrumentation tests with zero failures. This was an emulator, not a physical Pixel 9 Pro. QA-011 remains blocked because TalkBack service was disabled; QA-012 is structural only, not spoken TalkBack acceptance.

**Architecture audit:** the complete tree already contains `ScreenActionPreflight.kt`, `ScreenActionPreflightTest.kt`, and SEC-014F documentation. That is a coarse screen-safety policy plus a read-only enabled-service probe, not an action-specific platform gate. `OwnerActionArguments` already supplies the closed typed v2 argument model. `OwnerConsentTlsAdapter.reserve_action_capability` creates a durable RESERVED record but does not claim dispatch or query Android state. `CommandRouter` continues to reject every request with `VERIFIED_TRANSPORT_SESSION_REQUIRED`. The manifest has no AccessibilityService or MediaProjection service and does not declare broad package visibility.

**Selected bounded task:** implement the roadmap's next unblocked task without duplicating SEC-014F or enabling dispatch: a pure-JVM action-specific policy contract and a read-only Context-backed Android probe.

**Implementation:** `ActionPermissionGate` consumes the existing typed `OwnerActionArguments` and validates them with the existing canonicalizer. `navigate` checks only the exact package's launch intent, explicit component, exported/enabled ActivityInfo, enabled application and any activity permission already held by this app. `scroll` requires the existing exact app-owned enabled-accessibility-service probe plus a separate app-owned connected-service probe. `read_screen` requires a separate app-owned active user-approved projection-session probe. The two future service/session probes default to false. Each evaluation performs fresh reads; platform exceptions fail closed. The result is named `PlatformPrerequisitesPresent` and is explicitly not authorization. The new gate is not connected to CommandRouter, the reservation ledger, an executor or any device action.

**Tests actually run locally:** seven Kotlin test methods were invoked with a temporary pure-JVM harness and minimal JUnit stubs — PASS. The Android adapter and pure gate compiled with `kotlinc` against minimal local Android API stubs — PASS; this is syntax/type-shape validation only, not an Android SDK build. Six new Python source-boundary tests ran with `python3 -m unittest` — PASS. The repository could not be cloned into the local container because DNS/network access to github.com was unavailable; no local full-repository preflight is claimed. Exact-head GitHub CI for the new commit is required.

**Safety:** no manifest change, permission request/grant, AccessibilityService, MediaProjection service, listener, shell bridge, executor integration, screen capture, navigation, scrolling, device operation, firmware flash, OTA or deployment was added. The default screen-action probes deny because the corresponding app-owned runtime providers do not exist yet. Independent human security review remains pending.

**Milestones:** M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete.

**Next task:** design the app-owned AccessibilityService and MediaProjection session-provider lifecycle, with visible/revocable user controls and process-death handling, while keeping CommandRouter fail-closed. Only after independent security review should a coordinator order reservation, fresh permission recheck, one-use dispatch claim and immediate pre-call recheck.


**CI source-guard correction before acceptance:** the first exact-head Phase 1 push Python-policy run [42347711335](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42347711335) ran 663 tests and failed one existing `test_command_router_source` guard. The guard intentionally treats any `CommandRouter` mention in non-router Kotlin source as a call-site; the new adapter's explanatory comment triggered that conservative source scan even though no call existed. The adapter comment was narrowed to avoid the symbol reference; no behavior or wiring changed. The new head must pass a complete exact-head CI rerun before acceptance.


## Engineering Factory run — 2026-11-07, M3 platform session lifecycle registry

**Audit baseline:** branch `feat/phase1-agentic-phone` at `a58f26f7cd8145c5362899e7159a8e03d5020a77`. Recursive tree: 307 entries, not truncated. Latest 20 commits inspected; comparison with `main`: 259 ahead, zero behind; merge base `f3c9a701d2a337de8ef393ac14df044a79843d60`. Six open PRs (#1 and #3–#7). PR #1 is open/draft, targets `main`, and matched the authorized head; zero submitted reviews and zero inline review threads. Other PRs were left untouched. Repository rulesets returned an empty list; branch-protection enforcement is unverified because the connected GitHub integration could not read the branch-protection endpoint. `PROJECT-ADAPTER.md` and this roadmap are present; repository `SKILL.md` is absent. The authorized upstream shared factory package remains unverified and is not claimed as installed.

**Exact-head baseline:** Phase 1 push [42347787175](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42347787175) and PR [42347791687](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42347791687) passed; each Python policy job ran 663 tests, and Android debug unit tests/build, repeat APK comparison, strict dependency verification and negative control passed. CI-003 push [42347787189](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42347787189) and PR [42347791730](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42347791730) passed both independent builders and verifier. QA-005 PR [42347791710](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42347791710) completed 28/28 instrumentation tests on a disposable API 35 x86_64 emulator. QA-011 remains blocked because the TalkBack service was disabled; QA-012 is structural only, not spoken TalkBack acceptance. No physical Pixel 9 Pro test occurred.

**Selected task:** implement the next safe prerequisite after AGENT-004J without declaring or connecting an Android service: a pure-Kotlin process-local lifecycle registry for future app-owned AccessibilityService and MediaProjection session providers.

**Implementation:** `ActionPermissionSessionRegistry.kt` keeps separate ACCESSIBILITY and PROJECTION leases, binds callbacks/observations to the exact app package, assigns monotonic process-local generations, and permits only the exact current lease object to end a slot. Replaced-session callbacks cannot revoke a newer lease. Probe adapters expose fresh current-state reads. Process recreation starts empty; leases are never persisted. The lease is an in-process lifecycle handle only, not identity, consent, permission or authorization.

**Tests:** 11 pure-JVM lifecycle test methods and 5 Python source-boundary tests were added. Local `kotlinc` compilation and a custom JVM harness passed; all 11 Kotlin test methods passed using a minimal JUnit-compatible harness; all 5 Python source-boundary tests passed against a scratch repository layout. This is not a local Gradle build or full repository preflight. Exact-head GitHub CI after commit is required.

**Safety:** no Android service declaration, manifest permission, system prompt, foreground service, accessibility setting change, MediaProjection session, listener, shell bridge, executor integration or device action was added. `CommandRouter` remains fail-closed. Independent human security review remains pending.

**Milestones:** M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete.

**Next task:** owner-visible disclosure/revocation UX and narrowly scoped AccessibilityService lifecycle design. Keep the service undeclared until independent security/accessibility review accepts the disclosure, settings handoff, revocation and stop behavior. MediaProjection remains separate.


## Engineering Factory run — 2026-11-07, AGENT-004L owner Accessibility disclosure

Audit baseline: 43ad1c83fa46d3d3305d5a96948cb171d8f0e8f7; complete recursive tree 312 entries, not truncated; 20 recent commits inspected; branch 260 ahead of main, zero behind. Six PRs (#1, #3–#7) are open/draft. PR #1 matches the authorized branch and has no submitted reviews or inline threads. PROJECT-ADAPTER.md is present; repository SKILL.md is absent; upstream shared package remains unverified. Branch metadata reports protected=false; rulesets are empty and the protection-detail endpoint returned 403, so required-review enforcement is unverified.

Baseline exact-head workflows at 43ad1c83 passed: Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR. The two Python policy jobs each reported 668 tests passed; Android debug unit/build/repeat-build/dependency gates passed; CI-003 unsigned release reproducibility passed; QA-005 completed all steps on a disposable API 35 x86_64 emulator. QA-011 is only a TalkBack availability preflight and QA-012 structural semantics, not spoken acceptance.

AGENT-004L adds a non-exported owner-visible Accessibility disclosure Activity, a fresh exact-component status reader, explicit Settings handoff, launcher entry, pure-JVM state tests, instrumentation tests and Python source-boundary tests. ScreenActionPreflight now shares the centralized future service component name. The current manifest still declares no AccessibilityService or MediaProjection service and no new permissions. No automatic Settings launch, programmatic service toggle, screen capture, gesture, permission grant, executor or CommandRouter connection was added.

Local pure-JVM harness: five state scenarios passed. Exact-head Phase 1, CI-003 and QA-005 reruns are pending at commit preparation. No local Android Gradle build/emulator is claimed because the local container has no Android SDK. Independent human security/accessibility review remains pending. No milestone is complete: M1/M2/M6 in progress; M3 partial; M4 not started; M5 not accepted; M7 blocked; M8 blocked.

Next gate: independent security/accessibility review before declaring a narrowly scoped AccessibilityService; then wire only real service lifecycle callbacks to the exact session lease and test reconnect, process death, stale callbacks, revocation, stop behavior and TalkBack coexistence. MediaProjection remains separate.


## Engineering Factory run — 2026-11-07, AGENT-004M QA-005 keyguard precondition

Audit baseline: 8b021b682b0aa8677a464f9495631b9fa55a180d; recursive tree 320 entries, not truncated; 262 commits ahead of main, zero behind. Six open draft PRs (#1, #3–#7) were inspected; PR #1 matched the authorized branch. PROJECT-ADAPTER.md and this roadmap are present; repository SKILL.md is absent; upstream shared package remains unverified and is not claimed as installed. Branch protection is not established (metadata protected=false, empty rulesets, protection detail HTTP 403).

Exact-head Phase 1 push/PR and CI-003 push/PR passed (runs 42356568198, 42356572084, 42356568200, 42356572111). QA-005 run 42356572086 failed only in connectedDebugAndroidTest: 180-second timeout, first test AccessibilityDisclosureActivityTest.testAccessibilitySettingsIntentIsIssuedOnlyAfterExplicitTap, 0/30 complete, pre-cleanup screenshot shows lockscreen. No app assertion failure or crash was recorded. The test harness did not ensure the disposable emulator was unlocked after the synthetic PIN setup and APK install delay.

AGENT-004M prebuilds the instrumentation APK, extends the disposable AVD screen timeout, wakes the emulator, conditionally dismisses the synthetic test PIN through ordinary adb shell input, and requires dumpsys window policy to report mShowingLockscreen=false before instrumentation. Existing EXIT cleanup still clears the PIN. Python static regression gates cover command ordering, ordinary shell UID, no-root boundary and cleanup. No product permission, service declaration, service connection, executor, real device operation or physical hardware access is added. Exact-head validation is pending; no local Android SDK/AVD run is claimed.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete. Independent security/accessibility review remains pending.

Next: accept the QA-005 rerun only on exact-head evidence, then obtain independent security/accessibility review before considering any AccessibilityService declaration. MediaProjection remains separate.


## AGENT-004M QA-005 parser correction

The first AGENT-004M rerun (commit 19f24ab3) passed prebuild, dependency negative control and AVD startup, then failed closed before instrumentation because Android 15's `dumpsys window policy` did not expose the assumed `mShowingLockscreen` field. The artifact recorded `KeyguardServiceDelegate showing=false` and `KeyguardStateMonitor mIsShowing=false`; the synthetic PIN cleanup trap succeeded. The workflow now parses those exact observed fields and requires both to be false before instrumentation. This correction is harness-only; no Android application code changed. Exact-head rerun pending.


## QA-005 disclosure-test launch-route correction — 2026-11-07

The exact-head rerun at 3dd65d05 passed Phase 1 push/PR and CI-003 push/PR, and the emulator reached `:app:connectedDebugAndroidTest`, but the first AccessibilityDisclosureActivityTest again timed out with 0/30 complete. Captured Android 15 policy state showed both `KeyguardServiceDelegate showing=false` and `KeyguardStateMonitor mIsShowing=false`; the emulator screenshot showed the HOME screen, not keyguard; `dumpsys activity lastanr` reported no ANR. Logcat contained no ActivityTaskManager START for the disclosure Activity. The test was directly invoking `startActivitySync` on a non-exported Activity from the instrumentation target context, bypassing the app's actual launcher navigation. The correction keeps the Activity non-exported and changes the instrumentation to launch exported MainActivity, tap the real `Accessibility access & revocation` entry, and observe the private Activity with a non-blocking ActivityMonitor. The Settings action remains separately monitored and must occur only after the explicit disclosure button tap. No manifest/exported flag or production behavior is changed. Exact-head rerun required.


## AGENT-004N — bounded QA-005 launcher instrumentation

Audit base 95051f15: recursive tree 321 entries, not truncated; 265 commits ahead of main and zero behind; 20 latest branch commits inspected; six open PRs (#1, #3–#7) reviewed. PR #1 is open/draft with no submitted reviews or inline threads. PROJECT-ADAPTER.md and roadmap exist; repository SKILL.md absent; upstream shared package unverified/not installed.

At 95051f15, Phase 1 push/PR and CI-003 push/PR passed (42359107206, 42359110939, 42359107186, 42359110817). QA-005 run 42359110794 failed after 180 seconds in connectedDebugAndroidTest with 0/30 tests complete. Artifact 13569156325 showed the first test stalled in AccessibilityDisclosureActivityTest.testAccessibilitySettingsIntentIsIssuedOnlyAfterExplicitTap; keyguard was hidden, screenshot showed system HOME and last-anr reported no ANR. No product assertion/crash was established. The instrumentation harness used startActivitySync and waitForIdleSync without a local bound.

AGENT-004N changes only instrumentation and static source gates: launch MainActivity with targetContext.startActivity; observe it through ActivityMonitor within 10 seconds; require onActivityResumed within 10 seconds; retain the real launcher-button route to the non-exported disclosure Activity; remove waitForIdleSync; add a regression gate against both unbounded helpers. Exact-head CI pending. No manifest/service/permission/executor/router changes.

Next: verify exact-head Phase 1, CI-003 and full QA-005; then independent security/accessibility review before any AccessibilityService declaration. MediaProjection remains separate. All M1–M8 remain incomplete; M7/M8 blocked.


AGENT-004N follow-up correction: the first implementation commit removed the global-idle wait from the disclosure-launch helper but left two calls in the explicit-tap test. The new Python source guard detects either call. Both remaining calls were removed in this follow-up; all activity observation remains bounded by ActivityMonitor and the resume latch. No production source changed.


## Engineering Factory run — 2026-11-07, AGENT-004O QA-005 keyguard transition race

Audit baseline 57d70638a78e4c8864f1528fd6bebed2df420cf6: recursive tree 322 entries (not truncated), 20 recent commits inspected, 267 ahead of main, zero behind. Six open PRs (#1 and #3–#7) were inspected; PR #1 remains open/draft and matches the authorized branch, with zero submitted reviews and zero inline review threads. PROJECT-ADAPTER.md and this roadmap exist; repository SKILL.md is absent; the upstream shared package remains unverified and is not claimed as installed.

At this exact head, Phase 1 push/PR 42360496305 and 42360499894 passed, each with 680 Python policy tests and Android debug build/unit/dependency gates. CI-003 push/PR 42360496250 and 42360499926 passed independent unsigned release reproducibility. QA-005 42360499918, attempt 2, failed before instrumentation. Downloaded artifact 13571292518 confirmed a keyguard transition race: the initial policy snapshot showed both state fields false, while the post-wait snapshot showed both true. The old workflow had skipped PIN entry after the transient initial unlocked state.

AGENT-004O corrects only the disposable-emulator precondition: explicit KEYCODE_SLEEP, bounded dumpsys power confirmation of a non-interactive state, KEYCODE_WAKEUP, bounded positive Keyguard-showing observation, synthetic PIN entry through ordinary shell UID 2000, and a bounded requirement that both Keyguard state fields are hidden before instrumentation. It adds power/keyguard snapshots and static regression assertions. No production Android source, manifest, permission, service, executor, CommandRouter or physical-device operation is changed. Exact-head CI after this correction is required; no emulator success is claimed until the new QA-005 run and evidence pass.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete. Independent human security/accessibility review remains pending.

Next: accept the exact-head QA-005 sleep/wake correction only after emulator evidence passes; then complete independent security/accessibility review before any AccessibilityService declaration. MediaProjection remains separate and CommandRouter remains fail-closed.


## Engineering Factory follow-up — 2026-11-07, AGENT-004P exact SystemUI PIN controls

At 0b27ec5c8b0e527ab653cedbc5ad60182ba1d789, Phase 1 42369272145 and CI-003 42369272198 passed. Phase 1 Python policy ran 681 tests; Android debug build/unit/dependency gates passed. CI-003 independent runner verification reported byte-identical unsigned release APKs (7,862,996 bytes; SHA-256 1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b), identical normalized contents and SBOM, and release_ready=false.

QA-005 42369272181 failed after the new sleep/wake precondition succeeded. Artifact 13572737599 recorded mWakefulness=Asleep before wake and KeyguardServiceDelegate showing=true plus KeyguardStateMonitor mIsShowing=true after wake and after the old input attempt. The screenshot showed an empty Android SystemUI Enter PIN field and keypad. No instrumentation tests started, no ANR occurred and no app crash was established. This isolated the remaining failure to input-text not entering the Keyguard PIN keypad.

AGENT-004P replaces only the emulator preflight PIN entry with exact UIAutomator hierarchy parsing and taps for the SystemUI keyguard_pin_view/pin_container/key0–key9/key_enter controls. Every target must be uniquely present, enabled, clickable and within actual emulator display bounds. The helper requires emulator serial and UID 2000, never logs the synthetic PIN, and uses bounded ADB calls. Parser tests cover valid and adversarial hierarchies. No production app/manifest/service/executor change. Exact-head QA-005 acceptance is pending.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete; independent human security/accessibility review remains pending.


## Engineering Factory run — 2026-11-07, AGENT-004Q QA-005 helper invocation repair

At audit head 11cd5ae4ca0d84aabd146c04dcd40d990c613fd9, the recursive tree contained 326 entries and was not truncated; 20 recent branch commits were inspected; the branch was 269 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected; PR #1 remained the open draft umbrella and matched the authorized branch. PROJECT-ADAPTER.md and this roadmap exist; repository SKILL.md is absent; the upstream shared package remains unverified and is not claimed installed.

Phase 1 push 42370252796 and PR 42370256677 each ran 690 Python tests and failed one source-boundary assertion: the QA-005 helper built key IDs with a duplicated package literal instead of the expected SYSTEM_UI constant. Android debug build/unit tests passed. CI-003 push 42370252811 and PR 42370256658 passed independent unsigned release reproducibility.

QA-005 42370256924 booted the disposable API 35 emulator, observed the keyguard and captured its UI hierarchy, then failed before instrumentation because the step working directory is android/ but the helper path was root-relative. The helper also reads TEST_PIN from its process environment, while the workflow only assigned a non-exported shell variable. AGENT-004Q corrects the source expression, helper relative path, explicit environment handoff and regression gate. This is QA-only; no production Android source, manifest, permission, service, executor, CommandRouter or device behavior changes. Post-fix exact-head CI and emulator acceptance remain pending.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete. Independent human security/accessibility review remains pending.

Next: accept only exact-head Phase 1 and CI-003 success plus complete QA-005 emulator evidence; then obtain independent security/accessibility review before any AccessibilityService declaration. MediaProjection remains separate and CommandRouter remains fail-closed.


## Engineering Factory run — 2026-11-07, AGENT-004R fresh QA-005 hierarchy capture

At audit head 7180daeb44908bcea1c83ef4a4753b6ec059c8bb, the complete recursive tree contained 326 entries and was not truncated; 20 recent commits were inspected; branch comparison was 270 ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected; PR #1 remained open/draft and matched the authorized branch. PROJECT-ADAPTER.md and this roadmap are present; repository SKILL.md is absent. An authorized Library title search found no supplied upstream shared package; it remains unverified and is not claimed installed. Branch metadata reports unprotected; rulesets are empty and branch-protection enforcement is unverified.

Phase 1 push 42370939857 and PR 42370944187 passed 690 Python tests each and Android debug unit/build/dependency gates. CI-003 push 42370939860 and PR 42370944158 passed independent unsigned release reproducibility. QA-005 42370944161 booted the disposable API 35 emulator, passed build/negative-control setup and reached SEC-020B4D. The fresh SystemUI dump failed with ERROR: null root node returned by UiTestAutomationBridge.; the subsequent pull found no XML. Artifact 13573334800 was inspected: the screenshot showed the lockscreen rather than the PIN keypad; no instrumentation test started; last-anr reported no ANR and no application crash was established.

AGENT-004R moves hierarchy capture into the QA helper. Each attempt uses a unique remote path cleared before use, requires the exact UIAutomator success marker, and retries only the observed null-root diagnostic up to five times. A pulled, non-empty hierarchy must pass the existing exact SystemUI resource-id, enabled/clickable and display-bounds parser before any PIN tap. New tests cover retry, unique paths, unexpected-error denial and the hard attempt limit. This is QA-only; no production app, manifest, permission, service, executor, router or physical-device behavior changes. Post-fix exact-head CI and QA-005 acceptance remain pending.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete. Independent human security/accessibility review remains pending.

Next: accept only exact-head Phase 1/CI-003 success and full QA-005 emulator evidence, then obtain independent security/accessibility review before considering any AccessibilityService declaration. MediaProjection remains separate and CommandRouter remains fail-closed.


## 2026-11-07 follow-up — AGENT-004S exact SystemUI lock-entry handoff

At audit head 43351639df5d82bdec0593b27a7ec71d24c17f64, Phase 1 push/PR and CI-003 push/PR passed, but QA-005 failed before instrumentation. Artifact 13574063028 showed the disposable API 35 emulator still on the lockscreen after the swipe. Its fresh hierarchy exposed the exact enabled/clickable SystemUI `device_entry_icon_view` and child `device_entry_icon_fg` with content description `Device locked`; the PIN keypad was absent. The synthetic test PIN was cleared by the workflow EXIT trap.

AGENT-004S initially attempted a one-tap handoff from the exact SystemUI lock-entry node, but the next emulator artifact showed the tap did not reveal the PIN bouncer. The final correction removes helper-side input. It validates the exact locked-state parent/child read-only and uses a bottom-edge swipe (display height minus 120 px to mid-screen, 450 ms) in the disposable-emulator workflow. The helper recaptures fresh unique hierarchies within five attempts and requires the full PIN keypad before synthetic PIN entry. Negative tests reject wrong package/description/non-clickable controls and prove no input occurs in the helper. This changes no production Android behavior, permissions, services, owner-consent flow, CommandRouter or executor. Exact-head CI and full QA-005 remain required before acceptance.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete.


AGENT-004S source-gate correction: the first pushed candidate exposed one test-only assertion typo (an extra leading quote in the expected source fragment). GitHub Actions ran 699 Python tests on both push and PR; 698 passed and the new source-gate test failed on that assertion. The assertion now matches the exact bounds-derived `_adb(..., "tap", str(x), str(y))` invocation. No helper runtime behavior changed in this correction. Exact-head policy, Android, CI-003 and QA-005 reruns are required.


AGENT-004S follow-up evidence: QA-005 artifact 13574907764 showed the exact lock-entry icon tap did not reveal the PIN bouncer. The final harness removes helper-side taps and moves the single workflow swipe into the bottom gesture region. The helper remains read-only and fails closed if the exact PIN hierarchy does not appear. Exact-head CI and full QA-005 are required.


AGENT-004S source-gate follow-up: the read-only helper correction renamed the lockscreen parser from `collect_keyguard_entry_center` to `validate_keyguard_locked_surface`, but the static gate retained the old symbol and an obsolete `entry_tapped` assertion. Both push and PR Python-policy jobs ran 699 tests and failed with this single test-only ValueError. The gate now checks the read-only parser and asserts the capture helper contains no input tap. No runtime code changed in this correction; exact-head reruns are required.


## Engineering Factory run — 2026-11-07, AGENT-004T QA-005 wake-state gate

Audit baseline: `38596a6b138cf039e26f244e780c63d5bd6032f7`; complete recursive tree 329 entries, not truncated; latest 20 authorized-branch commits inspected; branch comparison 275 ahead of main and zero behind. Six open PRs (#1 and #3–#7) inspected. PR #1 remains the open draft umbrella targeting main and matched the authorized branch head; PRs #3–#7 target separate scoped branches and were left untouched. PROJECT-ADAPTER.md and the engineering roadmap are present; repository SKILL.md is absent; the upstream shared package remains unverified and is not claimed installed.

At exact head, Phase 1 push/PR runs 42375117580 and 42375122847 passed Android build/unit/dependency checks and Python policy checks. CI-003 push/PR runs 42375117743 and 42375122831 passed independent unsigned APK reproducibility. QA-005 run 42375122823 failed before instrumentation in the SEC-020B4D disposable-emulator credential preflight. Artifact 13575706693 was downloaded and inspected. Its screenshot and fresh UIAutomator hierarchy show the Android 15 lockscreen (exact SystemUI device-entry surface), not the PIN bouncer. The saved post-wake policy snapshot reports KeyguardServiceDelegate showing=true and KeyguardStateMonitor mIsShowing=true, but also screenState=SCREEN_STATE_TURNING_ON and interactiveState=INTERACTIVE_STATE_WAKING. The workflow previously treated either Keyguard flag as sufficient and sent the swipe before the display was fully interactive. The EXIT cleanup log confirms the synthetic emulator PIN was cleared; last-anr reports no ANR and no app crash was established.

AGENT-004T changes only the QA-005 workflow and source regression gate. After KEYCODE_WAKEUP, the workflow now waits up to 20 seconds for both mWakefulness=Awake and mInteractive=true, records power-state-after-wake.txt, and requires both Keyguard policy flags to be true before the single existing bounded swipe. The swipe, helper and PIN entry remain emulator-only and ordinary ADB shell UID 2000; no root or physical-device target is introduced. No Android production source, manifest, permission, service declaration, owner-consent behavior, CommandRouter or executor changes.

Post-change exact-head Phase 1, CI-003 and full QA-005 runs are required. No post-change test pass or emulator acceptance is claimed until those runs complete. Independent human security/accessibility review remains pending.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete.

Next: verify exact-head Phase 1 and CI-003, then inspect the full QA-005 emulator artifact and JUnit results. Do not declare SEC-020B4D accepted or add an AccessibilityService declaration until the full emulator gate and independent security/accessibility review pass. MediaProjection remains separate; CommandRouter remains fail-closed.


## Engineering Factory run — 2026-11-07, AGENT-004U Android 15 PowerManager predicate correction

Audit baseline: `81cbd72f3fdb240267cc19ee2aaabd985ad6f6e6`; recursive tree 330 entries, not truncated; latest 20 branch commits inspected; 276 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) inspected. PR #1 is open/draft, targets main and matched the authorized branch head; PRs #3–#7 remain separate and untouched. PROJECT-ADAPTER.md and this roadmap are present; repository SKILL.md is absent; the authorized Library title search found no supplied shared factory package. The upstream package remains unverified and is not claimed installed. Rulesets are empty; branch-protection enforcement is unverified.

At exact head, Phase 1 push/PR [42377979055](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377979055) and [42377982649](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377982649) passed Android debug and Python policy jobs. CI-003 push/PR [42377979046](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377979046) and [42377982589](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377982589) passed independent unsigned build/reproducibility verification. QA-005 [42377982743](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377982743) failed before instrumentation. Artifact [13576597256](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42377982743/artifacts/13576597256) shows the API 35 emulator's pre-wake `mWakefulness=Asleep` / `mHalInteractiveModeEnabled=false` and post-wake `mWakefulness=Awake` / `mHalInteractiveModeEnabled=true`. The workflow incorrectly required `mInteractive=true`, which is absent from this Android 15 PowerManager dump. The screen screenshot is lit; synthetic PIN cleanup succeeded; last-anr reports no ANR and no application crash was established.

AGENT-004U changes only the QA workflow and its Python source gate. Sleep now requires both asleep/hal-interactive-false fields; wake requires awake/hal-interactive-true. A regression test asserts the exact API 35 fields and rejects the unsupported `mInteractive` token. No product Android source, manifest, permission, service, consent, CommandRouter, executor or physical-device behavior changes. Exact-head Phase 1, CI-003 and full QA-005 reruns remain required; no new-head emulator acceptance is claimed.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete. Independent human security/accessibility review remains pending.

Next: inspect exact-head Phase 1/CI-003 and the new QA-005 artifact/JUnit evidence. Keep AccessibilityService registration, MediaProjection and real agent dispatch disconnected until emulator acceptance and independent review.


## 2026-11-07 follow-up: AGENT-004V wait for wake transition completion

At exact head `8758ba1a9187acbec6a98fa0c7829dd1cf651f3b`, Phase 1 push/PR runs [42382193350](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382193350) and [42382197027](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197027) passed with 701 Python tests each and Android debug build/unit checks. CI-003 push/PR [42382193270](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382193270) and [42382197099](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197099) passed independent unsigned reproducibility: 7,862,996-byte APKs, 21 entries, SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`; normalized content SHA-256 `fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140`. Release remains unsigned and not release-ready.

QA-005 [42382197044](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197044) passed the Android 15 `mHalInteractiveModeEnabled` gate but failed after the bottom-edge swipe. Artifact [13578420997](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382197044/artifacts/13578420997) shows `mWakefulness=Awake`, `mHalInteractiveModeEnabled=true`, but `mWakefulnessChanging=true` and `mLastWakeTime` only 97 ms old. The screenshot/hierarchy remained on the lockscreen with the exact device-entry icon; the PIN bouncer did not appear. Both Keyguard policy indicators reported showing. Synthetic PIN cleanup succeeded and last-anr reported no ANR.

AGENT-004V changes only the QA workflow and source regression gate: the awake predicate now also requires `mWakefulnessChanging=false` before the swipe. No product source, manifest, permissions, services, consent, router, executor or physical-device behavior changes. Exact-head reruns remain required; no emulator acceptance is claimed.


## 2026-11-07 follow-up: AGENT-004W minimum post-wake settle interval

At exact head `29c078a03ba7b509689ed90635f1c5e18fc4bc72`, Phase 1 push/PR [42382756758](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382756758) and [42382761141](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761141) passed with 702 Python tests each and Android debug unit/build checks. CI-003 push/PR [42382756740](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382756740) and [42382761169](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761169) passed independent unsigned reproducibility.

QA-005 [42382761144](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761144) passed emulator boot and the corrected Android 15 wake predicates, but the bottom-edge swipe did not reveal the PIN bouncer. Artifact [13578476716](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42382761144/artifacts/13578476716) shows `mWakefulness=Awake`, `mWakefulnessChanging=false`, `mHalInteractiveModeEnabled=true`, yet `mLastWakeTime` was only 67 ms old. Keyguard remained showing; screenshot/hierarchy showed the lockscreen and device-entry icon, not the PIN bouncer. Synthetic PIN cleanup succeeded; last-anr reported no ANR.

AGENT-004W changes only the QA workflow and source regression gate to require a 1,500 ms minimum age from `mLastWakeTime` before the existing swipe, in addition to the stable PowerManager flags. No product source, manifest, permissions, services, consent, router, executor or physical-device behavior changes. Exact-head reruns remain required; no emulator acceptance is claimed.


## Engineering Factory run — 2026-11-07, AGENT-004X QA-005 wake-age parser correction

Audit baseline: 0ffb78dfacf09b2856c836e4ee631e70b389425f; recursive tree contained 333 entries and was not truncated; latest 20 authorized-branch commits were inspected; branch comparison was 279 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 remained open/draft, targeted main, and matched the authorized branch head; PRs #3–#7 target separate scoped branches and were left untouched. PR #1 had no submitted reviews or inline review threads. Branch metadata reported protected=false; rulesets were empty, so enforcement remains unverified. PROJECT-ADAPTER.md and the engineering roadmap are present; repository SKILL.md is absent. The upstream shared engineering-factory package remains unverified and is not claimed installed.

At exact head, Phase 1 push [42383275068](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383275068) and PR [42383280140](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280140) passed. The PR Python policy job ran 703 tests and passed; Android debug unit/build, repeat APK comparison, strict Gradle dependency verification, modified-dependency negative control and source-manifest gate passed. CI-003 push [42383275207](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383275207) and PR [42383280178](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280178) passed independent unsigned release build and reproducibility verification.

QA-005 PR run [42383280219](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280219) booted the disposable API 35 emulator, built the debug APK and passed the dependency negative control, but stopped before instrumentation at the post-wake PowerManager gate. Artifact [13578492527](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42383280219/artifacts/13578492527) contains a valid snapshot: mWakefulness=Awake, mWakefulnessChanging=false, mHalInteractiveModeEnabled=true, and mLastWakeTime=32654 (22892 ms ago). The pre-cleanup screenshot shows the illuminated Android lockscreen. The last-ANR report says no ANR occurred; no app crash was established. The EXIT trap successfully cleared the synthetic emulator PIN.

Evidence-led root cause: the workflow's GNU sed -E expression contained double-escaped parentheses and back-reference (two backslashes before the parentheses and capture reference) in the actual shell source, so it did not extract the valid 22892 millisecond age and the fail-closed gate rejected an otherwise settled snapshot. The after-wake snapshot writer also used a double-escaped newline format.

AGENT-004X corrects the sed expression to the exact single-escape ERE form and corrects the snapshot writer to printf with a real newline. Two regression tests execute the exact expression against the captured Android 15 mLastWakeTime format, including a too-recent value and missing/malformed values; another checks the snapshot writer's newline escaping. This is a QA harness-only change. No Android production source, manifest, permission, service, owner-consent flow, CommandRouter, executor, physical device or release behavior changes.

Post-change exact-head Phase 1, CI-003 and full QA-005 results are required before acceptance. No new-head emulator acceptance is claimed by this run. Independent human security/accessibility review remains pending.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete.

Next: verify the parser regression tests and exact-head Phase 1/CI-003, then inspect the new QA-005 emulator artifact and JUnit results. Do not add an AccessibilityService declaration, connect MediaProjection or enable real agent dispatch until full emulator acceptance and independent security/accessibility review pass. CommandRouter remains fail-closed.


## Engineering Factory follow-up — 2026-11-07, AGENT-004Y QA-005 parser integration and lockscreen gesture boundary

Audit baseline: ae1285119b63253cd04186fb23cfd84928ea8513; recursive tree 336 entries, not truncated; latest 20 branch commits inspected; branch was 280 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 remained open/draft against main and matched the authorized branch; it had no submitted reviews or inline review threads. PRs #3–#7 were left untouched. PROJECT-ADAPTER.md and the roadmap are present; repository SKILL.md is absent; the upstream shared engineering-factory package remains unverified and is not claimed installed. Branch metadata reports protected=false and rulesets were empty; protection enforcement remains unverified.

At exact head ae128511, Phase 1 push [42384024809](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384024809) and PR [42384029041](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384029041) passed. The PR Python-policy suite ran 717 tests; Android debug unit/build, repeat debug APK comparison, strict Gradle dependency verification, modified-dependency negative control and manifest security gate passed. CI-003 push [42384024664](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384024664) and PR [42384029055](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384029055) passed independent unsigned release builders and cross-runner reproducibility verification.

QA-005 PR [42384029065](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384029065) booted the disposable API 35 emulator, built the debug APK, passed the dependency negative control and passed the corrected PowerManager wake gate. It then failed before instrumentation because the bounded bottom-edge swipe did not reveal the PIN bouncer. Artifact [13579091222](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384029065/artifacts/13579091222) was downloaded and inspected: the post-wake snapshot reported mWakefulness=Awake, mWakefulnessChanging=false, mHalInteractiveModeEnabled=true and mLastWakeTime age 2541 ms; both Keyguard policy indicators were showing. The screenshot and fresh SystemUI hierarchy still showed the lockscreen, with the exact device-entry icon at [446,1538][634,1726] and child description Device locked, but no PIN keypad. The last-ANR report reported no ANR since boot. The EXIT cleanup cleared the synthetic emulator PIN. Logcat recorded INV.SystemUI showGestureNav at 15:01:04.672 shortly after the swipe; this is a diagnostic clue, not proof that navigation intercepted the gesture.

Prior attempts are not duplicated: the earlier exact device-entry icon tap at QA-005 run [42374293034](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42374293034) also left the lockscreen visible. The AOSP DeviceEntryIconViewBinder source binds a long-press listener rather than a normal click action; no further tap workaround is introduced.

AGENT-004Y makes the tested PowerManager parser from AGENT-004X the workflow's single source of truth: the wake loop calls scripts/qa005_power_state.py, the final failure path prints its diagnostic, and the duplicate shell sed parser is removed. The workflow records secure navigation_mode read-only and moves the one bounded swipe start from 120 px to 180 px above the bottom edge (same midpoint destination and 450 ms duration). At the captured 420 dpi profile this moves the origin from about 28.6 dp to about 42.9 dp from the edge; the hypothesis is to avoid the gestural-navigation edge region while retaining an ordinary lockscreen swipe. Static source tests assert parser wiring, navigation-mode evidence and the bounded swipe origin. The existing 11 parser unit tests remain the executable parser contract.

This is QA-harness-only. No production Android source, manifest, permissions, services, owner-consent flow, CommandRouter, executor, physical-device, signing, OTA or release behavior changes. Exact-head Phase 1, CI-003 and full QA-005 reruns are required; no emulator acceptance is claimed. Independent human security/accessibility review remains pending.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete.

Next: verify the helper-backed wake gate and exact-head Phase 1/CI-003, then inspect the navigation-mode artifact, post-swipe SystemUI hierarchy and JUnit output. Do not add an AccessibilityService declaration, connect MediaProjection or enable real agent dispatch until the complete QA sequence and independent security/accessibility review pass. CommandRouter remains fail-closed.


## Engineering Factory follow-up — 2026-11-07, AGENT-004Z QA-005 source-gate alignment and lockscreen swipe origin

Audit baseline: 531407b415e0f3b92b71fe832754950cb46023a2; recursive tree 337 entries, not truncated; latest 20 branch commits inspected; six open PRs (#1 and #3–#7). PR #1 remained open/draft against main and matched the branch; it had no submitted reviews or inline threads. PRs #3–#7 were left untouched. PROJECT-ADAPTER.md and roadmap exist; repository SKILL.md is absent; the upstream shared package remains unverified and is not claimed installed. Branch metadata reports protected=false; rulesets were empty and protection enforcement remains unverified.

At exact head 531407b, Phase 1 push [42384614275](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384614275) and PR [42384618251](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384618251) each ran 717 Python tests and failed five stale source-gate assertions that still expected the removed shell grep/sed implementation; 712 tests passed. The Android job passed. CI-003 push [42384614277](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384614277) and PR [42384618227](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384614227) passed both independent builders and the cross-runner verifier.

QA-005 PR [42384618137](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384618137) booted API 35, passed the helper-backed PowerManager wake gate and configured the read-only navigation-mode artifact. It failed before instrumentation because the one swipe beginning 180 px above the bottom edge did not reveal the PIN bouncer. Artifact [13578824258](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42384618137/artifacts/13578824258) was downloaded and inspected. It records navigation_mode=2 (gestural), a lockscreen screenshot, exact clock bounds [289,502][791,1444], device-entry icon bounds [446,1538][634,1726], Keyguard still showing, no PIN keypad, and no ANR since boot. The synthetic emulator PIN was cleared. The logcat showGestureNav event is a clue, not proof of gesture interception.

The 11 parser unit tests passed locally; compileall passed; the helper accepted the captured 2,541 ms post-wake PowerManager snapshot. The Phase 1 source-gate failure is test drift: five older tests still asserted that the workflow itself contained the parser's grep/sed predicates after the implementation moved them into the dedicated tested Python helper.

AGENT-004Z aligns those source gates with the helper's exact wakefulness, transition, HAL-interactive and minimum-age checks. It also moves the single QA swipe start to display_height minus 440 px. On the captured 1080x1920 API 35 AVD this is y=1480, in the observed 94 px gap between the clock bottom (1444) and device-entry icon top (1538), and about 105 dp above the bottom edge. The same midpoint destination and 450 ms duration remain. This is a bounded test of a central lockscreen swipe, away from the gestural navigation edge and the non-clicking device-entry icon; it is not a proven fix until the next emulator artifact confirms the PIN keypad.

No production Android source, manifest, permissions, services, owner-consent flow, CommandRouter, executor, physical device, signing, OTA or deployment behavior changes. Exact-head Phase 1, CI-003 and full QA-005 reruns are required. Independent human security/accessibility review remains pending.

M1 FOUNDATION — IN PROGRESS; M2 OS INTERFACE — IN PROGRESS; M3 AGENTIC INTELLIGENCE — PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS — NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY — NOT ACCEPTED; M6 SECURITY/PRIVACY — IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION — BLOCKED; M8 PRODUCTION READINESS — BLOCKED. No milestone is complete.

Next: verify the aligned 717-test policy suite and Android/CI-003 builds, then inspect navigation-mode and post-swipe SystemUI/JUnit evidence. Do not add AccessibilityService, MediaProjection or real agent dispatch until full emulator acceptance and independent security/accessibility review pass. CommandRouter remains fail-closed.


## Engineering Factory follow-up — 2026-11-07, AGENT-005A QA-005 Keyguard preflight ownership

Audit baseline: exact authorized branch head `655ec3b1003eb422f0cf64a4f100f599e6e2ac48`; recursive tree contained 338 entries and was not truncated; the latest 20 branch commits were inspected; branch comparison was 284 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 remained open/draft against main, its head matched the authorized branch, and it had zero submitted reviews and zero inline review threads. PRs #3–#7 were left untouched. `PROJECT-ADAPTER.md` and the roadmap are present; repository `SKILL.md` is absent. The upstream shared engineering-factory package remains unverified and is not claimed installed.

At exact head `655ec3b1003eb422f0cf64a4f100f599e6e2ac48`, Phase 1 push [42387158468](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387158468) and PR [42387163287](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387163287) passed. The PR Python policy suite ran 717 tests and passed; Android `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat debug APK comparison, strict Gradle dependency verification, modified-dependency negative control and manifest security gate passed. CI-003 push [42387158534](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387158534) and PR [42387163311](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387163311) passed independent unsigned release builders and cross-runner verification. The two release APKs were byte-identical: 7,862,996 bytes, 21 ZIP entries, SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`; normalized contents SHA-256 `fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140`. Runtime SBOM SHA-256 `447349a9e919be709745b9ce3290bb708fb90b29bcaa2fac9328081110aa76d5`. The separate scoped build-environment inventory covered 1,260 components; it is not a complete hosted-runner image inventory. Release provenance reports `release_ready=false`.

QA-005 PR run [42387163255](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387163255) booted the disposable API 35 emulator, built the debug APK and passed the modified-dependency negative control. It failed in the SEC-020B4D preflight before instrumentation. Evidence artifact [13580410837](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42387163255/artifacts/13580410837) was downloaded and inspected. PowerManager reported `mWakefulness=Awake`, `mWakefulnessChanging=false`, `mHalInteractiveModeEnabled=true`, and `mLastWakeTime` age 32,418 ms. KeyguardServiceDelegate reported `showing=true`, `secure=true`; KeyguardStateMonitor reported `mIsShowing=true` and `mInputRestricted=true`. The pre-cleanup screenshot showed the ordinary Android lockscreen, not a PIN bouncer. No ANR was reported. The EXIT cleanup successfully cleared the synthetic PIN. No instrumentation tests started; downstream QA-006 through QA-020B3 steps were skipped.

Root cause: after the workflow configures a synthetic PIN, it incorrectly required Keyguard to already be hidden before starting instrumentation. The existing SEC-020B4D instrumentation test already owns a bounded credential-preparation routine: it checks device security, wakes the emulator, locates the visible SystemUI device-entry control, waits for the PIN keypad, enters only the configured synthetic PIN through exact SystemUI keypad controls, and verifies the device is unlocked. The workflow's redundant preflight prevented that tested routine from ever running. In addition, the SystemUI device-entry affordance uses a long-press listener; a normal tap is not the correct semantic action.

AGENT-005A removes the contradictory workflow Keyguard-hidden gate while retaining the secure-PIN setup/EXIT cleanup, bounded PowerManager awake gate, and a read-only Keyguard diagnostic snapshot. The instrumentation helper now requires the exact visible, enabled, clickable, long-clickable SystemUI device-entry node and invokes `AccessibilityNodeInfo.ACTION_LONG_CLICK`; it rejects ambiguous/missing nodes and out-of-screen bounds. It then continues to require the exact SystemUI PIN keypad and ordinary shell identity (UID 2000). No Keyguard-dismiss API, root, shell shortcut or credential bypass is introduced. Python source gates now assert that the workflow delegates authentication to the test and that the long-press is bound to the exact SystemUI node.

This change is QA/instrumentation-only. No production Android source, manifest, permission, AccessibilityService, MediaProjection service, owner-consent protocol, trust store, CommandRouter, executor, physical device, signing, OTA or deployment behavior changes. Exact-head Phase 1, CI-003 and QA-005 reruns are required before acceptance; no new-head emulator acceptance is claimed by this entry. Independent human security/accessibility review remains pending.


## AGENT-005A independent diff correction

Independent review of the first candidate commit `8c70ebe36ed2396659b56d72cb1a4571eb1af2f0` found that the workflow tree edit had retained the old Gradle command at the replacement boundary, producing a duplicated `:app:connectedDebugAndroidTest` invocation on one shell line. The candidate is not accepted. This follow-up removes the duplicate, adds a source regression assertion requiring exactly one instrumentation invocation, and corrects the Kotlin helper documentation to describe its long-click behavior. The new exact-head CI runs, not the candidate runs, determine acceptance.


## AGENT-005A test-gate correction

The first exact-head policy jobs on candidate `948ae030cf9ec2a605b2f5c5bd056168c5d25af5` ran 719 tests and reported one error: the newly added exactly-once assertion referenced `boundary_step` before the test assigned it. The failure is confined to the new Python test's statement order; the long-click source test itself passed. This follow-up moves the assertion immediately after the boundary slice is assigned. The candidate policy jobs are not accepted; a fresh exact-head rerun is required.


## AGENT-005A instrumentation compilation correction

The QA-005 run on candidate `948ae030cf9ec2a605b2f5c5bd056168c5d25af5` completed SDK installation and compiled the main debug APK, then failed at `:app:compileDebugAndroidTestKotlin`: the earlier source-block replacement had left a duplicate, incomplete `awaitCredentialPrompt` declaration immediately before the real method. No emulator was started. The duplicate line is removed here, and a new source regression test requires exactly one complete helper declaration and rejects the incomplete form. This is a test-harness compile defect; it is not evidence of a production application crash. The exact-head AndroidTest build and emulator sequence must be rerun.


## AGENT-005B — QA-005 action-filtered ActivityMonitor isolation (2026-11-07)

**Selected task:** correct the single remaining QA-005 instrumentation failure using its exact JUnit/logcat evidence.

At `c743588fc298b391c1f541f5140f860142a86ec7`, Phase 1 push [42393636236](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393636236) and PR [42393639999](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393639999) passed. Each Python policy job ran 720 tests. Both Android jobs passed `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat debug APK comparison, strict dependency verification and the modified-dependency negative control. CI-003 push [42393636218](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393636218) and PR [42393640076](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393640076) passed independent-runner verification: unsigned release APKs were byte-identical (7,862,996 bytes; 21 entries; SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`; normalized entries SHA-256 `fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140`). Runtime SBOM SHA-256 `ee9157b34a0c3108d28e89226fec8b0784d24a042f79cc109b7ce8e9438272b2`; scoped build-environment inventory SHA-256 `12ace283d99bb359f3783797a1865e3c49ad6d53f6aedb9f8972f1e8c7ab61bc`. Provenance reports `release_ready=false`.

QA-005 [42393640119](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393640119) failed one of 30 instrumentation tests. Artifact [13582811813](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42393640119/artifacts/13582811813) contains the JUnit XML and logcat. The sole failure was an actionless explicit MainActivity test Intent being intercepted by the blocking action-filtered Accessibility Settings ActivityMonitor. AGENT-005B changes only the instrumentation test, its Python source regression gate and documentation: the launch now carries `ACTION_MAIN` and `CATEGORY_LAUNCHER`, with runtime assertions. No production Android source or manifest behavior changed.

Exact-head reruns are required. Until QA-005 passes on the corrected head, the full emulator smoke sequence is not accepted. M1/M2/M6 remain IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Independent human security/accessibility review remains PENDING. The upstream shared `SKILL.md` remains unverified and is not claimed as installed.

## Audit and implementation update — 2026-11-07, AGENT-005C

At parent head `c06404f6a25b9b4c2a55fae415efe5f6d702adcf`, the recursive tree contained 340 entries and was not truncated; 20 recent commits were inspected; the branch was 289 commits ahead of `main`, zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 remained open/draft and matched the authorized branch; PRs #3–#7 were left untouched. PR #1 had no submitted reviews or inline review threads. `PROJECT-ADAPTER.md` and the roadmap exist; repository `SKILL.md` is absent. Authorized Library searches did not surface the upstream shared engineering-factory package; it remains unverified and is not claimed installed.

At the exact parent head, Phase 1 push/PR and CI-003 push/PR passed. The Phase 1 PR policy log reported 721 Python tests passed; Android debug unit/build, repeat APK comparison, strict dependency verification and modified-dependency negative control passed. CI-003 independent runners produced byte-identical unsigned APKs (7,862,996 bytes; SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`); provenance explicitly reported `release_ready=false`.

QA-005 [42396557841](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42396557841) ran 30 instrumentation tests (29 passed, 1 failed). Artifact [13584455104](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42396557841/artifacts/13584455104) showed the sole failure at `openDisclosureFromLauncher`: MainActivity was displayed with the corrected launcher Intent, but the private disclosure Activity was not observed. The blocking action-filtered Accessibility Settings ActivityMonitor remained registered during that second actionless explicit-component launch. AGENT-005C scopes monitor registration until after the disclosure Activity is already open and before the explicit Settings-button tap, with a regression test for that ordering.

This is instrumentation-only. No production Android source, manifest, permission, service, trust store, CommandRouter, executor, physical hardware, signing or deployment behavior changed. The new exact-head Phase 1, CI-003 and QA-005 runs must determine acceptance. No new-head emulator acceptance is claimed. Independent human security/accessibility review remains pending.

M1/M2/M6 remain IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED. No milestone is complete.

## Audit and implementation update — 2026-11-07, AGENT-005D

At parent `dd5980ee9fb6636a65f77b048dafc9332a6f5878`, Phase 1 push/PR passed with 721 Python tests each; Android debug unit/build, repeat APK comparison, strict dependency verification and negative control passed. CI-003 push/PR passed independent unsigned APK reproducibility (7,862,996 bytes; SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`); provenance reports `release_ready=false`.

QA-005 [42401631073](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42401631073) executed 30 instrumentation tests: 28 passed and 2 failed. Both AccessibilityDisclosureActivity tests passed after AGENT-005C. The two SEC-020B4D lifecycle tests failed because the exact visible, long-clickable SystemUI device-entry node was not found. The pre-cleanup screenshot shows the lockscreen; PowerManager reported awake/interactive and Keyguard secure/showing; no ANR was reported. The helper did not include its existing bounded UI hierarchy snapshot in this failure path.

AGENT-005D adds a five-second/100-ms bounded retry for the exact SystemUI node and includes text-free structural node/window diagnostics on failure. It preserves the package/resource/class/visibility/clickability/long-clickability and screen-bound checks, ordinary shell UID 2000, and ACTION_LONG_CLICK. No coordinate guessing or production Android code changes. Exact-head QA-005 rerun is required; no emulator acceptance is claimed.



## AGENT-005E — QA-005 instrumentation process-start diagnostics (2026-11-08)

At exact head `b63ca632feec80b927884483cc19d44eebd86732`, Phase 1 push/PR and CI-003 push/PR passed. QA-005 booted the disposable API 35 emulator and compiled both APKs, then failed before test discovery: JUnit reports zero tests, and logcat records ActivityManager `am_anr` for the instrumented `tech.mrnothing.os` process with reason `failed to complete startup`. The app process was killed for a background ANR; no test assertion or `FATAL EXCEPTION` was observed. `dumpsys activity lastanr` did not report this event. Root cause within process startup remains undetermined.

AGENT-005E adds bounded capture of the Android events buffer and app/test `dumpsys activity exit-info` to the QA-005 evidence artifact, with Python source regression coverage. This is CI/diagnostics-only; no production app, permission, service, trust or executor code changed. Exact-head CI and emulator evidence are pending. No milestone status changes: M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED. No milestone is complete.


## 2026-11-08 — AGENT-005F verified audit and next gate

Branch feat/phase1-agentic-phone audited at f3937dbe1ddc46b06e24a2ef732b626c2033cb23; recursive tree 343 entries, not truncated; 292 commits ahead of main, zero behind. Six open draft PRs (#1 and #3–#7) were inspected. PR #1 matches the authorized branch, remains draft, and has no submitted reviews or inline review threads. PRs #3–#7 remain untouched. The branch is unprotected. PROJECT-ADAPTER.md and this roadmap exist; repository SKILL.md is absent. The upstream shared factory package remains unverified and is not claimed installed.

At this exact head, Phase 1 push/PR passed (Python policy 722/722 on each; Android debug unit/build, repeat APK and dependency checks passed). CI-003 push/PR passed its independent unsigned-build verifier. QA-005 failed before test discovery: the instrumented target process hit a startup ANR after am_proc_start/am_proc_bound; no JUnit tests ran. The evidence shows high emulator CPU pressure but does not establish a single root cause. AGENT-005F adds bounded DropBox data_app_anr capture and a source regression gate to seek the missing process stack. This is diagnostics-only; no product permissions, services or execution paths change.

Milestones remain M1/M2/M6 IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7 BLOCKED and M8 BLOCKED. No milestone is complete. Next: inspect the DropBox ANR artifact on the new exact-head QA run before deciding whether to optimize test discovery, wait for emulator idle, or investigate an application initialization path. Do not change production startup or weaken ANR gates without evidence.


## 2026-11-08 — AGENT-005G instrumentation discovery correction

At parent head `155295c299067c0161eddb481b7ea9a956f9a3d5`, QA-005 [42407298271](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42407298271) built both APKs and booted the disposable emulator, then failed before test discovery. DropBox artifact [13588166608](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42407298271/artifacts/13588166608) shows the main thread in `DexFile.getClassNameList` → `ClassPathPackageInfoSource.findClassesInApk` → `scanForApkFiles` → `TestGrouping.testCaseClassesInPackage` → `InstrumentationTestRunner.onCreate`. The blocked work is the legacy runner's default whole-package class discovery, not MainActivity initialization. CPU pressure avg10=62.88 and total CPU 93% may amplify the scan.

AGENT-005G configures the legacy runner's documented comma-separated `class` argument with all five existing `InstrumentationTestCase` classes, retaining all 30 methods and avoiding a new test framework dependency. A Python regression gate compares the Gradle allowlist with every instrumentation test class in the source directory. No production code, permissions, services, trust, consent or execution behavior changes. Exact-head CI/emulator rerun is pending. No milestone status changes; no milestone is complete. Independent human security/accessibility review remains pending.


## AGENT-005H — 2026-11-08, SystemUI device-entry action correction

Audit at `9a41421804cb73366ccc972e68900cd05084810a`: recursive tree 345 entries (not truncated); 20 latest commits inspected; branch 295 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected; PR #1 matches the authorized branch and remains draft. PRs #3–#7 were left untouched. `PROJECT-ADAPTER.md` and this roadmap exist; repository `SKILL.md` is absent. The upstream shared package remains unverified.

At exact head `9a41421804cb73366ccc972e68900cd05084810a`, Phase 1 push/PR passed: the PR Python policy suite reported 723 tests passed; Android `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat debug-APK comparison, strict dependency verification and manifest security gate passed. CI-003 push/PR passed independent unsigned release reproducibility: two 7,862,996-byte APKs (21 entries) were byte-identical, SHA-256 `1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b`; normalized entries SHA-256 `fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140`. The independent build-environment inventory covered 1,260 components. CI provenance explicitly reports `release_ready=false`.

QA-005 [run 42412685924](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42412685924) executed 30 instrumentation methods: 28 passed and 2 failed. Both failures occurred before the SEC-020B4D Activity/fake-store lifecycle assertions, because the test helper required a long-clickable SystemUI device-entry node. Actual Android 15 hierarchy evidence showed the exact node was clickable=true and longClickable=false. The synthetic PIN cleanup succeeded.

AGENT-005H updates only the Android instrumentation helper, its Python source regression gate and QA/roadmap evidence. The helper now uses `AccessibilityNodeInfo.ACTION_CLICK` on the exact visible, enabled, clickable SystemUI node with screen-bounded bounds and retains UID 2000 checks. No production Android source, permission, service, trust, consent, executor or device-control behavior changed. Exact-head reruns remain required.

Milestones remain M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Independent human security/accessibility review remains pending.


### AGENT-005H follow-up — source regression gate alignment

The first exact-head Phase 1 Python runs on candidate `a1bb94a818921d594dc0d4eba420d2826d50dca7` failed in `tests/test_sec020b4d_lifecycle_instrumentation.py`: two tests could not find the renamed helper, and one assertion still required the old long-click helper. The new `test_qa005_workflow_gate.py` click-action test passed. This follow-up aligns the SEC-020B4D source gate with the observed Android 15 clickable/not-long-clickable SystemUI node. No product code or Android permissions change. Candidate CI is not accepted; exact-head reruns are required.


AGENT-005H KDoc cleanup: the AndroidTest helper's comment now accurately describes the exact SystemUI node as clickable (not long-clickable). The SEC-020B4D Python source gate rejects the stale `long-clickable` wording. No runtime behavior changed.


## 2026-11-08 — AGENT-005J exact-head QA acceptance and M1 threat model

The authorized branch parent at run start was 680d5cbd52630e685fb1ada69126a6555b1685f4; recursive tree 347 entries, not truncated; branch comparison is 300 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 matches the branch, remains draft against main, and has no submitted reviews or inline review threads. The branch is unprotected; repository rulesets are empty. PROJECT-ADAPTER.md and this roadmap exist; repository SKILL.md is absent. The upstream shared factory package remains unverified and is not claimed installed.

Exact-parent verification is now complete:
- Phase 1 push run 42417459789 and PR run 42417463397 passed. Both Python policy jobs reported 730 tests passed. Android :app:testDebugUnitTest, :app:assembleDebug, repeat debug APK comparison, strict Gradle dependency verification, modified-dependency negative control and manifest security gate passed.
- CI-003 push run 42417459698 and PR run 42417463410 passed independent-runner verification. Two unsigned release-variant APKs were byte-identical (7,862,996 bytes; SHA-256 1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b; normalized-entry SHA-256 fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140). The scoped build-environment inventory contains 1,260 components. Provenance reports release_ready=false; the inventory is not a complete hosted-runner image SBOM.
- QA-005 PR run 42417463430 passed on a disposable Android API 35 x86_64 emulator. JUnit reports 30 tests, zero failures, zero errors and zero skipped. QA-005 through QA-010 passed; QA-013, QA-020B2 and QA-020B3 passed. QA-011 remains blocked_service_disabled; QA-012 passed structural hierarchy checks only, with spoken_navigation_verified=false and acceptance_passed=false. This is emulator evidence, not Pixel 9 Pro hardware evidence.

The previous QA-012 viewport correction is therefore accepted at the exact parent head. The DropBox ANR query returned no data_app_anr entries during this successful run; this is not a guarantee about other devices or future runs.

AGENT-005J selects the highest-priority unblocked M1 gap: a consolidated, evidence-labeled security threat model. The repository had no dedicated threat-model document or STRIDE register. The new docs/THREAT-MODEL.md records assets, trust boundaries, actors, invariants, STRIDE threats, data handling, evidence, residual risks, owners and M1 acceptance criteria. tests/test_threat_model_document.py guards structural completeness. The document is DRAFT pending independent security review and does not authorize execution. No production Android source, manifest, permission, service, trust store, consent, dispatcher or executor changed.

Milestones remain M1 FOUNDATION IN PROGRESS (threat model draft; independent review pending); M2 OS INTERFACE IN PROGRESS (spoken TalkBack not accepted); M3 AGENTIC INTELLIGENCE PARTIAL (no integrated executor); M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED pending physical Pixel 9 Pro access; M8 BLOCKED. No milestone is complete.

Next task: independent security review of the threat model and existing SEC-017–SEC-020B6 boundaries. In parallel, obtain separate deliberate approval before enabling TalkBack on a disposable emulator for spoken acceptance. Do not connect an executor until the cross-store revocation/reservation race has a reviewed atomic final-admission design.


## AGENT-005K — durable reservation expiry hardening (2026-11-08)

At starting head 63a4d23e4d97117a342ae831600736fcd0797ae7, all five exact-head Phase 1/CI-003/QA-005 workflows were green. AGENT-004H's storage-only ledger was missing its own issue/expiry check: reserve could create an already-expired row and claim_dispatch could transition a stale RESERVED row to DISPATCH_STARTED. The ledger now checks time inside its SQLite write transaction, refuses future/expired creation, refuses future claim, and terminally records an expired reservation as FAILED_NO_EFFECT/CAPABILITY_EXPIRED. Four focused regression cases were added. This is defense in depth only; the live TLS adapter's monotonic deadline and current enrollment checks remain required. The adapter still does not claim dispatch and CommandRouter remains fail-closed. Exact-head CI and independent review are pending. Upstream shared SKILL.md remains unverified.

**Next security priority:** serialize current owner-enrollment generation/revocation with the durable DISPATCH_STARTED claim. The present owner registry and action reservation ledger are separate SQLite databases, so their current checks do not yet establish one cross-store linearization point. Do not connect an executor until this is resolved and reviewed.


## AGENT-005L — lock-coupled enrollment and dispatch admission (2026-11-08)

Audit baseline: feat/phase1-agentic-phone at 7bf32e5f45e5d8ee0cfd013706ead4c88fe92849; complete recursive tree 351 entries, not truncated; 20 recent commits inspected; branch 303 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 matches the authorized branch, remains draft against main, and has no submitted reviews or inline threads. The branch is unprotected and repository rulesets are empty. PROJECT-ADAPTER.md and this roadmap exist; repository SKILL.md is absent. The upstream shared factory package remains unverified and is not claimed installed.

Exact-head workflows at the audit head all passed: Phase 1 push/PR, CI-003 independent-runner push/PR, and QA-005 emulator PR. QA-005 completed 30/30 instrumentation tests on a disposable API 35 x86_64 emulator. This does not establish spoken TalkBack or physical Pixel 9 Pro acceptance.

AGENT-005K exposed the remaining gap: the owner enrollment registry and action reservation ledger are separate SQLite databases. SEC-019A already makes consent-nonce consumption atomic with enrollment revocation/rotation inside the enrollment database; this task addresses the distinct final DISPATCH_STARTED claim.

Implementation: SQLiteOwnerEnrollmentRegistry.hold_active_enrollment_for_dispatch acquires BEGIN IMMEDIATE, checks the exact active owner/device, transport fingerprint, credential generation and consent-key digest, and holds that writer lock while DurableActionReservationLedger.claim_dispatch commits its own reservation transaction. The ledger re-reads the immutable reservation binding inside its transaction. All signed rotation/revocation operations use the same enrollment writer lock, establishing a single-host ordering: revocation/rotation first denies; claim first is durably ordered before later revocation. Direct claims without the exact registry are rejected. Store failures fail closed; a post-ledger enrollment-context failure returns ENROLLMENT_LOCK_COMMIT_UNCERTAIN and never authorizes dispatch.

Four integration tests cover revocation-before-claim, rotation-before-claim, a real two-thread claim-versus-revocation lock ordering, and enrollment-store outage. The claim remains storage-only. It does not validate the live TLS socket, monotonic adapter session or Android permission state, and it does not execute an action. This is not a distributed transaction or multi-host guarantee. Exact-head CI and independent review are pending at submission.

Milestones remain M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Independent human security/accessibility review remains pending.


## AGENT-005M — live-capability final-admission simulation (2026-11-08)

The AGENT-005L lock-coupled enrollment/dispatch claim is now callable through a no-side-effect adapter simulation that revalidates the retained verifier-created capability under both database writer locks. The final guard checks the exact live TLS socket/session, monotonic session and capability deadlines, current paired enrollment, transport certificate fingerprint, credential generation, consent-key digest, action and canonical arguments digest. A revocation committed after reservation but before the final claim cancels the reservation; capability expiry after reservation also cancels before claim. The simulation immediately records `FAILED_NO_EFFECT/NO_EXECUTOR_CONNECTED` after a successful storage claim.

This is not a production coordinator: the final guard is a trusted in-process callback; the prototype performs no Android permission probe and never executes an action. Direct storage-level `claim_dispatch` remains a storage primitive and must not be treated as authorization. The exact same SQLite registry object is required for transport and consent lookup, with a separate action ledger. Independent human security review remains required before any executor integration. Keep M3 PARTIAL and M6 IN PROGRESS; no milestone is complete.


## AGENT-005N — composed Android action preflight (2026-11-08)

Audit baseline: authorized branch head `aebd8ca9b648df3a0b02a63e675d58673395455e`; recursive tree 355 entries, complete; 20 recent commits inspected; 305 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected; PR #1 alone uses this branch and remains draft. PR #1 has no submitted reviews or inline threads. Branch protection is disabled and repository rulesets are empty. Local adapter and roadmap exist; repository SKILL.md is absent; upstream shared package remains unverified.

Starting-head Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR all passed. Python policy was 751/751 on both Phase 1 events. Android Gradle unit/build, repeat debug APK, strict dependency verification, tampered-dependency negative control and manifest gate passed. CI-003 independent unsigned APK reproducibility passed with `release_ready=false`. QA-005 completed 30/30 instrumentation tests, zero failures and zero skipped on a disposable Android 15 API 35 x86_64 emulator. QA-011 remains blocked because the service is disabled; QA-012 is structural, not spoken TalkBack. QA-020B2/B3 passed.

AGENT-005N adds a non-integrated `ActionPreflightCoordinator` that composes the existing coarse safety policy and action-specific Android permission gate. It validates typed arguments before state reads, uses an app-owned safety-signal provider with deny-all default, fails closed on missing/throwing state, short-circuits platform reads after safety denial, and freshly evaluates action-specific OS prerequisites. Its positive result is explicitly only `ReadyForIndependentAuthorization`; it is not a capability or dispatch permission. Eleven JVM tests and seven Python source-boundary tests were added. CommandRouter remains fail-closed; no provider, service, permission, listener or executor is connected.

M3 remains PARTIAL. M1/M2/M6 remain IN PROGRESS; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Next: independent security review of the full authorization chain and preflight composition. Any later no-op Android admission integration must remain isolated from real device APIs until reviewed.



## AGENT-005O — least-privilege action preflight (2026-11-08)

Audit baseline: authorized branch `feat/phase1-agentic-phone` at `75f6f2384181b8a7107850bf5f40cf890db8527a`; complete recursive tree 360 entries, not truncated. The latest 10 commits and all six open PRs (#1 and #3–#7) were inspected. PR #1 is the only open PR using this branch, targets `main`, remains draft and has no submitted reviews or inline threads. The project adapter and roadmap exist; repository `SKILL.md` is absent. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed installed.

Exact-head Phase 1 push/PR and CI-003 independent-runner push/PR passed. Both Phase 1 Python policy jobs ran 758 tests and passed. Android unit tests, debug assembly, repeat debug APK comparison, strict dependency verification, modified-dependency negative control and source-manifest gate passed. CI-003 produced byte-identical unsigned release APKs on two independent runners (7,867,852 bytes; SHA-256 `07618b5eaf5d36995c5a7fae286c0a41aee1407c89f6437d2c326b4324d4336a`; normalized-entry SHA-256 `50ea1d354ec93d34c1b8d4973c9a2f956c9fd12754795eb439cd0a9214a70c83`). Runtime inventory and SPDX SBOM matched. Provenance reports `release_ready=false`.

QA-005 exact-head emulator run [42436280956](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42436280956) completed successfully. The API 35 disposable x86_64 emulator passed the SEC-020B4D lifecycle step and QA-005 through QA-010, QA-013, QA-020B2 and QA-020B3. QA-011 remains `blocked_service_disabled`; QA-012 checks structural semantics only and is not spoken TalkBack acceptance. The emulator artifact is [13598959293](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42436280956/artifacts/13598959293). No physical Pixel 9 Pro was tested.

**Finding:** the composed AGENT-005N policy required `ownAccessibilityServiceEnabled` as a common prerequisite for every action. That conflicts with AGENT-004J's action-specific contract: `navigate` only launches a verified exact package/Activity, and `read_screen` uses a user-approved MediaProjection session. Neither requires an AccessibilityService. Requiring it would create unnecessary pressure to enable a highly privileged service for unrelated operations, violating least privilege and the documented action-specific gate.

**Change:** `ScreenActionPreflight` now applies common owner/device/consent/restricted-surface/emergency-stop/revocation checks to every action, then enforces:
- `navigate`: no AccessibilityService or MediaProjection requirement; exact package launchability remains in `ActionPermissionGate`.
- `read_screen`: active user-approved MediaProjection required; no AccessibilityService requirement.
- `scroll`: app-owned AccessibilityService enabled; the action-specific gate separately requires it connected.

Added pure-JVM tests for the two non-accessibility actions and a Python source-boundary regression test. The Android service remains undeclared; no prompt, grant, listener, executor, dispatcher, shell bridge or device action was added. CommandRouter remains fail-closed.

**Independent review status:** source/diff and test assertions were re-read against AGENT-004J and SEC-014F. This is an author-side review, not independent human security approval. The supervisor gate remains PENDING. Exact-head CI and QA must pass after this commit.

Milestones remain M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete.


## AGENT-005P — make live final admission mandatory (2026-11-08)

The exact-head audit found that DurableActionReservationLedger.claim_dispatch accepted an omitted/None final_admission_guard and treated it as success. That allowed a direct caller with an active enrollment row to move a reservation to DISPATCH_STARTED without proving that it had revalidated the adapter-retained live TLS socket/session and one-use capability. The transport adapter supplied a guard, but the storage API did not enforce that contract for every caller.

**Change:** the keyword-only final_admission_guard is now required. Explicit non-callable/None values are rejected; only the exact Boolean True is accepted; exceptions and non-Boolean truthy values fail closed. The guard is invoked while both the enrollment and reservation database writer locks are held, before the final signed-time check and state transition. Storage-only tests now pass an explicit test guard and a regression test proves omission cannot claim.

**Boundary:** a callback is still trusted in-process code, not a cryptographic capability or protection against hostile code already executing in the host process. Only the reviewed TLS adapter may provide the production guard; it must never come from an agent, LLM or request. No Android executor, listener, permission grant or device action is connected. Independent human security review remains pending.


## Verification correction — invalid-guard response assertion

The first exact-head Phase 1 push run (42438951780) ran 761 tests and found one test-only assertion mismatch. The implementation correctly rejects an explicit non-callable guard before reading the reservation row, so the returned decision has state null; the durable row itself remains RESERVED. The test incorrectly expected the decision's state field to contain RESERVED. The assertion now checks a null decision state and separately reads the ledger to prove the row remains RESERVED. No implementation change was needed. The failed run is retained in Actions history; the corrected head must pass a fresh exact-head run.


## AGENT-005Q — final-admission writer-lock regression (2026-11-08)

Audit baseline: authorized branch `feat/phase1-agentic-phone` at `103ebdd61849bdfde14ec4919d58acd4e2e9035d`; complete recursive tree 362 entries, not truncated; 20 recent commits inspected; branch 311 commits ahead of `main` and zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 is the only PR using this branch, targets `main`, remains draft, and has no submitted reviews or inline review threads. Other PR branches were not modified. The branch is not protected (`protected=false` in the branch listing). `PROJECT-ADAPTER.md` and the roadmap exist; repository `SKILL.md` is absent; the upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed installed.

At the starting head, exact-head Phase 1 push [42439006024](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42439006024) and PR [42439010276](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42439010276) passed; each Python-policy job ran 761 tests. Android unit tests, debug assembly, repeat debug APK comparison, strict dependency verification, modified-dependency negative control and source-manifest gate passed. CI-003 push [42439006083](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42439006083) and PR [42439010052](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42439010052) passed; independent runners produced byte-identical unsigned APKs (7,867,868 bytes; SHA-256 `c7036c64e3a49ea9d8642c29082c42537e2c8ba0863d43d3cbd4fbb098603da7`). The verifier reports `reproducible=true`, `release_ready=false`; the scoped 1,260-component build-environment inventories and SBOMs matched. QA-005 [42439010136](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42439010136) passed 30/30 Android instrumentation tests (zero skipped/failed) on a disposable API 35 x86_64 emulator, plus launcher/recovery, QA-006–QA-010, QA-013 and QA-020B2/B3. QA-011 remains `blocked_service_disabled`; QA-012 is structural only, not spoken TalkBack acceptance. No physical Pixel 9 Pro was tested.

AGENT-005Q adds one adversarial concurrency regression in `tests/test_owner_enrollment_registry.py`. While `final_admission_guard` is executing, it starts a signed revocation through a fresh enrollment SQLite connection and a pre-dispatch cancellation through a fresh reservation SQLite connection. Both operations must remain blocked until the final guard returns and `DISPATCH_STARTED` commits. Afterward, cancellation must not undo the claim and the signed revocation may commit only after the claim. This tests the lock scope of the actual callback, not merely the lock scope before it. The test changes no production code and invokes no device action.

The exact-head CI triggered by this test commit is pending at commit creation; no result is claimed here. The implementation remains a single-host SQLite lock-coupling prototype, not a distributed transaction. The callback remains trusted in-process code and must never be supplied by model/request input. CommandRouter remains fail-closed; no executor, listener, Android permission, service, production signing or OTA path is connected. Independent human security review remains pending.

Milestones remain M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete.


## AGENT-005U — pre-COMMIT process-death recovery (2026-11-08)

Audit baseline: authorized branch feat/phase1-agentic-phone at cc20bfbedac7db2a8f3f89c54742fa3cfb4a5445; recursive Git tree 370 entries, not truncated; 20 recent commits inspected; branch 318 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 alone uses the authorized branch, targets main, remains draft, has 318 commits/306 changed files, and has no submitted reviews or inline review threads. PRs #3–#7 target the feature branch or its QA-014 parent branches and were not modified. The branch is unprotected and required status-check enforcement is off. PROJECT-ADAPTER.md and this roadmap exist; repository SKILL.md is absent; the upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed installed.

At the starting head, Phase 1 push [42451179062](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42451179062) and PR [42451182901](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42451182901) passed; both Python-policy jobs ran 767 tests and passed compilation and the Android source-manifest gate. Android :app:testDebugUnitTest, :app:assembleDebug, clean repeat debug APK comparison, strict dependency verification and the modified-dependency negative control passed. CI-003 push [42451179006](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42451179006) and PR [42451182829](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42451182829) passed; independent builders produced byte-identical unsigned APKs (7,867,868 bytes; SHA-256 c7036c64e3a49ea9d8642c29082c42537e2c8ba0863d43d3cbd4fbb098603da7). Exact-head QA-005 [42451182867](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42451182867) passed its disposable API 35 x86_64 emulator workflow. QA-011 remains blocked_service_disabled; QA-012 is structural only, not spoken TalkBack acceptance. No physical Pixel 9 Pro was tested.

AGENT-005U adds a test-only child-process regression at the pre-COMMIT boundary. The proxy pauses before forwarding the SQLite COMMIT after the ledger UPDATE has executed. The parent terminates the process, reopens the ledger and requires the row to remain RESERVED, verifies that the enrollment writer lock was released, then proves one valid claim succeeds and the next is rejected. No production Android source, permission, service, executor, shell bridge or device action changes.

Exact-head CI for this implementation is pending at commit creation. The same-host test does not prove power-cut durability, filesystem corruption recovery, multi-host locking or exactly-once external side effects. The independent human security review of SEC-021A/B/C and the trusted in-process callback boundary remains pending. Keep PR #1 draft/open and keep the real executor disconnected.

Milestones remain M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete.

Next priority after this regression: independent security review of SEC-021A/B/C and the cross-store callback trust boundary. Do not add an executor or expand device integrations before that gate is approved.


## AGENT-005V — signed enrollment revocation process-death recovery (2026-11-08)

Audit baseline: authorized branch feat/phase1-agentic-phone at ff6f2c5b31cb77afe3c457e2db37b17b0b935897; complete recursive tree 370 entries, not truncated; 20 recent commits inspected; 319 commits ahead of main, zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 alone uses the authorized branch, targets main, remains draft/open, and has no submitted reviews or inline threads. The branch reports protected=false; branch-protection endpoint access was unavailable, so required-check enforcement is not asserted. PROJECT-ADAPTER.md and this roadmap exist; repository SKILL.md is absent; the upstream shared factory package remains unverified and is not claimed installed.

AGENT-005V adds two test-only subprocess regressions to tests/test_owner_enrollment_registry.py:

- **Before COMMIT:** a child process applies a signed revocation update and history insert, pauses before forwarding the real SQLite COMMIT, then is terminated. Reopening proves the enrollment remains active at generation 1, history remains unchanged, one later dispatch claim succeeds, and a duplicate claim is rejected.
- **After COMMIT:** the child forwards the real SQLite COMMIT, emits a marker, then is terminated before returning from apply_signed_enrollment. Reopening proves the enrollment is inactive at generation 2, the revocation history is present exactly once, and a previously reserved action is denied with DEVICE_NOT_ACTIVE while remaining RESERVED.

Implementation commit: [f9345a7](https://github.com/Davidcarmelalex/MrNothing-OS/commit/f9345a75a73457c858b3825682c26ef365c5d49f). No production source, Android source, permission, executor, shell bridge, network listener or device behavior changed.

Exact implementation-head verification: Phase 1 push [42459446849](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42459446849) and PR [42459451010](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42459451010) passed; both Python-policy jobs ran **770 tests** and passed. Android unit tests, debug assembly, clean repeat debug APK comparison, strict dependency verification, modified-dependency negative control and Android source-manifest gate passed on push and PR.

CI-003 independent unsigned reproducibility push [42459446874](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42459446874) and PR [42459451018](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42459451018) passed. Independent runners produced byte-identical unsigned release APKs (7,867,868 bytes; SHA-256 c7036c64e3a49ea9d8642c29082c42537e2c8ba0863d43d3cbd4fbb098603da7; normalized-entry SHA-256 37b7e6846eaa4f58f143f430cb84aa481e4858c0cde392a7f2526cd8b89b9462). Runtime inventory, SPDX runtime SBOM, toolchain and scoped 1,260-component build-environment inventory/SBOM matched. CI-003 reports reproducible=true, release_ready=false.

Exact-head QA-005 [42459451011](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42459451011) passed the disposable Android 15/API 35 x86_64 emulator workflow. Thirty instrumentation tests started and finished; the complete job passed. QA-005 launcher/recovery, QA-006 through QA-010, QA-013, QA-020B2 and QA-020B3 passed. QA-011 remains blocked_service_disabled; QA-012 is structural only, not spoken TalkBack. No physical Pixel 9 Pro was tested.

Independent human security review of SEC-021A/B/C and the trusted in-process callback boundary remains **PENDING**. The real executor remains disconnected. No milestone is complete: M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED.

Next bounded task: AGENT-005W, signed enrollment commit-acknowledgement-loss fault injection, including pre/post-commit recovery, row/history atomicity and duplicate-statement replay rejection. Keep it test-only and preserve the fail-closed executor boundary.


## AGENT-005Y — read-only enrollment outcome reconciliation (2026-11-08)

Audit baseline: authorized branch `feat/phase1-agentic-phone` at `6f1f554faae5c9cdab9facd85fb0f9e646a73178`; recursive Git tree 372 entries, not truncated; latest 20 branch commits inspected; 323 commits ahead of `main`, zero behind. Six open PRs (#1 and #3–#7) inspected. PR #1 targets `main`, is open/draft, points to the authorized branch head, and has zero submitted reviews and zero inline review threads. PRs #3–#7 remain open/draft on their own branches; no other branch was modified. `PROJECT-ADAPTER.md` and this roadmap exist; repository `SKILL.md` is absent; the upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed installed.

At the starting head, Phase 1 PR run [42463827434](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42463827434), CI-003 PR run [42463827351](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42463827351), and QA-005 PR run [42463827369](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42463827369) all completed successfully. The Phase 1 jobs completed Python security tests/static compilation and Android unit/build/dependency-verification gates. CI-003 independent builders and verifier passed. QA-005 completed the disposable Android 15/API 35 x86_64 emulator sequence. QA-011 remains an availability preflight only; QA-012 is structural semantics, not spoken TalkBack. No physical Pixel 9 Pro was tested.

AGENT-005Y extends SEC-022 with a read-only `reconcile_outcome_unknown` API. It classifies exact committed history with a coherent latest device row as `APPLIED`; an absent exact history entry with a coherent prior state as `NOT_OBSERVED`; and metadata/history/database inconsistency as `UNRESOLVED`. All outcomes set `automatic_retry_permitted=false`. The typed exception now includes the owner identifier as bounded reconciliation metadata. Regression assertions cover applied initial enrollment/rotation/revocation, not-observed rollback-failure recovery, mismatched metadata and corrupt-database fail-closed behavior.

This API is an observation aid, not an authorization or retry mechanism. It does not protect against a privileged actor replacing a valid database with a different valid snapshot. No Android permission, network listener, executor, shell bridge, or device action is connected. Exact-head CI and QA for this implementation must pass before acceptance; independent human security review remains pending.

Milestones remain M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 PERMISSION-CONTROLLED INTEGRATIONS NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 PHYSICAL HARDWARE VALIDATION BLOCKED; M8 PRODUCTION READINESS BLOCKED. No milestone is complete.

Next task: independent security review of SEC-021A/B/C and SEC-022/AGENT-005Y, including database replacement threat assumptions and the trusted in-process final-admission callback boundary. Keep the real executor disconnected.


## AGENT-005Z — pinned build-tool download resilience (2026-11-08)

Audit baseline: authorized branch `feat/phase1-agentic-phone` at `1de4c02404ca3adce9052afbb5d282d6cfa9edb8`; recursive Git tree 372 entries, not truncated; compare against `main` reports 324 commits ahead and zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 targets `main`, remains open/draft, and has no submitted reviews or inline review threads. The branch is unprotected and required status-check enforcement is off. `PROJECT-ADAPTER.md` and this roadmap exist; repository `SKILL.md` is absent; the upstream shared package remains unverified and is not claimed installed.

The current-head audit found that Python policy passed (777 tests) and QA-005 passed on the disposable Android 15/API 35 x86_64 emulator (30/30 instrumentation tests, zero skipped/failed). Android build and CI-003 did not complete: the exact-head runs repeatedly received HTTP 504 while downloading Gradle 8.9, Temurin 17.0.13+11, or the Kotlin compiler artifact. Failed-job reruns on push and PR also failed at dependency acquisition. No Android build assertion failure or current-head reproducibility result is claimed.

AGENT-005Z adds a shared pinned Gradle downloader and aligns the Android workflows to exact Eclipse Temurin 17.0.21+9, matching the Temurin build observed in the Phase 1 Ubuntu 24.04 runner toolcache. The downloader permits only Gradle-operated HTTPS distribution endpoints, retries transient transport failures, enforces TLS 1.2+, verifies the pinned Gradle 8.9 SHA-256 before atomic placement, rejects unsupported versions, and fails closed on checksum mismatch. No community mirror or caller-supplied URL is accepted. Both workflows use the same helper.

The CI-003 static workflow gate now checks exact JDK alignment, shared downloader usage, official-host allowlisting, checksum-before-placement ordering, unsupported-version rejection and transport-failure fallback. A local shell syntax check and eight focused static/fault-injection tests passed in a temporary harness; exact repository CI remains the acceptance gate.

The JDK pin change is a deliberate toolchain baseline update from Temurin 17.0.13+11 to 17.0.21+9. Historical CI-003 evidence for 17.0.13+11 remains historical and does not satisfy new-head acceptance. The new exact-head Phase 1, CI-003 and QA-005 workflows must pass before this change is accepted.

No Android app source, permission, consent, enrollment, executor, shell bridge, network listener, OTA or release-signing path changed. Independent human security review of SEC-021A/B/C and SEC-022/AGENT-005Y remains pending. The real device executor remains disconnected. No physical Pixel 9 Pro was tested. No milestone is complete: M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED.

Next priority: independently review SEC-021A/B/C and SEC-022/AGENT-005Y, then accept the new exact-head CI results. Do not connect the real executor before independent security approval.


### AGENT-005Z correction — shell interpolation guard (2026-11-08)

A post-push source inspection caught a quoting defect in the first downloader commit: the shell URL template placeholders were emitted literally instead of expanding the pinned version and endpoint array. The initial commit is therefore not accepted. The follow-up corrects the shell interpolation and adds explicit static assertions for the URL template and loop expansion. Exact-head CI on the corrected commit is mandatory; no Gradle download/build success is claimed for the defective intermediate commit.


### AGENT-005Z static-gate correction (2026-11-08)

The local fixture run caught a second test-only defect: the existing concurrency assertion had lost the `ci003-` group prefix when the test was expanded. The assertion is restored to the workflow's actual group string. The corrected eight-test harness must pass before exact-head CI acceptance; no result from the intermediate failing assertion is counted as a pass.


## AGENT-005ZB — Maven Central fallback and verified Gradle cache (2026-11-08)

At corrected head `735a572145e8d9df83cefb249d7555fb7a39170c`, both Python policy jobs passed with 782 tests. Phase 1 Android jobs reached Gradle but failed resolving `kotlin-compiler-embeddable:2.0.21` after the Maven Central request redirected to the JetBrains GitHub release and returned HTTP 504. CI-003 showed mixed outcomes: one builder reached the Kotlin compiler download and failed there; another received HTTP 504 from both Gradle distribution endpoints. The third configured Gradle endpoint did not resolve in the hosted runner DNS and was removed. Exact-head QA-005 was still in progress at audit close.

AGENT-005ZB adds the canonical Sonatype Maven Central endpoint `repo1.maven.org` before `mavenCentral()` and moves the Gradle Plugin Portal ahead of Maven Central for plugin resolution. Strict dependency verification remains enabled. Both Android workflows now use `actions/setup-java` Gradle caching with a custom cache path containing `~/.gradle/caches` and `~/.gradle/distributions`; pull-request jobs are read-only cache consumers. The pinned Gradle 8.9 downloader verifies cached archives before reuse, rejects symlinks/non-regular files, fails closed on cache checksum mismatch, and downloads only from the two Gradle-operated HTTPS distribution endpoints. The third endpoint was removed because the hosted runner could not resolve its DNS name.

The static gate now checks repository order, cache isolation, shared pinned JDK, checksum validation, cache-hit behavior, cache-tamper rejection and official-host failover. Local shell syntax and focused test results are recorded after execution; exact-head push/PR CI and QA-005 remain the acceptance gate. No Android application behavior or device-control code changed. Independent security approval and physical Pixel 9 Pro validation remain pending.


### AGENT-005ZB repository-order correction (2026-11-08)

The first exact-head run after AGENT-005ZB exposed a strict dependency-verification failure for the Kotlin plugin marker POM when Gradle Plugin Portal was moved ahead of Maven Central. This was an integrity-gate failure, not a reason to update or disable checksums. The repository order was corrected to preserve the original Maven Central-before-Plugin-Portal precedence, with Sonatype repo1 added only after Maven Central. Exact-head CI must re-run on the corrected order. The failed intermediate run is not accepted.


## AGENT-005ZC — QA-005 build-tool and cache parity (2026-11-08)

Audit baseline: authorized branch `feat/phase1-agentic-phone` at `44f3b5597c48dbc6a92b2f965a872a6fced1128d`; recursive Git tree contained 374 entries and was not truncated; `main...feat/phase1-agentic-phone` was 329 commits ahead and zero behind. Twenty recent commits were inspected. Six open PRs (#1 and #3–#7) were audited. PR #1 targets `main`, remains open/draft, points to the authorized branch, and has no submitted reviews or inline review comments. `PROJECT-ADAPTER.md` and this roadmap exist; repository `SKILL.md` is absent; the upstream shared factory package remains unverified and is not claimed installed.

Exact-head rerun attempt 3 at the audit head:
- Phase 1 push [42471149042](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42471149042): passed. Python policy/static suite reported 785 tests; Android debug unit/build, clean repeat APK comparison and CI-005 modified-dependency negative control passed.
- Phase 1 PR [42471152946](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42471152946): Python policy/static suite reported 785 tests and passed; Android Gradle distribution acquisition failed after repeated HTTP 504 responses from both official Gradle endpoints.
- CI-003 push [42471149025](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42471149025) and PR [42471152940](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42471152940): independent builder jobs failed resolving `kotlin-compiler-embeddable:2.0.21` after the Maven Central request redirected to the JetBrains GitHub release and returned HTTP 504; the cross-runner verifier was skipped.
- QA-005 PR [42471152984](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42471152984): failed during Gradle dependency resolution on the same Kotlin compiler HTTP 504; the emulator did not start.

These failures occurred during external tool/dependency acquisition, before Android test/build assertions or emulator instrumentation. No checksum was weakened and no community mirror was introduced.

AGENT-005ZC closes a workflow-parity gap: QA-005 now pins Temurin 17.0.21+9, uses the same Gradle dependency/distribution cache paths as Phase 1 and CI-003, marks pull-request cache consumers read-only, and calls the shared `scripts/download_gradle_distribution.sh` helper. Two static regression tests enforce the shared JDK/cache configuration and prohibit a separate direct single-host Gradle download. CI-004 documentation now covers all three Android workflows.

Only CI workflow, CI static-test, CI documentation and roadmap files change. No Android application source, Python security runtime, permission, consent, enrollment, executor, network listener, OTA or release-signing behavior changes. Exact-head CI after this commit is pending; the prior-head passing Phase 1 push is not substituted for new-head acceptance.

Independent human security review of SEC-021A/B/C and SEC-022/AGENT-005Y remains PENDING. No physical Pixel 9 Pro was tested. The executor remains disconnected. No milestone is complete.

Next priority: obtain independent security review of SEC-021A/B/C and SEC-022/AGENT-005Y, including the trusted final-admission callback boundary. Keep the real executor disconnected until that gate is approved.


## AGENT-005ZD — CI-006 checksum binding to the shared Gradle downloader (2026-11-08)

Audit baseline: authorized branch `feat/phase1-agentic-phone` at `4feef32563d5a9877350120cfeb4b8a50ad41ce1`; the complete recursive tree and recent branch history were rechecked; the branch remains 330 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) remain; PR #1 is open/draft against main. The project adapter and roadmap exist; repository `SKILL.md` is absent; the upstream shared package remains unverified.

The AGENT-005ZC exact-head Phase 1 push passed with 787 Python tests and Android debug build/unit/repeat-build/dependency-negative-control gates. CI-003 builders then completed Gradle release build, merged/packaged manifest gates and dependency-verification negative control, but failed while generating the scoped build-environment SBOM: `build_environment_sbom.py` still searched for the old inline `echo SHA256 ... | sha256sum --check` workflow command that CI-004 had intentionally replaced with the shared verified downloader. This was a parser/contract drift, not an APK build or checksum failure. The CI-003 PR attempt showed the same parser failure on one builder and an upstream Gradle 504 on the other.

AGENT-005ZD updates CI-006 to read the explicit `--gradle-sha256` provenance value, adds a static gate requiring it to match the shared downloader's pinned digest, and adds a regression test that rejects a missing provenance checksum. The inventory continues hashing the actual downloaded Gradle ZIP and comparing it with the expected digest before recording the component. No checksum was changed, no mirror was added and no integrity gate was bypassed.

Exact-head Python/Android/CI-003/QA-005 reruns after this correction are pending. No Android app source, permission, consent, enrollment, executor, network listener, OTA or release-signing behavior changes. The real executor remains disconnected. No physical Pixel 9 Pro was tested. Independent human security review of SEC-021A/B/C and SEC-022/AGENT-005Y remains pending. No milestone is complete.

Next priority: independent security review of the enrollment and final-admission chain, including SEC-021A/B/C, SEC-022 and the trusted in-process callback boundary. Keep the real executor disconnected until approval.


## AGENT-005ZE — CI-006 inventory uses the verified cached ZIP (2026-11-08)

At head `71d2cdd59b528c60454df3aa7c8bb9a1d3e4fd2a`, Phase 1 push passed with 789 Python tests and Android debug build/unit/repeat-build/dependency-negative-control checks. CI-003 push and PR builders completed release Gradle builds, merged/packaged manifest security gates and dependency-verification negative controls, then failed in CI-006 inventory generation because `--gradle-zip` still referenced `$RUNNER_TEMP/gradle-8.9-bin.zip`. The shared downloader writes the verified archive to `$HOME/.gradle/distributions/gradle-8.9-bin.zip` and only extracts it to RUNNER_TEMP; it does not copy the ZIP there.

AGENT-005ZE changes the CI-003 inventory argument to hash the actual verified cache file and adds a static gate that rejects the nonexistent temporary ZIP path. CI-006 documentation records the path contract. The actual archive SHA-256 remains independently checked against the workflow provenance pin. No dependency checksum, signature, mirror policy or security control was changed.

Exact-head CI after this fix remains pending. No Android runtime or device-control source changed. No physical Pixel 9 Pro was tested. Independent human security review remains pending; no milestone is complete; the real executor remains disconnected.

Next task: obtain independent security review of SEC-021A/B/C, SEC-022 and the final-admission callback boundary before any executor integration.


## AGENT-005ZF — enforce SQLite query-only reconciliation (2026-11-08)

Audit baseline: authorized branch `feat/phase1-agentic-phone` at `9bdcb841338dc78593c8cd8d2bf210d660c65c67`; recursive tree contained 377 entries and was not truncated; latest 20 branch commits inspected; `main...feat/phase1-agentic-phone` was 332 commits ahead and zero behind. Six open PRs (#1 and #3–#7) were audited. PR #1 remains open/draft against main and has no submitted reviews or inline review threads. `PROJECT-ADAPTER.md` and this roadmap exist; repository `SKILL.md` is absent; the upstream shared factory package remains unverified and is not claimed installed.

The latest exact-head workflows at the audit baseline passed: Phase 1 push [42473218565](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42473218565) and PR [42473221997](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42473221997); CI-003 push [42473218568](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42473218568) and PR [42473221917](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42473221917); QA-005 PR [42473222104](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42473222104). The Phase 1 Python job reported 790 passing tests; Android unit/build, dependency-verification negative control, independent unsigned-build comparison and disposable-emulator workflow passed. QA-011/012 remain preflight/structural checks, not spoken TalkBack acceptance.

Author-side adversarial review of AGENT-005Y found that `reconcile_outcome_unknown` issued only read statements but opened its SQLite connection in read-write mode. AGENT-005ZF now enables `PRAGMA query_only=ON` before starting the read snapshot. Two regressions prove (1) SQLite itself rejects a write attempt before `BEGIN`, while reconciliation still returns APPLIED, and (2) an exact history row paired with a divergent current device row returns UNRESOLVED. All outcomes continue to deny automatic retry.

This is defense in depth for the local reconciliation API, not an independent security approval. The database-replacement threat assumption and SEC-021A/B/C trusted final-admission callback boundary still require independent review. The executor remains disconnected. No physical Pixel 9 Pro was tested. No milestone is complete.

Next task: independent security review of SEC-021A/B/C and SEC-022/AGENT-005Y/005ZF, including transaction snapshot semantics, database replacement limits and final-admission callback provenance. Keep the real executor disconnected until approval.


## AGENT-006A — reconcile threat-model evidence and dispatch risk mapping (2026-11-08)

**Audit head:** `3fd85d229debc361ddece0e9cf2aeec567e104cd`. The audit confirmed 377 tree entries, 333 commits ahead/0 behind main, six open PRs, and no independent PR #1 review submissions or inline threads. `PROJECT-ADAPTER.md` is present; `SKILL.md` and the upstream shared package remain unverified.

The prior threat model cited source baseline `680d5cbd`, which predated SEC-021A/B/C and SEC-022. This bounded documentation task refreshes its evidence baseline to `3fd85d22`, maps the current lock-coupled dispatch, live-capability final-admission, cross-store acknowledgement-loss and typed enrollment reconciliation prototypes into B4, TM-06, TM-07 and TM-12, and explicitly records the single-host SQLite, trusted in-process callback, no-executor and no-power-loss guarantees. The engineering scorecard now distinguishes the current 2026-11-08 evidence snapshot from its historical 2026-11-02 snapshot.

**Exact-head evidence at the audited source baseline:** Phase 1 push [42476490546](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42476490546) and PR [42476493866](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42476493866) passed with 792 Python tests each and Android unit/build/dependency checks. CI-003 push [42476490516](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42476490516) and PR [42476493841](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42476493841) passed independent byte-identical unsigned APK verification. QA-005 PR [42476493897](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42476493897) passed the API 35 x86_64 emulator sequence with 30/30 instrumentation progress, zero failures and zero skips. QA-011 did not establish spoken TalkBack; QA-012 was structural only.

This task changes documentation only; it does not alter Python/Android runtime code, permissions, trust records, listener, executor, device state, signing or OTA. The documentation update is not an independent security review and does not approve the callback boundary. The real executor remains disconnected; no physical Pixel 9 Pro was tested; no milestone is complete.

**Next task:** obtain an independent security review of SEC-021A/B/C and SEC-022/AGENT-005Y/005ZF. The reviewer must inspect lock ordering, exact callback provenance and side-effect-free behavior, database replacement/rollback assumptions, commit-ack-loss handling and the no-executor boundary. Do not connect an executor until the reviewer records identity, date, reviewed SHA, findings and disposition.


## AGENT-006B — exact-head evidence reconciliation and scorecard refresh (2026-11-08)

**Audit head:** `415ac44dec4f68562a8b037ea0964e6f0f5ff89b`; complete recursive tree 377 entries, not truncated; 20 recent commits inspected; branch 337 ahead/0 behind main. Six open PRs (#1 and #3–#7); PR #1 remains draft against main with 337 commits and 313 changed files, zero review submissions and zero inline review threads. PRs #3–#7 are separate draft branches and were not modified. `PROJECT-ADAPTER.md` exists; repository `SKILL.md` is absent; upstream shared package remains unverified.

This bounded task reconciles the current repository/CI state into `docs/ENGINEERING-SCORECARD.md`. Source/test baseline remains `3fd85d22`; subsequent commits through `415ac44d` are documentation-only. No Android/Python runtime source, manifest permission, trust store, listener, executor, device state, signing or OTA behavior changed.

**Exact-head evidence at `415ac44d`:**
- Phase 1 push [42481269680](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42481269680) and PR [42481273565](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42481273565) passed. Both Python policy jobs explicitly reported 792 tests passed. Android Gradle unit tests, debug assembly, repeat debug-APK byte comparison, strict dependency verification and modified-dependency negative control passed.
- CI-003 push [42481269679](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42481269679) and PR [42481273563](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42481273563) passed. Independent runners produced byte-identical unsigned APKs (7,867,868 bytes; 21 ZIP entries; SHA-256 `c7036c64e3a49ea9d8642c29082c42537e2c8ba0863d43d3cbd4fbb098603da7`; normalized-entry SHA-256 `37b7e6846eaa4f58f143f430cb84aa481e4858c0cde392a7f2526cd8b89b9462`). The scoped build-environment inventory contains 1,260 components and explicitly does not cover the complete hosted-runner image. Provenance reports `reproducible=true`, `release_ready=false`.
- QA-005 PR [42481273606](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42481273606) passed on a disposable Android 15/API 35 x86_64 emulator. The job log reports the 15-test instrumentation suite and progress through 28/30 with zero failures/zero skips; no final 30/30 aggregate line was present in the fetched log, so do not claim 30/30 completion. QA-006 through QA-010, QA-013, QA-020B2 and QA-020B3 passed. QA-011 reports `blocked_service_disabled`; QA-012 is structural only, not spoken TalkBack acceptance.
- The latest exact-head evidence does not establish physical Pixel 9 Pro/StrongBox behavior, signed release/OTA, power-loss durability, independent security approval or production readiness.

**Independent security gate remains pending.** A reviewer separate from the implementation author must challenge SEC-021A/B/C and SEC-022/AGENT-005Y/005ZF, including lock ordering, final-admission callback provenance, cross-store transaction/reconciliation semantics, database replacement/rollback assumptions and fail-closed recovery. Record reviewer identity, date, reviewed SHA, findings and disposition. Keep the real executor disconnected until that review is accepted.

**Milestones:** M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED pending authorized physical Pixel 9 Pro validation; M8 BLOCKED. No milestone is COMPLETE. No percentage is inferred from CI.

**Next task:** obtain the independent security review described above. Do not implement executor integration as a substitute for that gate.


## AGENT-006C — prepare independent security review packet (2026-11-08)

**Audit head:** `e49a9e33fca842601554e2357d0dfe9130a14f1e`. Complete recursive tree: 377 entries, not truncated; 20 recent commits inspected; branch 339 ahead/0 behind main; merge base `f3c9a701d2a337de8ef393ac14df044a79843d60`. Six open PRs (#1 and #3–#7) were inspected. PR #1 is open/draft against main at the audited head, 339 commits and 313 changed files, with zero review submissions and zero inline review threads. PRs #3–#7 remain on their separate branches and were not modified. `PROJECT-ADAPTER.md` exists; repository `SKILL.md` is absent; upstream shared package remains unverified. Rulesets endpoint returned an empty list; branch-protection read was denied with HTTP 403 and remains unverified.

This bounded task creates `docs/SECURITY-REVIEW-PACKET-AGENT-006C.md`. It records the exact baseline, scoped implementation/test files, adversarial review questions for SEC-021A/B/C and SEC-022/AGENT-005Y/005ZF, independent test procedure, acceptance criteria, reviewer record, and stop condition. The packet is explicitly not an independent review, approval, certification, or executor authorization. No reviewer identity was available; the independent gate remains PENDING.

**Exact-head CI evidence at `e49a9e33`:**
- Phase 1 push [42485836414](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42485836414) and PR [42485840667](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42485840667) passed. Both Python policy jobs reported 792 tests passed. Android `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat debug-APK comparison, strict dependency verification, modified-dependency negative control, Python static compilation, and Android source-manifest security gate passed.
- CI-003 push [42485836421](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42485836421) and PR [42485840826](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42485840826) passed. Two independent runners produced byte-identical unsigned APKs (7,867,868 bytes; 21 ZIP entries; SHA-256 `c7036c64e3a49ea9d8642c29082c42537e2c8ba0863d43d3cbd4fbb098603da7`; normalized-entry SHA-256 `37b7e6846eaa4f58f143f430cb84aa481e4858c0cde392a7f2526cd8b89b9462`). The scoped build-environment inventory contains 1,260 components and explicitly excludes the complete hosted-runner image. Provenance reports `reproducible=true`, `release_ready=false`.
- QA-005 PR [42485840704](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42485840704) passed on a disposable Android 15/API 35 x86_64 emulator. Logged checks include launcher start, 200% font scaling, HOME consent/cancel/accept, stock-launcher recovery, keyboard focus, insecure enrollment denial, owner-trust UI checks, and credential-prompt cancellation. QA-011 reports `blocked_service_disabled`; QA-012 is structural only; spoken TalkBack is not accepted.
- These runs do not establish physical Pixel 9 Pro/StrongBox behavior, signed release/OTA, power-loss durability, independent security approval, or production readiness.

No runtime source, Android permission, trust record, listener, executor, device state, signing configuration, OTA or firmware was changed. The real executor remains disconnected.

**Milestones:** M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED pending authorized physical Pixel 9 Pro validation; M8 BLOCKED. No milestone is COMPLETE.

**Next task:** a separate reviewer must complete the packet against the exact current head, record identity/date/SHA/findings/disposition, and submit a GitHub review on PR #1. Do not implement executor integration as a substitute for this gate.


## AGENT-006D — quarantine unattended legacy HERMES shell tasks (2026-11-08)

**Audit baseline:** \`92680812645c3d8f549e049bb7d75b80ed702ec6\`; 378-entry recursive tree, not truncated; branch 341 ahead / 0 behind \`main\`; PR #1 open/draft with 341 commits and 314 changed files. The source baseline for the independent SEC-021/SEC-022 review remains \`e49a9e33\`; the two commits between it and \`92680812\` were documentation-only.

**Finding:** the legacy \`agents/hermes/agent.py\` used \`subprocess.run(..., shell=True)\` for free-form task strings, and the due-task scheduler could execute shell tasks without a fresh interactive approval.

**Bounded change:** shell tasks now require an explicit interactive confirmation bound to the exact command text; parsing uses \`shlex\`, execution uses \`shell=False\` with a 30-second timeout, and shell-interpreter invocations are rejected. The background scheduler does not execute shell tasks; it marks them approval-required and notifies once. Typed notification tasks remain schedulable. Added regression coverage and updated the HERMES README and TM-08 threat entry.

**Limitations:** this is not a sandbox, strong owner authentication, OS permission boundary or production executor. A manually approved executable still runs with the local Termux process's privileges. The legacy helper remains disconnected from the native Android command router. Independent security review of SEC-021A/B/C and SEC-022 remains pending.

**Exact-head CI:** pending at commit creation. Record the actual GitHub Actions outcomes before treating this task as accepted.

**Next:** independent reviewer completes the AGENT-006C packet on the exact current head. Do not connect any executor as a substitute.


## AGENT-006E — default-deny legacy OpenClaw network diagnostics (2026-11-08)

**Audit baseline:** authorized branch feat/phase1-agentic-phone at 596593914fd040ea9881605a0e9e183e7d228e09; complete recursive tree 380 entries, not truncated; 20 recent commits inspected; branch 343 ahead / 0 behind main; merge base f3c9a701d2a337de8ef393ac14df044a79843d60. Six open PRs (#1 and #3–#7) were inspected. PR #1 is open/draft against main, with 343 commits and 318 changed files; zero submitted reviews and zero inline review threads. PROJECT-ADAPTER.md exists; repository SKILL.md is absent. The authorized Library search did not locate the upstream shared factory package; it remains unverified and is not claimed installed.

**Finding:** agents/openclaw/agent.py constructed which, ping, nmap, dig, and curl commands as shell strings and accepted an arbitrary target. The CLI could therefore invoke network probes without an explicit per-target authorization step. The module was a legacy Termux prototype and was not connected to the native Android router.

**Bounded implementation:** OpenClaw now accepts only fixed executable names with argv arrays and shell=False; argument count/length and timeouts are bounded. Tool discovery uses shutil.which. Network scans require an exact IPv4 literal in MRNOTHING_OPENCLAW_ALLOWED_TARGETS, restricted to RFC1918 private, loopback, or link-local ranges, plus a fresh typed SCAN <target> confirmation. Public/global IPs, hostnames, URLs, CIDRs, malformed allowlists and whitespace variants fail closed. DNS probing was removed. The socket fallback is reachable only after both gates. Wi-Fi information remains a local read available only after the operator explicitly selects wifi.

Added tests/test_openclaw_agent.py with 17 tests for target parsing, malformed/public/unlisted targets, confirmation absence/decline/type/exception, no-side-effect denial, argv-only subprocess execution, fixed executable allowlisting, bounded timeouts/arguments, no shell-based tool discovery, no DNS probing, socket fallback scope, and local Wi-Fi argv. Added docs/OPENCLAW-LEGACY-SAFETY.md; updated the README agent row and TM-08 threat mapping.

**Tests executed in the isolated working harness before push:** python -m unittest -q tests.test_openclaw_agent — 17/17 passed; python -m compileall -q agents/openclaw/agent.py tests/test_openclaw_agent.py — passed; static source assertions for shell=False, no shell=True, and removal of dig +short — passed. All subprocess/socket boundaries were mocked. No network scan, DNS query, third-party access, Termux installation, Android installation, or physical-device operation was performed. Full repository tests and Android CI must be taken from exact-head GitHub Actions after push.

**Limitations:** the environment allowlist and typed prompt do not prove target ownership, provide strong owner authentication, create a sandbox, or reduce the privileges of an approved Termux process. Keep OpenClaw disconnected from the Android command router. Other legacy helpers require a separate inventory; this change does not claim all shell execution has been removed from the repository.

**Exact-head CI at commit creation:** pending. Record actual push/PR Phase 1, CI-003 and QA-005 outcomes before acceptance.

**Independent review:** AGENT-006C remains PENDING_INDEPENDENT_REVIEW; no reviewer identity or separate GitHub review was available. This implementation does not satisfy or replace that gate.

**Milestones:** M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED pending authorized physical Pixel 9 Pro validation; M8 BLOCKED. No milestone is COMPLETE.

**Next:** obtain a separate reviewer for the exact-head AGENT-006C security packet. Then inventory any remaining legacy shell helpers (AGENT-006F) without executing them. Do not connect an executor as a substitute for either gate.


### AGENT-006E verification correction

The first Phase 1 push run for commit e9c5c19 ran 823 Python tests and failed one existing threat-model wording invariant requiring the exact phrase "subprocess shell execution". TM-08 now retains that phrase while distinguishing the OpenClaw mitigation from other legacy prototypes.

A review of the new API also removed the injectable confirmation callback: scan_network now invokes the module's own exact-target typed prompt. Tests patch that prompt at the unit boundary; production callers cannot supply a callback that simply returns True. The isolated 17-test suite and compileall were rerun after this correction. The failed first run remains in Actions history and is superseded only by fresh exact-head CI.


A second exact-head Phase 1 push run for 9abd382 also failed: two confirmation tests exposed a stale callable(confirm) guard left in the source after the signature was changed. The guard has now been removed, and the static regression explicitly rejects reintroduction. The first and second failed runs are retained as evidence; only a new exact-head CI pass can supersede them.


A third exact-head Phase 1 push run for 223ae25 exposed a stale function identifier: the callback-free scan path still called the removed name confirm(canonical), so three authorization tests failed closed. The call now targets the internal confirm_scan(canonical) prompt, and the static test asserts the correct internal function is used and the removed identifier is absent. The isolated 17-test suite and compileall passed after this correction. This is recorded as an implementation defect, not waived.


## AGENT-006F — harden legacy agent launch and approval boundaries (2026-11-08)

Implementation commits: c62c587647bf030cab59912b9d4798f62e4d1154 and fb5e1ce81b2ad93f2434e2433c8bd72238fd270c.

- agents/hermes/agent.py now requires an internal exact-command confirmation for interactive shell tasks, uses shlex plus argv-only shell=False, bounds command length and timeout, rejects shell interpreters, and leaves scheduled shell tasks pending for owner review instead of executing them unattended.
- core/main.py resolves only direct regular child agents, rejects path traversal and symlinks, bounds and parses argv, and requires a fresh exact-list confirmation before configured auto-start. The confirmation callback is not caller-injectable.
- The follow-up fixed regex and NUL/domain-separator escape literals. tests/test_core_agent_launcher.py covers valid direct-child resolution, traversal, symlinks, bounded argv, challenge binding, startup denial and callback-injection resistance.
- These are legacy Termux process controls, not a sandbox, Android permission boundary or native executor. A manually launched process still runs with the Termux user's privileges.

Audit at exact source head fb5e1ce81b2ad93f2434e2433c8bd72238fd270c: recursive tree 383 entries, not truncated; 20 recent commits inspected; branch 349 ahead / 0 behind main; six open PRs (#1 and #3–#7). PR #1 is open/draft against main at this exact head, 349 commits, 313 changed files, zero review submissions and zero inline review threads. PROJECT-ADAPTER.md exists; repository SKILL.md is absent; upstream shared package remains unverified. Branch is unprotected; rulesets query returned none.

Exact-head GitHub Actions:
- Phase 1 push 42498817883 and PR 42498821916: both Android and Python-policy jobs passed. Python security tests/static compilation and Android manifest gate passed; Gradle unit/build, repeat debug-APK comparison, strict dependency verification and modified-dependency negative control passed.
- CI-003 push 42498817824 and PR 42498822007: both independent builders and the cross-runner verifier passed.
- QA-005 42498822018: disposable Android 15/API 35 x86_64 emulator workflow passed, including launcher/recovery, large text, HOME consent/recovery, keyboard, owner-enrollment denial, authority UI and credential-prompt probe. QA-011 is explicitly availability preflight, not spoken TalkBack acceptance; QA-012 is structural semantics only.

No physical Pixel 9 Pro, StrongBox, spoken TalkBack, signed release/OTA, production deployment or independent security approval is established. The real Android executor remains disconnected.

## AGENT-006G — require owner confirmation for legacy Termux SMS (2026-11-08)

Scope: modules/whatsapp/whatsapp.py, tests/test_whatsapp_consent.py, docs/AGENT-006G-TERMUX-MESSAGING-CONSENT.md, and TM-14 in docs/THREAT-MODEL.md.

- Direct Termux SMS now requires an internal one-time typed challenge derived from the normalized recipient and exact message. No caller-supplied confirmation callback is accepted.
- Recipient syntax is bounded; message length is capped at 1,600 characters; empty/NUL-containing messages fail closed.
- SMS is invoked only through a fixed argv list with an explicit -- option terminator before the message, shell=False, a 10-second timeout and check=True. Logs record command completion, not carrier delivery, and do not record message content.
- WhatsApp opens a URL-encoded compose screen only. The log and documentation explicitly state that the owner must review and tap Send; opening the compose screen is not represented as delivery.
- Regression tests mock all subprocess/input boundaries. No real SMS, WhatsApp message, Termux installation, network request or device operation is performed.
- This module remains a legacy Termux prototype, not an Android permission provider or native HERMES integration. The interactive challenge is not strong owner authentication; independent review remains required before any agent integration.

Exact-head CI: pending at commit creation; record actual push/PR Phase 1, CI-003 and QA-005 results after completion.

Milestones: M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED pending authorized physical Pixel 9 Pro validation; M8 BLOCKED. No milestone is COMPLETE.


## AGENT-006H — make PaperClip local-only and inventory legacy external effects (2026-11-08)

**Audit baseline:** \`feat/phase1-agentic-phone\` at \`0f849e9d0fbbafba6c75bc69de2f8fa50432217b\`; complete recursive tree 385 entries, not truncated; latest 20 commits inspected; branch 351 commits ahead of \`main\`, zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 remains open/draft against \`main\` at this head with 351 commits and 313 changed files; it has zero submitted reviews and zero inline review threads. PRs #3–#7 remain separate QA-014/SEC-016/AGENT-004A workstreams; their branches were not modified. \`PROJECT-ADAPTER.md\` exists; repository \`SKILL.md\` is absent; the upstream shared package remains unverified and is not claimed installed.

**Baseline exact-head evidence:** Phase 1 push [42501121955](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42501121955) and PR [42501126635](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42501126635) passed; both Python-policy jobs reported 850 tests, and Android unit/build, repeat-build, dependency-verification negative control and manifest gate passed. CI-003 push [42501121902](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42501121902) and PR [42501126640](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42501126640) passed; independent builders produced byte-identical unsigned APKs and provenance reported \`release_ready=false\`. QA-005 PR [42501126615](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42501126615) passed on a disposable Android 15/API 35 x86_64 emulator. QA-011 remains read-only availability, not spoken TalkBack acceptance; QA-012 is structural semantics only. No physical Pixel 9 Pro was tested.

**Finding:** \`agents/paperclip/agent.py\` claimed local-only inference but called a Transformers pipeline with a remote TinyLlama model identifier when no local llama.cpp result was available. That could retrieve model/config artifacts from a model hub during ordinary prompt handling without a separate per-model network approval. The prompt itself was not shown to be uploaded, but implicit artifact retrieval contradicted the local-only claim and introduced unpinned model supply-chain contact.

**Implementation:** removed the Transformers/model-hub fallback. PaperClip now selects only a direct-child local GGUF file, rejects symlinked model directories/files/executables, resolves only \`$HOME/mrnothing/bin/llama-cli\` (no PATH/which fallback), uses argv-only \`shell=False\`, a 120-second timeout and 256-token cap, rejects non-text/NUL/over-8,192-character prompts, and redacts prompt content from processing logs. If no local model/executable is ready, it uses deterministic local fallback text. Local model provenance and executable integrity remain the owner's responsibility; this is not a sandbox.

**Legacy inventory:** added \`docs/AGENT-006H-PAPERCLIP-OFFLINE-BOUNDARY.md\` covering PaperClip, HERMES, core agent launch, OpenClaw, network, voice, WhatsApp/SMS, Web3 wallet and the native Android router. It records that the native external-effect allowlist is currently empty and that the document is not a runtime policy engine. Critical remaining risks include plaintext wallet private-key persistence and an invalid fallback key/address pair; unconfirmed network diagnostics; microphone/transcript handling; and plaintext PaperClip conversation memory.

**Regression coverage:** added 10 PaperClip tests for direct-child local GGUF selection, symlink rejection, fixed local executable resolution, no PATH fallback, argv-only execution, prompt bounds, no model-hub fallback and prompt-log redaction. The threat-model structural test now requires unique threat IDs through TM-15. All subprocess/model execution boundaries are mocked; no network probe, model download, model execution, SMS, WhatsApp message, microphone capture, wallet generation/signing, Termux install or device operation is performed.

**Exact-head CI for this implementation commit:** pending at commit creation; record the actual push/PR Phase 1, CI-003 and QA-005 outcomes in the PR verification comment after completion.

**Independent review:** AGENT-006C remains PENDING_INDEPENDENT_REVIEW. This inventory does not satisfy that gate or authorize executor integration.

**Milestones:** M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is COMPLETE.

**Next:** AGENT-006I should block legacy wallet use with real funds until plaintext private-key persistence and the invalid fallback are removed; then harden network and voice modules with explicit target/capture consent. Keep all legacy modules disconnected from the native Android router.


## AGENT-006J — consent-gated legacy network diagnostics (2026-11-09)

**Audit baseline:** branch feat/phase1-agentic-phone at 3554fefab1a1745bfc485b8becdef3562a7c40c1; complete recursive tree 389 entries, not truncated. The latest 20 branch commits were inspected. The branch is 353 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected; PR #1 remains the draft umbrella PR against main, with no submitted review or inline review threads. PROJECT-ADAPTER.md exists; repository SKILL.md is absent; the upstream shared package remains unverified and is not claimed installed.

**Architecture/instruction audit:** Kotlin launcher and Android tests remain separate from the Python/Termux legacy modules. CommandRouter remains fail-closed; no production Android executor, network listener, AccessibilityService or MediaProjection provider is connected. The project adapter assigns Android, AI/agents, security, UX/accessibility, CI/QA, hardware/release and independent supervisor responsibilities; those are ownership roles, not a claim that separate reviewers were launched.

**Baseline exact-head evidence:** Phase 1 push [42507369582](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42507369582) and PR [42507373834](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42507373834) passed; the Python policy and Android jobs passed. CI-003 push [42507369711](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42507369711) and PR [42507373804](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42507373804) passed, including two independent unsigned builders and the cross-runner verifier. QA-005 PR [42507373815](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42507373815) passed on a disposable Android 15/API 35 x86_64 emulator. The workflow reports structural/availability accessibility checks; QA-011 is not spoken TalkBack acceptance and QA-012 is not spoken-navigation acceptance. No physical Pixel 9 Pro was tested. The exact-head Python suite reported 872 tests passed on both push and PR.

**Finding:** the standalone network module previously called curl for public-IP lookup, accepted arbitrary ping targets/counts, ran speedtest-cli with provider-selected servers, monitored a fixed public target without per-probe consent, and used a UDP route-selection connect to a fixed public address for local-IP discovery.

**Implementation:** AGENT-006J replaces those paths with exact private-IPv4 allowlisting (MRNOTHING_NETWORK_ALLOWED_TARGETS), internal target/count-bound typed confirmation, 1–3 packet bounds, fixed argv/shell=False, a 10-second ping timeout, thread-safe process-local per-target/global rate limits, and a 1–300 second monitor with 30–60 second interval and no more than 10 probes. Each monitor probe requires fresh confirmation. Public-IP lookup is restricted to a fixed HTTPS api.ipify.org request after exact consent, with TLS verification, no ambient proxy, no redirect, 6-second timeout and a 46-byte read bound. Provider-selected speed tests are disabled. Local IP discovery uses local interface ioctl and sends no packet.

**Regression coverage:** new offline tests cover private IPv4 parsing and allowlist failure, exact confirmation and noninteractive denial, bounded counts, fixed argv and timeout, rate limits, fixed-host HTTPS/no-proxy/no-redirect behavior, response bounds, disabled speed tests, per-probe consent and local ioctl without network send. Tests mock input, subprocess, HTTP and ioctl boundaries. No network traffic is performed by tests.

**Threat model:** TM-16 records outbound traffic disclosure and probe-abuse risks, mitigations and residual limitations. The network row in AGENT-006H's inventory is superseded by the dedicated AGENT-006J record; voice capture/transcript retention and PaperClip plaintext memory remain open.

**Independent review:** pending. The author cannot self-approve; review must challenge allowlist tampering, process-local rate-limit resets, fixed provider disclosure, proxy/redirect behavior and same-user Termux trust. The Android executor remains disconnected.

**Exact-head CI:** pending at commit creation; exact-head push/PR Phase 1, CI-003 and QA-005 results must be recorded in the PR verification comment after completion.

**Milestones:** M1 FOUNDATION IN PROGRESS; M2 OS INTERFACE IN PROGRESS; M3 AGENTIC INTELLIGENCE PARTIAL; M4 NOT STARTED; M5 PIXEL 9 PRO COMPATIBILITY NOT ACCEPTED; M6 SECURITY/PRIVACY IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is COMPLETE.


## AGENT-006K — legacy voice consent and transcript privacy (2026-11-09)

Audited parent: `d07390768eae1747fe759726b7d524d50a291299`. The existing `PROJECT-ADAPTER.md` is retained; upstream `SKILL.md` remains unverified. This bounded change hardens the standalone Termux voice helper: fresh exact typed confirmation for each 1–15 second STT request, transcript/TTS log redaction, fixed argv/timeouts, bounded speech data, executable symlink rejection, and fail-closed audio-file persistence pending a reviewed retention policy. Added 12 offline mocked voice regression tests, TM-17 and a structural threat-model test. Local targeted tests passed 12/12; exact-head hosted CI must be checked separately. No microphone capture or Android device action was performed. Independent AGENT-006C security approval remains pending; native executor disconnected. Milestones M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7/M8 BLOCKED. No milestone COMPLETE. Next: independently review authorization chain and voice-provider/cancellation assumptions; assess PaperClip plaintext conversation memory.

## AGENT-006L — PaperClip opt-in session-only memory (2026-11-09)

**Audit baseline:** `feat/phase1-agentic-phone` at `e8e77860d0d3af37f35877c121a6d899f7c0bbf1`; complete 393-entry recursive tree (not truncated), 10 recent commits and six open PRs audited. PR #1 is draft against main, with zero independent review submissions. `PROJECT-ADAPTER.md` exists; repository `SKILL.md` is absent and upstream shared package remains unverified. All five preceding exact-head GitHub workflows passed (Phase 1 push/PR, CI-003 push/PR and QA-005 PR), but QA-011 is availability only and QA-012 is structural only; no spoken TalkBack or physical Pixel acceptance.

**Finding:** `agents/paperclip/agent.py` automatically loaded and wrote `memory.json` as plaintext, storing up to 100 user/assistant messages without explicit consent or encryption. A compromised Termux user or permissive file could expose prior conversations. This was not a native Android memory provider.

**Bounded implementation:** Disabled persistent memory loading and saving; legacy `memory.json` is neither read, migrated, modified nor deleted. Fresh sessions default to memory OFF. The interactive `memory on` command explicitly opts into RAM-only retention (maximum 100 entries, bounded text); `memory off` and `forget` clear session conversations and facts and revoke opt-in. `save_memory` raises rather than silently reintroducing plaintext persistence. An existing legacy file triggers a content-free warning requiring owner-controlled cleanup. No cryptographic encryption or secure erase is claimed; memory can still exist in process RAM or OS-managed swap. Other process-level Termux protections remain out of scope.

**Tests:** Added `tests/test_paperclip_session_memory.py` with nine offline tests: default opt-out, legacy preservation, no opt-out retention, bounded opt-in, invalid input rejection, fail-closed legacy save, clearing/revocation, interactive opt-in/forget and source-level no JSON persistence. No model, network, SMS, microphone, wallet or Android device effect is invoked. Exact-head GitHub CI results must be checked after the final commit; do not infer pass from the prior head.

**Review gate:** AI/agents and security specialists must independently review the memory lifecycle, opt-in semantics, CLI disclosure, legacy-file cleanup guidance, RAM/swap exposure and future encrypted owner-authenticated storage. The implementation author cannot self-approve. Do not connect PaperClip to the native Android executor or restore persistence without a reviewed key management, encryption, access control, retention, export and deletion design.

**Milestones:** M1 foundation IN PROGRESS; M2 OS interface IN PROGRESS; M3 agentic intelligence PARTIAL; M4 device integrations NOT STARTED; M5 Pixel 9 Pro compatibility NOT ACCEPTED; M6 security/privacy IN PROGRESS; M7 physical hardware BLOCKED; M8 production readiness BLOCKED. No milestone COMPLETE.

**Next bounded task:** independent security acceptance of SEC-021A/B/C, SEC-022 and legacy-module boundaries; then a separately reviewed encrypted persistent-memory design with owner opt-in and deletion/recovery tests. Maintain disconnected Android executor and draft PR status.


## AGENT-006M — PaperClip prompt argument privacy (2026-11-09)

**Audit baseline:** `003e376f3fe7a5439d22dee3ff6a72d6e97676a4`; 394-entry complete repository tree; six open PRs; PR #1 draft, independent reviews absent. Local PROJECT-ADAPTER.md present, upstream SKILL.md absent and shared package unverified. All five preceding exact-head workflows at baseline passed (Phase 1 push/PR, CI-003 push/PR, QA-005 PR); this does not establish physical Pixel, spoken TalkBack, signed OTA or independent security acceptance.

**Bounded mitigation:** PaperClip no longer places user prompt content in the `llama-cli` process argument vector. Uses `-f /dev/stdin` and a subprocess input pipe; retains local-only model/executable selection, fixed argv, bounds and redacted failures. No prompt file is created. Synthetic local-child pipe regression added. Full details: [AGENT-006M-PAPERCLIP-ARGV-PRIVACY.md](AGENT-006M-PAPERCLIP-ARGV-PRIVACY.md).

**Local evidence:** isolated authorized server clone, 21/21 focused PaperClip tests, 917/917 full Python preflight tests, launcher source gate, Python compilation and diff whitespace check passed. Actual llama-cli/Termux, Android Gradle, emulator, physical Pixel and signed release not tested locally. Exact-head hosted CI to be checked after commit.

**Independent gate:** pending. Real llama-cli `-f /dev/stdin` compatibility and prompt echo must be checked on the intended runtime; stdin and child memory are not a complete confidentiality boundary. Keep Android executor disconnected. M1/M2/M6 in progress, M3 partial, M4 not started, M5 not accepted, M7/M8 blocked. No milestone complete. Next: independently review SEC-021/SEC-022 and PaperClip privacy, then design owner-authenticated encrypted persistence with deletion/recovery tests.


## AGENT-006N — PaperClip session teardown and model-filename privacy (2026-11-09)

Bounded M6 legacy PaperClip hardening: `main()` clears opted-in RAM session references in `finally` on exit, EOF, interrupt, and unexpected exception; `think()` no longer logs private GGUF filenames, and the startup banner no longer prints them. Seven new synthetic/offline regressions check teardown and preservation of existing plaintext legacy files. See [AGENT-006N evidence](AGENT-006N-PAPERCLIP-SESSION-PRIVACY.md). This is **not** secure memory erasure, encrypted persistence, production Android integration, independent review, or physical Pixel validation. Upstream shared `SKILL.md` remains unverified. **M1/M2/M6 in progress; M3 partial; M4 not started; M5 not accepted; M7/M8 blocked. No milestone complete.** Exact-head CI must be checked independently after push; independent security approval remains pending.


## AGENT-006Q — PaperClip event-log directory privacy (2026-11-09)

The AGENT-006P event logger now verifies that both its HOME and logs directories
are owned by the effective user and are not group/other-writable, and tightens
owner-owned 0755 directories to 0700 by descriptor. Three offline regression
tests cover the two refusal paths and private-mode tightening. Local VPS
verification: 42 focused PaperClip tests, 938 full Python tests, compileall and
git diff --check passed. Python 3.14 emitted pre-existing SQLite resource
warnings. Hosted exact-head CI and independent security review must be tracked
separately. No real executor, Android permission, physical Pixel, signing or
deployment was involved. Upstream SKILL.md remains absent/unverified.

M1/M2/M6 remain IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED,
M7 BLOCKED, M8 BLOCKED. No milestone is independently COMPLETE.

## SEC-023B1B2A dormant owner MemoryVault consent-intent binding (2026-11-09)

Separate scoped draft proposal off feat/phase1-agentic-phone, reusing
OwnerAuthorityConfirmationState for one-shot, 30-second monotonic owner
intent binding. Canonical digest binds owner profile, signing identity,
retention, future key alias and fresh caller-supplied nonce. Fail-closed
preflights and cancellation/replay/rollback/concurrency regressions are
synthetic only. A successful result is AWAITING_CRYPTOOBJECT_PROOF, not
authorization. No real credential prompt, CryptoObject, Keystore operation,
MemoryVault activation, persistence, IPC or physical Pixel interaction.
See docs/SEC-023B1B2A-CONSENT-INTENT.md. SEC-023B1B1 PR #18 and earlier
MemoryVault PRs remain unmerged, with independent review pending.
Upstream shared SKILL.md absent/unverified. No M1–M8 milestone complete.
