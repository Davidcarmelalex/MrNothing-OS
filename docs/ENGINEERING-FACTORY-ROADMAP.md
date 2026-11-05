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
