# Mr Nothing OS — Security Threat Model v1

**Status:** Draft for independent security review; not a security certification.  
**Repository:** Davidcarmelalex/MrNothing-OS  
**Authorized branch:** feat/phase1-agentic-phone  
**Evidence baseline:** 2026-11-08, source head 680d5cbd52630e685fb1ada69126a6555b1685f4  
**Target:** Google Pixel 9 Pro (codename caiman); no physical-device validation is claimed.

## 1. Purpose, scope and system reality

This document consolidates the security assumptions and unresolved risks that must be reviewed before Mr Nothing OS connects an AI-generated plan to Android device effects.

The current deliverable is an experimental Kotlin Android HOME launcher plus separate Python/Termux orchestration and security prototypes. It is not currently a replacement Android operating-system image, custom kernel, verified Pixel firmware distribution, signed OTA system or production autonomous executor. The native Android application and legacy Termux runtime are separate build/runtime boundaries.

In scope:

- Kotlin launcher, owner-facing disclosure, HOME-role consent and stock-launcher recovery.
- HERMES planning/admission prototypes and the offline plan simulator.
- Owner/device enrollment, consent-signing, live transport binding, replay prevention and action reservations.
- Android permission probes, process-local platform-session leases and owner trust-store prototypes.
- CI, dependency verification, unsigned reproducible APKs, build provenance and QA evidence.
- Future AccessibilityService, MediaProjection, device-action, OTA and Pixel-specific integration boundaries.

Out of scope for this version:

- A compromised Android kernel, compromised bootloader, malicious OEM firmware or an attacker with persistent root. Such compromise defeats many application-level controls and requires a separate platform threat model.
- Carrier, SIM-provider and emergency-services infrastructure.
- Formal cryptographic certification, penetration-test assurance or legal/privacy certification.
- Any claim that a physical Pixel 9 Pro has been installed, flashed or tested.

## 2. Security objectives

1. **Owner authority:** only the device owner, through a fresh and explicit Android-controlled ceremony, can authorize sensitive actions.
2. **Separation of evidence:** model output, JSON fields, caller booleans and package names are never proof of identity, consent or Android permission.
3. **Least privilege:** no root prerequisite; no broad shell bridge; no AccessibilityService or screen-capture service without deliberate OS-level user enablement.
4. **Freshness and replay resistance:** one-use capabilities are bound to the exact action, canonical arguments, owner/device/session, expiry and current enrollment generation.
5. **Fail closed:** unavailable storage, platform state, trust, identity, cancellation or verifier dependencies deny admission.
6. **Revocability:** permission/session loss, owner cancellation, credential rotation or revocation prevents future dispatch.
7. **Privacy:** screen, audio, message and app data are minimized, visibly accessed, redacted and retained only under a separately approved policy.
8. **Recoverability:** the owner can return to the stock launcher; future firmware/OTA must have authenticated rollback and recovery.
9. **Supply-chain integrity:** source, dependencies, build provenance and release artifacts are traceable; unsigned debug/CI artifacts are never represented as installable production releases.

## 3. Assets and security properties

| Asset | Security property | Current classification |
|---|---|---|
| Owner identity and device enrollment | Authenticity, integrity, revocation | Prototype registry; no production provisioning |
| Owner signing keys and trust anchors | Confidentiality, integrity, non-exportability | Android Keystore prototypes; StrongBox not hardware-verified |
| Live transport/session identity | Authenticity, freshness, connection binding | Library adapter prototype; no production listener |
| Consent challenges, signatures and nonces | Integrity, freshness, one-use semantics | Protocol prototypes with durable host-side replay state |
| Action arguments and idempotency keys | Integrity, boundedness, non-substitution | Canonicalization and reservation primitives |
| Android permissions and platform leases | Current OS authority, revocability | Read-only probes/registry; providers not connected |
| Screen, audio, messages and app metadata | Confidentiality, minimization, retention | No production capture pipeline |
| Trust records and enrollment database | Integrity, rollback resistance, availability | Encrypted/transactional prototypes; hardware and cross-store limits remain |
| Audit and CI provenance | Accountability, integrity | CI artifacts and test records; no production audit service |
| APK, firmware and OTA packages | Authenticity, integrity, rollback safety | Unsigned reproducible APK only; no signed OTA |

## 4. System components and trust boundaries

| Boundary | Data crossing it | Required rule | Current status |
|---|---|---|---|
| B1: model/planner to HERMES policy | Proposed action, target and arguments | Treat all model output as untrusted; strict typed schema and bounded plan | Offline sandbox/admission prototypes; no device execution |
| B2: HERMES host to transport adapter | Command envelope and authenticated peer | Identity must be derived from the live transport and trusted enrollment, not a payload Boolean | mTLS adapter prototype; no production listener |
| B3: transport to owner-consent verifier | Challenge, signature, exact action/argument digest | Verify one-use capability, freshness, peer/session binding and current enrollment | Protocol primitives implemented; production caller absent |
| B4: consent verifier to reservation store | Verified action and idempotency identity | Durable reservation before any future side effect; duplicates are not dispatchable | Separate reservation primitive; no dispatch consumer |
| B5: Android app to Android OS | HOME role, credential prompt, permissions, accessibility/projection state | Query OS immediately before use; user must enable sensitive services in system UI | Launcher and probes exist; no AccessibilityService or MediaProjection service declared |
| B6: permission/session probe to action router | Current platform state | A positive probe is only a prerequisite, never owner consent or authentication | Pure-Kotlin gate/registry; router remains fail-closed |
| B7: router to device executor | Approved typed action | Require all gates again at the execution boundary; no arbitrary shell or model-selected intent | No integrated executor; all Android requests rejected |
| B8: source/dependency to CI artifact | Source, toolchain, dependencies and APK | Pin tools, verify dependencies, bind provenance and compare independent builds | CI checks pass; unsigned artifacts are not for release |
| B9: release/OTA to physical device | Signed package and rollback metadata | Protected signing keys, verified boot compatibility, recovery and rollback | Not implemented or hardware-tested |

## 5. Threat actors and assumptions

- **Untrusted model or prompt-injected content:** may propose harmful, malformed, out-of-scope or misleading actions.
- **Malicious application/content:** may attempt to influence UI automation, exploit intents or induce disclosure of sensitive screen data.
- **Network attacker:** may intercept, replay, redirect or terminate a future remote session.
- **Compromised HERMES host or local process:** may submit forged envelopes, reuse credentials or tamper with state.
- **Local attacker with device access:** may inspect app-private data, alter settings, exploit an unlocked device or attempt credential/UI deception.
- **Supply-chain attacker:** may compromise dependencies, build tools, GitHub Actions or release artifacts.
- **Physical attacker / compromised OS:** may bypass app-level controls through bootloader, root, recovery or hardware compromise.

Assumptions: Android's platform permission and credential UI are trusted for the application threat model; owner-controlled device settings remain authoritative. A rooted or compromised OS invalidates application-only guarantees. These assumptions require a separate Pixel/OEM/boot-chain review before hardware deployment.

## 6. Security invariants

- A Boolean such as authenticated=true, a model statement, a device ID or a JSON field never creates a trusted session.
- No action may execute unless live transport identity, current owner/device enrollment, exact one-use consent, action/argument digest, current Android prerequisites, policy and durable idempotency checks all pass.
- Revalidate revocation, expiry, permission and live-session state at the final execution boundary; planning-time checks are insufficient.
- If enrollment/replay/reservation state cannot be checked atomically enough for the action's risk, deny dispatch.
- Accessibility and MediaProjection must be enabled by the owner through Android's UI, visibly active, narrowly scoped and immediately revocable. Never toggle them silently.
- Cancellation before dispatch prevents the side effect. An unknown outcome after dispatch must not be retried blindly.
- No arbitrary shell strings, subprocess invocation, hidden UI automation, biometric/credential bypass or restricted-screen bypass may enter the native Android path.
- No CI debug or unsigned artifact is a production release. No production key or secret belongs in Git.
- No physical flash, bootloader unlock, OTA deployment or irreversible device operation is authorized by this engineering workflow.

## 7. STRIDE threat register

Risk ratings are preliminary engineering priorities, not measured likelihoods. Status labels distinguish implemented primitives from production integration.

| ID / STRIDE | Threat and impact | Existing control/evidence | Residual gap and required gate | Priority |
|---|---|---|---|---|
| TM-01 Spoofing | A model or caller claims to be the owner/device and injects an authenticated request. | SEC-017 enrollment records; SEC-019B binds verifier evidence to an exact live TLS socket; Android CommandRouter rejects requests without a verified transport session. | No production listener, certificate issuance, device provisioning or independent security review. Test spoofed peers, socket substitution and revoked credentials before integration. | Critical |
| TM-02 Tampering | Arguments or action identity are changed after consent, or malformed JSON is interpreted differently across Kotlin/Python. | Canonical argument encoding, domain-separated digest, strict field/type/size checks and cross-language fixtures. | No end-to-end production dispatcher. Require mutation/fuzz corpus and exact action/argument binding at final dispatch. | High |
| TM-03 Repudiation | A sensitive action cannot be reconstructed or attributed to an owner decision. | Reservation state and correlation primitives exist; raw arguments/results are intentionally not stored by the reservation primitive. | No production append-only operational audit pipeline, retention policy or independent log-integrity design. | High |
| TM-04 Information disclosure | Screen, audio, message, credential or app data is captured or retained beyond the owner's intent. | No production screen/audio capture service; no AccessibilityService or MediaProjection component is declared. | Data minimization, visible capture indicator, redaction, retention/deletion and export controls must be reviewed before any capture provider. | Critical |
| TM-05 Denial of service | Oversized requests, replay-ledger exhaustion, lock contention, slow callbacks or emulator/host resource pressure prevent service. | Bounded payloads/plans, timeouts, SQLite busy limits, capacity fail-closed behavior and emulator QA timeouts. | No production network rate limiting, backpressure, abuse monitoring or availability SLO. | Medium |
| TM-06 Elevation of privilege | A plan or stale permission observation is treated as authority to invoke Accessibility, projection, launch or another privileged action. | ActionPermissionGate separates OS prerequisites from consent; session registry is process-local; CommandRouter rejects all requests. | No real providers, final dispatch integration or service UX. Preserve owner-only Settings navigation and test disable/unbind/process-death races. | Critical |
| TM-07 Spoofing / replay | A captured signed capability is replayed, or a revoked credential remains accepted. | SEC-019A transactional enrollment/replay admission; bounded one-use nonce state; SEC-018 verifier-time revalidation; SEC-019B live socket binding. | Action reservation is a separate store; no executor exists. Before dispatch, prove atomic current-generation/revocation/session admission with reservation or a single admission lock/transaction. No distributed replay design. | Critical |
| TM-08 Tampering / EoP | Legacy Termux agent shell helpers are accidentally exposed through the native Android bridge, allowing shell injection or unrestricted commands. | Gradle graph/source audit documents separation; native Android source has no shell/process bridge; CommandRouter remains fail-closed. | Legacy HERMES/OpenClaw prototypes contain subprocess shell execution. They must remain unexposed and be replaced with typed reviewed APIs before any bridge. | Critical |
| TM-09 Tampering / rollback | Local trust records, generation markers or enrollment files are replaced, truncated or rolled back. | Encrypted Android trust-record prototype, marker-first AtomicFile flow, strict failure modes and synthetic failure-injection tests. | StrongBox and reboot persistence are not verified on Pixel 9 Pro. Marker aliases are not a hardware monotonic counter and do not survive uninstall/factory reset. | High |
| TM-10 Tampering / supply chain | Compromised dependency, mutable action reference, build tool or artifact enters a release. | Pinned GitHub Action SHAs, Gradle dependency verification, modified-artifact negative control, independent unsigned APK reproducibility and scoped SBOM. | No signed production artifact, protected release key, complete hosted-runner SBOM or release signing/verification ceremony. CI provenance explicitly reports release_ready=false. | High |
| TM-11 Elevation of privilege | UI automation targets a restricted surface, hidden control or another app without informed owner consent. | Launcher disclosure, explicit HOME-role prompt/cancel, stock-launcher recovery and structural hierarchy checks. | TalkBack spoken navigation is not tested; no production accessibility provider; restricted-surface policy and human accessibility review remain open. | High |
| TM-12 Denial of service / repudiation | Owner cancellation, stale callbacks or ambiguous outcomes cause repeated or untraceable side effects. | One-shot consent state, cancellation tests, durable reservation lifecycle and process-local lease generations. | No real executor/reconciliation protocol or production audit stream. Require exactly-once claim, cancellation race, unknown-outcome and restart tests before side effects. | High |
| TM-13 Tampering / availability | An unverified OTA or firmware update bricks the device or downgrades security state. | No firmware flash or OTA deployment is performed by CI; release gates explicitly block production. | Signed A/B update, verified boot/rollback analysis, recovery image, caiman vendor/boot chain matrix and physical rollback drill are not implemented. | Critical |

## 8. Data handling and retention requirements

| Data | Permitted handling before production | Required future control |
|---|---|---|
| Private signing keys | Android Keystore only; synthetic keys in tests | Hardware-backed provisioning, non-exportability proof and rotation/recovery review |
| Public keys, certificate fingerprints and trust records | Bounded, integrity-protected records | Owner-visible lifecycle, secure backup/restore policy and verified deletion |
| Challenges, nonces and idempotency keys | Short-lived capabilities; consumed replay markers fail closed | Defined retention/compaction with anti-rollback and atomicity review |
| Screen/audio/message content | No production capture currently | Per-session consent, visible indicator, redaction, local-only default and explicit retention/deletion |
| App/package metadata | Read only when required for a visible action | Minimize collection and avoid unnecessary telemetry |
| Logs and CI artifacts | Redact secrets; synthetic credentials only | Access control, retention, tamper evidence and artifact expiry |
| Test fixtures | Synthetic keys, dummy fields and disposable emulator PIN only | Never substitute test material for production authority or user credentials |

## 9. Verified implementation and test evidence at the baseline

Exact source head: 680d5cbd52630e685fb1ada69126a6555b1685f4.

- Phase 1 push run 42417459789 and PR run 42417463397 completed successfully. Each Python policy job ran 730 tests and reported OK. Android debug unit tests, debug APK assembly, repeat-build comparison, strict Gradle dependency verification, modified-dependency negative control and manifest security gate passed.
- CI-003 push run 42417459698 and PR run 42417463410 completed successfully. Independent runners produced byte-identical unsigned release-variant APKs: 7,862,996 bytes, 21 ZIP entries, SHA-256 1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b; normalized-entry SHA-256 fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140. The scoped build-environment inventory covers 1,260 components. Provenance states release_ready=false and does not claim a complete host-image SBOM.
- QA-005 PR run 42417463430 completed successfully on a disposable Android API 35 x86_64 emulator. JUnit reports 30 tests, 0 failures, 0 errors and 0 skipped. QA-005 through QA-010 passed; QA-013, QA-020B2 and QA-020B3 passed.
- QA-011 reports package_present=true but accessibility_enabled=false and talkback_service_enabled=false; spoken_navigation_verified=false. QA-012 reports structural_checks_passed=true, hierarchy_snapshots=2, but spoken_navigation_verified=false and acceptance_passed=false.
- QA-020B2 used fixed invalid dummy fields and verified Cancel cleared them without changing trust state. QA-020B3 verified the DUMP-protected cancellation harness and test-only credential path; no trust store, permission grant or executor was connected.
- The QA artifact reports no retained data_app_anr DropBox entry for this successful run. The instrumentation process completed normally; this does not prove absence of all possible ANRs on other devices.

These results validate the stated CI/emulator checks at the baseline commit only. They do not establish spoken TalkBack acceptance, physical Pixel compatibility, StrongBox hardware behavior, a signed release or production readiness.

## 10. Residual risks and required owners

| Risk | Owner | Required closure evidence |
|---|---|---|
| Independent security review of identity, consent, revocation and trust-store design | Security + independent supervisor | Written review against this threat model; no unresolved critical findings |
| Atomic revocation/session/action-reservation boundary | Security + AI/agents | Transaction/lock design, race tests, restart tests and adversarial review before executor |
| Typed executor and Android dispatch boundary | Android + AI/agents | No shell, final OS permission recheck, exact capability consumption, cancellation and idempotency tests |
| Accessibility provider and spoken navigation | UX/accessibility + Android | Owner-enabled TalkBack test, spoken labels/focus/actions, coexistence, recovery and revocation evidence |
| Screen-capture provider and privacy lifecycle | Android + security | Fresh OS consent, visible foreground indicator, stop callback, process-death handling and data deletion tests |
| Pixel 9 Pro hardware and boot chain | Hardware/release | Authorized physical device, caiman build/ABI/vendor matrix, StrongBox, reboot, SIM/Wi-Fi/Bluetooth, thermal and recovery evidence |
| Signed OTA/release | Hardware/release + supervisor | Protected signing, reproducible signed artifacts, SBOM, signature verification, rollback and recovery drill |
| Legacy shell-based Termux prototypes | AI/agents + security | Demonstrated isolation or replacement with typed APIs; no native bridge to shell helpers |
| Operational audit and rate limiting | Security + CI/QA | Redacted append-only audit, abuse limits, retention/deletion and monitoring tests |

## 11. Milestone gates

| Milestone | Current evidence-based status | Remaining security gate |
|---|---|---|
| M1 Foundation | IN PROGRESS | Independent review and approval of this threat model, threat-to-test traceability and release provenance |
| M2 OS interface | IN PROGRESS | Deliberately consented TalkBack spoken-navigation acceptance and independent accessibility review |
| M3 Agentic intelligence | PARTIAL | Authenticated deterministic executor, atomic final admission, cancellation, idempotency and 20 sandbox scenarios |
| M4 Permission-controlled integrations | NOT STARTED | Owner-enabled provider UX, five supported workflows, final permission rechecks and revocation tests |
| M5 Pixel 9 Pro compatibility | NOT ACCEPTED | caiman build/ABI/vendor and boot-chain evidence |
| M6 Security/privacy | IN PROGRESS | Independent threat review, hardware-backed key validation, retention and kill-switch tests |
| M7 Physical hardware validation | BLOCKED | Authorized physical Pixel 9 Pro and complete hardware/recovery evidence |
| M8 Production readiness | BLOCKED | Signed reproducible release, SBOM, 100 scripted scenarios, OTA rollback and independent signoff |

No milestone is COMPLETE. No completion percentage is inferred from passing CI.

## 12. M1 acceptance criteria and review checklist

M1 may advance only when an independent reviewer:

- Confirms each asset, actor, trust boundary and high/critical threat is complete and correctly scoped.
- Challenges the assumptions around model output, live TLS identity, consent, revocation, Android permission and legacy shell separation.
- Confirms every high/critical threat maps to an owner, a mitigation and a repeatable test or explicitly accepted residual risk.
- Reviews the cross-store revocation/reservation race before any dispatch implementation.
- Confirms no production endpoint, service, executor, signing key or device flash is accidentally enabled.
- Records reviewer identity, date, commit SHA, findings and disposition in a separate review record.

The document author cannot self-approve. Until that independent review exists, M1 remains IN PROGRESS and this threat model remains DRAFT.

## 13. Change triggers

Re-review this model before introducing any of the following: a network listener; production mTLS/client-certificate issuance; Android AccessibilityService; MediaProjection; SMS/call/contacts/notification access; an action dispatcher or executor; a new permission or exported component; cloud/third-party connector; persistent session restoration; signed OTA; bootloader/firmware change; or a change to key storage, trust anchors, replay retention or action-reservation transactions.
