# MrNothing OS — verified engineering milestones

**SEC-017 audit baseline:** 2026-11-05, branch feat/phase1-agentic-phone at f5607aa9ddf52b3c9bacf8ac959fe786db1b4835. Exact-head push checks (run 41989793035), PR checks (run 41989800493) and QA-005 disposable x86_64 emulator workflow (run 41989800863) all completed successfully. Android Gradle/JUnit, Python policy/static checks and repeat debug-APK comparison passed. QA-005 through QA-010 and QA-013 passed; QA-011/012 remain read-only preflights, not TalkBack speech acceptance. SEC-017 signed durable paired enrollment is implemented with synthetic software keys. Production authority-key provisioning, verifier-time revocation, connected command execution, custom firmware, OTA and release signing have not been demonstrated.

| Gate | Owner(s) | Objective acceptance evidence | Baseline |
| --- | --- | --- | --- |
| **M1 Foundation** | CI/QA + Android | reproducible pinned build, test inventory, threat model, CI green, reviewed adapter, supervisor signoff | IN PROGRESS |
| **M2 OS interface** | Android + UX | default HOME role, app library, accessibility checks with TalkBack/large text, user-controlled stock-launcher recovery, emulator E2E | IN PROGRESS (QA-005 emulator workflow passed; TalkBack speech acceptance and hardware remain unverified) |
| **M3 Agentic intelligence** | AI/agents | authenticated deterministic plan->tool->result state machine, cancellation, injection and timeout tests, 20 sandbox scenarios | IN PROGRESS (isolated plan/consent primitives; no integrated executor) |
| **M4 Device integrations** | Android + security | opt-in permission UX, 5 supported app workflows, revocation tests, no restricted-screen bypass | NOT STARTED |
| **M5 Pixel 9 Pro compatibility** | Hardware/release | caiman build/ABI checks, vendor/boot chain analysis, modem limitations documented, recovery plan | NOT STARTED |
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
