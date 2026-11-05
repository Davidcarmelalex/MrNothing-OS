# MrNothing OS — verified engineering milestones

**Pre-SEC-017 audit baseline:** 2026-11-05, branch feat/phase1-agentic-phone at c696b1276fd994897876af845dd6c7ad6c052bad. Exact-head push checks (run 41981940394), PR checks (run 41981946233) and QA-005 disposable x86_64 emulator workflow (run 41981946192) all completed successfully. The Python-policy job ran 317 tests; Android Gradle/JUnit and repeat debug-APK byte comparison passed. QA-005 through QA-010 and QA-013 passed; QA-011/012 are read-only preflights, not TalkBack speech acceptance. No physical Pixel 9 Pro, production enrollment authority, verifier-time revocation, connected command executor, custom firmware, OTA or release signing has been demonstrated.

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
