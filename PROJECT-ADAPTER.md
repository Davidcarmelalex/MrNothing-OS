# MrNothing OS — Universal Engineering Factory project adapter

**Scope:** `Davidcarmelalex/MrNothing-OS`, exclusively `feat/phase1-agentic-phone`. Target device: **Google Pixel 9 Pro (`caiman`)**.

**Provenance:** At the 2026-11-02 audit, no `SKILL.md` or `PROJECT-ADAPTER.md` existed in the audited repository tree. No authorized copy of the reusable upstream Universal Autonomous Engineering Factory package was found in the supplied files. **This adapter is a local, project-specific implementation of the user's factory contract, not a claim that the upstream shared skill was installed or verified.** Do not silently overwrite it if the upstream package later arrives; review differences first.

## Mission and architecture
Build an accessible, privacy-preserving, agent-first Android experience that can replace the stock launcher with explicit user choice. Preserve compatibility with ordinary Android apps. Investigate a Pixel-specific AOSP distribution separately, only after device and firmware safety gates. Root is not a prerequisite for basic functionality and must never be silently obtained.

Components: Kotlin HOME launcher and device diagnostics; consented Android system integrations; Python HERMES policy/orchestration; authenticated, device-bound command channel; audited tool registry; voice interface; optional AOSP/device build; signed OTA/recovery. Existing Termux modules remain legacy prototypes, not proof of integrated functionality.

## Specialist ownership and path boundaries
| Role | Owns | Must verify |
| --- | --- | --- |
| Android engineer | `android/**` | compile, launcher selection/recovery, lifecycle and permissions |
| AI/agent engineer | `agents/**`, `core/hermes_gateway.py`, agent orchestration | deterministic plans, tool limits, cancellation, injection resistance |
| Security engineer | `core/*security*`, `core/*policy*`, threat model | identity binding, consent, replay prevention, fail-closed paths |
| UX/accessibility engineer | launcher UI and UX docs | TalkBack, contrast, large text, focus, reduced motion |
| CI/QA engineer | `.github/workflows/**`, `tests/**`, scripts | repeatable checks, artifact provenance, no unsupported claims |
| Hardware/release engineer | device, OTA, installer docs and future firmware | Pixel-specific hardware matrix, signed images, rollback |
| **Independent supervisor/verifier** | evidence review across all areas, no self-approval | inspect diff, rerun tests, challenge security assumptions, record gate decision |

Roles are **responsibilities**, not a claim that separate agents or humans have been launched. When separate independent reviewers are unavailable, mark the independent gate **PENDING** rather than self-certifying.

## Workflow per engineering run
1. Read latest branch SHA, open PRs, CI, tree, architecture, adapter, tests and prior evidence. Check for concurrent changes.
2. Select the highest-priority **unblocked and bounded** task with a measurable acceptance test.
3. Work only on the existing feature branch or an explicitly scoped branch; do not merge `main`.
4. Implement minimal compatible changes; never duplicate code or overwrite unrelated changes.
5. Run targeted tests, full available tests and static/security checks; state which environments were **not** tested.
6. Request independent verification, or explicitly record the absence of it. Keep PR draft until all required gates pass.
7. Record commit SHA, tests, CI, blockers and next task in the run report.

## Safety and release policy
No unauthorized root escalation, credential extraction, covert recording, unrestricted shell tools, CAPTCHA/biometric bypass, production deployment, device flashing, bootloader unlocking or irreversible changes. All sensitive actions require explicit informed user approval; emergency stop and recovery are mandatory. Android accessibility permissions and screen capture must be user-enabled, visible and revocable. Physical telephony audio must be validated on a real Pixel; root or default-dialer status does not prove audio routing. Sign release artifacts using protected keys; never commit keys or secrets. Supply SBOM and reproducible-build evidence before release.

**Milestone gates:** See [docs/ENGINEERING-FACTORY-ROADMAP.md](docs/ENGINEERING-FACTORY-ROADMAP.md). A milestone is COMPLETE only when its listed evidence exists and the independent supervisor has approved it.


## Audit update — 2026-11-05

The recursive tree of feat/phase1-agentic-phone contains this local PROJECT-ADAPTER.md and no SKILL.md. An authorized Library title-only search for SKILL.md returned no result, and no upstream shared package was supplied or verified. The upstream package remains unverified; this local adapter must not be represented as an installed copy.

SEC-019B extends the consent boundary with exact live SSLSocket-object binding, adapter-retained issued challenges, monotonic session/challenge expiry and a three-argument verifier API. The executor remains disconnected. Independent security approval remains pending.


SEC-020A adds a pure-JVM offline authority trust policy for first-install, signed rotation and explicit recovery. It returns a validated proposal only; it does not persist trust, mutate Android Keystore, display a ceremony UI or connect enrollment/execution. SEC-020B remains required for the StrongBox-backed generation watermark, encrypted active-anchor persistence and owner-visible credential-confirmed ceremony.

## Audit update — 2026-11-05, SEC-020B1

The current audited feature-branch head before this run was `487b341a11a9ffd1559882d7f269380311f79a35`. CI-005 strict Gradle dependency verification is already implemented and recorded as exact-head passing; it was not duplicated. SEC-020A is present as a pure-JVM trust-transition policy. This run adds SEC-020B1's bounded StrongBox-required storage transaction backend, marker-first commit ordering, encrypted active-record persistence and JVM failure-injection tests. The store is not connected to the owner enrollment UI, network enrollment, permissions or executor. Upstream shared `SKILL.md` remains unverified; this local adapter is not an installed upstream package.


## Verification update — 2026-11-05, SEC-020B1 exact-head acceptance

The SEC-020B1 implementation head `e530187404a07425a2e8dc066e024f4b8d982daf` passed both Phase 1 push/PR workflows, both CI-003 independent-runner push/PR workflows, and QA-005 emulator PR workflow. Run IDs: Phase 1 `42028301394` / `42028312778`; CI-003 `42028301428` / `42028312691`; QA-005 `42028312811`. The Phase 1 Python suite reported 380 passing tests; Gradle `:app:testDebugUnitTest`, `:app:assembleDebug`, repeat-build comparison, strict dependency verification and negative control passed. CI-003 verified byte-identical unsigned APKs on independent runners. QA-005 passed launcher/recovery, 200% font, HOME consent/cancel, stock-launcher restore, keyboard, structural accessibility and insecure-enrollment denial. QA-011 explicitly reported `blocked_service_disabled`; QA-012 was structural only, not spoken TalkBack acceptance. Emulator evidence is artifact `13415725749`. No physical Pixel 9 Pro test or independent security review occurred. Upstream shared `SKILL.md` remains unverified and is not claimed as installed.


## Audit update — 2026-11-05, SEC-020B2 owner-visible trust ceremony

The exact audited branch head before this run was 929e932a16841bb14c628c2e6aaab2ce3472b7f8. The recursive tree contained 222 entries, PROJECT-ADAPTER.md and no SKILL.md. Open PRs #1, #3, #4, #5, #6 and #7 were inspected; PR #1 targets main and the other five target the authorized feature branch. No upstream shared factory package was supplied or verified. This adapter remains project-specific.

SEC-020B2 adds a non-exported offline authority import Activity, strict canonical Base64/Ed25519 input parsing, exact out-of-band fingerprint comparison, an explicit owner attestation checkbox, a one-shot 30-second input/store-state-bound confirmation, a fresh Android system-credential prompt and a post-prompt trust-store reinspection before SEC-020A proposal creation and SEC-020B1 commit. It adds no Android permission, network listener, enrollment integration or executor connection. The UI attestation cannot prove the independent fingerprint source; StrongBox and credential behavior remain hardware/runtime gates. Exact-head CI and independent review are pending at submission.

## Audit and engineering update — 2026-11-05, QA-020B2

The recursive tree at eb6647e77a4a63f2472dbf0571d283d7a0764d07 contains 229 entries, PROJECT-ADAPTER.md, the engineering roadmap and no repository SKILL.md. The upstream shared factory package remains unverified and is not claimed as installed. The authorized branch was unchanged at the start of this run. Open PRs #1, #3, #4, #5, #6 and #7 were audited; PR #1 remains the phase-1 umbrella draft. PRs #3/#4 already use QA-014/QA-014P for certificate-chain regression work, so the owner-authority Activity runtime gate is deliberately named QA-020B2 to avoid task-ID collision.

The current branch already contains OwnerAuthorityTrustActivity, its launcher entry, parser/state JVM tests and source-security gates. The missing evidence was real emulator navigation and interaction with that Activity; the existing QA-005 workflow did not open it. This run adds an emulator-only QA-020B2 smoke test and strict hierarchy helper. It opens the Activity through MainActivity, verifies the five labeled fields and trust state, checks invalid/empty fingerprint preview refusal, checks the insecure-emulator credential preflight (or cancels an unexpected system credential UI without entering a credential), verifies Cancel clears fields without changing trust state, and returns to the launcher.

No trust material or credentials are entered. No permission is granted, no authority is committed, no agent executor is connected, and no physical device is targeted. Exact-head CI and emulator evidence are pending. M1/M2/M6 remain IN PROGRESS; M3 remains PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED pending Pixel 9 Pro access; M8 BLOCKED. No milestone is complete. Independent security review remains PENDING.


## QA-020B2 runtime correction — scrollable status label

The first emulator attempt reached OwnerAuthorityTrustActivity and captured the actual hierarchy. It showed that the initial status TextView is below the ScrollView viewport and is therefore absent from the initial UIAutomator dump, while the title, trust-state label, five field labels and five EditText nodes are present. The original helper incorrectly required the below-fold status text during initial-screen validation. The check is now limited to visible structural fields and trust state; action-result status text remains asserted after scrolling to the relevant controls. No Android application code or trust behavior changed. A new exact-head emulator rerun is required.


## Audit and correction — 2026-11-05, QA-020B2 populated-field cancellation

The current authorized branch head at run start was 2600e33abb42bdb6ee6361056539c4e6af0f00ca; its recursive tree contained 233 entries. The local PROJECT-ADAPTER.md and engineering roadmap are present; no repository SKILL.md exists. The upstream shared factory package remains unverified and is not claimed as installed. Open PRs #1, #3, #4, #5, #6 and #7 were audited. PR #1 remains a draft against main; no review submissions or inline review threads were present. Other workers' QA-014 and SEC-016 branches were left untouched.

The exact-head Phase 1 push/PR and CI-003 push/PR workflows passed at 2600e33. QA-005 PR run 42047955324 failed only in QA-020B2 after all prior launcher/accessibility/enrollment steps passed. Artifact 13425996691 established that UIAutomator reports an empty EditText's hint in its text attribute and that the hierarchy was still scrolled to the bottom, exposing only three fields. The Android Activity source calls clear() on all five EditText values in cancelPending(true); the observed failure was a harness assertion error, not evidence of an application defect.

The QA-020B2 harness is strengthened to enter five fixed invalid dummy strings (no valid key, fingerprint, signature or credential), verify them, invoke Cancel, scroll to the top, and require all five EditText nodes to return to their exact empty-field hints with the trust-state label unchanged. No preview or confirmation follows dummy entry. No app code, permissions, role, trust store, enrollment, executor or physical device is changed. Independent security review remains pending. Upstream shared SKILL.md remains unverified.


### QA-020B2 snapshot split

The corrected smoke harness captures the Cancel result immediately while the lower status TextView is visible, then scrolls to the top for the five empty-field hints and trust-state comparison. These assertions use separate hierarchy snapshots because the status and all five fields do not share a single scroll viewport.


## Exact-head QA-020B2 acceptance — 2026-11-05

The final QA-020B2 correction at source/test head 9eb814c3a2176f9be552372c5d6f078774edb7dd passed the complete exact-head validation set:

- Phase 1 push run 42051143160 and PR run 42051155411: PASS. Both reported 416 Python tests passed; Android manifest security gate passed; Gradle :app:testDebugUnitTest and :app:assembleDebug passed; repeat debug APK was byte-identical within each runner; strict dependency verification and the modified-artifact negative control passed.
- CI-003 push run 42051143237 and PR run 42051155321: PASS. Independent runners produced byte-identical unsigned APKs (2,196,905 bytes, 13 entries; SHA-256 c58ac03288ff210c03036645ee26e5c70925972b4b7356567c3021b6e6031d1e), identical normalized contents (b11c9f6ab88743d690dfa556f4f086126bbd8a1165aaa02f29c5c81cf718b396), runtime inventory (a8a1b16dd1cefb90d14426c477e924a3710c7a160def52a2ece3a6d55c266e44) and SPDX runtime SBOM (c4d577f316439ed5445e5fd553a01c4eea0c54c135420b416792bbaad07a1b3d). Both verifiers reported reproducible=true and release_ready=false.
- QA-005 disposable x86_64 emulator PR run 42051155383: PASS. QA-005, QA-006 through QA-010, QA-013 and QA-020B2 passed. QA-011 reported blocked_service_disabled (not TalkBack acceptance); QA-012 passed structural semantics only (not spoken TalkBack). QA-020B2 artifact 13426024605 contains the five synthetic invalid field values, separate Cancel-status snapshot and post-cancel empty-hint snapshot. The log records: all five fixed invalid dummy fields were cleared; trust state unchanged; launcher restored.

The original QA-020B2 failure at run 42047955324 was a hierarchy-harness defect, not an application defect: empty EditText nodes expose hints as their UIAutomator text and the lower viewport contained only three fields. The corrected test proved all five fields were populated with fixed invalid test strings, then cleared by Cancel. It did not preview or confirm those values, enter credentials, mutate the trust store, grant permissions or invoke an executor.

This evidence is disposable-emulator-only. It does not establish Pixel 9 Pro StrongBox/Keyguard behavior, physical crash recovery, spoken TalkBack, independent security approval or production readiness. No milestone is complete; M1/M2/M6 remain IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7 BLOCKED and M8 BLOCKED. The upstream shared SKILL.md remains unverified and is not claimed as installed.


## Audit and implementation update — 2026-11-05, SEC-020B3

The branch was audited at `ef0995691025010ee531b01958f455d97047edfa`; the recursive tree contained 233
entries, the local project adapter and roadmap, and no repository `SKILL.md`.
The upstream shared factory package remains unverified and is not claimed as
installed. Open PRs #1 and #3–#7 were inspected; only the authorized
`feat/phase1-agentic-phone` branch is modified.

SEC-020B3 replaces the deprecated Keyguard credential Intent with the Android
platform BiometricPrompt API configured for `DEVICE_CREDENTIAL` only. API 30+
is required; API 29 fails closed. The callback must report the device-credential
authentication type. A retained CancellationSignal is canceled only after
the one-shot binding is revoked, so late callbacks cannot commit. No new
dependency or Android permission is introduced. Exact-head CI and emulator
verification are pending; independent security review and Pixel 9 Pro hardware
validation remain outstanding.


## Audit and QA implementation update — 2026-11-05, QA-020B3

The exact audited branch head was 0c29a35ac39f9e7f92aa9fc009a1c33c2e9784e7; the complete recursive tree contained 236 entries. PROJECT-ADAPTER.md and docs/ENGINEERING-FACTORY-ROADMAP.md are present; no repository SKILL.md exists. The upstream shared factory package remains unverified and is not claimed as installed. Open PRs #1 and #3–#7 were inspected; only feat/phase1-agentic-phone is modified.

The exact-head SEC-020B3 runs were green: Phase 1 push/PR 42057750836 / 42057761743, CI-003 push/PR 42057750392 / 42057761731, and QA-005 PR 42057762205. QA-005 passed QA-020B2 only; it did not exercise a successful credential prompt. PR #1 remains draft with no independent review submissions or inline review threads. Branch-protection read returned HTTP 403; repository rulesets returned an empty list, so required-review enforcement is not established.

QA-020B3 adds a debug-only prompt probe sharing the production OwnerCredentialPromptFactory. It uses a disposable API 35 x86_64 AVD and a fixed synthetic PIN set/cleared through ordinary adb shell UID 2000. It verifies visible system PIN UI, cancellation denial and a successful platform-reported DEVICE_CREDENTIAL callback. The probe has no trust-store, permission-grant or executor path and is excluded from the main/release manifest. This is prompt-runtime evidence only, not StrongBox trust commit or Pixel hardware evidence. Exact-head CI is pending at submission.


## Audit and QA correction — 2026-11-05, QA-020B3 cancellation surface

At this run's start, the authorized branch was exactly d33b17ca5a35329889ed82f9dfde7bda402dd4b4; its recursive Git tree contained 248 entries and was not truncated. The tree contains PROJECT-ADAPTER.md and docs/ENGINEERING-FACTORY-ROADMAP.md, and no SKILL.md. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. Open PRs #1 and #3–#7 were inspected. PR #1 remains a draft against main, with zero submitted reviews and zero inline review threads. The authorized feature branch is unprotected; repository rulesets returned no entries. No main merge or unrelated worker-branch write was performed.

Exact-head Phase 1 push/PR runs 42067981150 and 42067990657 passed; CI-003 push/PR runs 42067981156 and 42067990710 passed. The Phase 1 PR Python-policy job passed 428 tests, the Android manifest gate, Gradle unit tests, debug assembly, repeat-build comparison, strict dependency verification and its modified-artifact negative control. CI-003's two independent runners and verifier passed unsigned release build, negative control, SPDX runtime SBOM and artifact/toolchain equivalence. QA-005 run 42067990751 passed emulator setup, launcher/recovery, QA-006 through QA-013 and QA-020B2, then failed only in QA-020B3's cancellation step.

Artifact 13434834475 proves the API 35 x86_64 emulator displayed the SystemUI device-credential prompt. KEYCODE_BACK did not dismiss it; all 25 subsequent hierarchy snapshots still showed the SystemUI PIN panel, so the app status TextView was not in the hierarchy. The cleanup log confirms the disposable test PIN was cleared. This is a harness cancellation-method failure, not evidence of an app authentication defect.

The correction derives a tap point from SystemUI's explicit clickable Tap to cancel authentication background node and the credential-panel bounds. It fails closed if the node is missing, ambiguous, hidden, non-clickable or lacks a safe outside-panel margin. The exact captured failure hierarchy yields 540 31. Three parser regression tests were added. Local verification: 14 focused Python tests passed; bash -n and compileall passed; the actual run artifact parsed to 540 31. Exact-head CI and emulator rerun are pending. No physical device, root, trust-store commit, permission grant, executor or production signing was used. M1/M2/M6 remain IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Independent security review remains PENDING.


## Audit and correction — 2026-11-06, QA-020B3 cancellation harness

The latest authorized branch head at audit was `c92fad5dd8fea0fd5029cd01d14a36fd59924d6d`; the complete recursive tree contained 249 entries and was not truncated. `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` are present; repository `SKILL.md` is absent. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. Open PRs #1 and #3–#7 were audited; only the authorized feature branch is modified.

Exact-head Phase 1 push/PR and CI-003 push/PR workflows passed at c92fad5. QA-005 run 42084901826 passed all earlier launcher, recovery, accessibility-structure, insecure-enrollment and QA-020B2 steps, then failed at QA-020B3 cancellation. Artifact 13442612292 proves the bottom-margin tap at (540,1494) entered one character into the SystemUI credential field while leaving the prompt open. The test PIN cleanup succeeded; the fixed PIN was not submitted. The prior safe-bottom-tap assumption is superseded.

The current correction derives a tap point from the actual SystemUI `lockPassword` EditText side gutter (captured fixture: 133,1033), rejects overlapping clickable controls, and asserts immediately after the gesture that the prompt is dismissed or the field remains empty. Exact-head emulator rerun is pending. No physical Pixel, StrongBox, production signing, trust-store commit, permission grant or executor activity is claimed. M1/M2/M6 remain IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED. No milestone is complete; independent security review remains pending.


## Audit and correction — 2026-11-06, QA-020B3 cancellation harness

At run start the authorized branch was 8b875fd23d86df525f17d942b74d684682064de2; the complete recursive tree contained 249 entries. PROJECT-ADAPTER.md and the roadmap are present; repository SKILL.md is absent. The authorized Library search did not locate an upstream Universal Autonomous Engineering Factory package. The upstream package remains unverified and is not claimed as installed.

Open PRs #1 and #3–#7 were audited. PR #1 remains a draft to main with zero submitted reviews and zero inline threads; other PRs were not modified. Main remains f3c9a701d2a337de8ef393ac14df044a79843d60. The authorized branch is unprotected and no rulesets were returned, so required-review enforcement is not established.

Phase 1 push/PR runs 42095099243 and 42095108564 passed; CI-003 push/PR runs 42095099195 and 42095108570 passed. QA-005 run 42095108551 failed only at QA-020B3 cancellation. The SystemUI prompt appeared; the side-gutter tap (133,1033) did not dismiss it; the credential field remained empty and the test PIN cleanup succeeded.

The coordinate-based cancellation gesture is removed. QA-020B3 now uses a debug-only android.permission.DUMP-protected receiver to cancel the probe's active CancellationSignal. The script must observe the prompt-error callback and prompt disappearance, then verify a second prompt returns DEVICE_CREDENTIAL_ACCEPTED for the synthetic emulator PIN. This tests cancellation-signal behavior, not the user's SystemUI outside-tap gesture. Receiver/control are debug-only and have no trust-store, permission-grant, network, command-router or executor path. Exact-head CI/emulator reruns remain the acceptance gate.


## Audit and implementation update — 2026-11-06, QA-020B3 exact-head acceptance and SEC-020B4

The complete recursive tree at the start of this run contained 251 entries at 60a7a8162c71a04fb6cc90af7afc68ee33f3f46b; it was not truncated. The branch head, latest 12 commits, all six open PRs, exact-head Actions runs, architecture and existing adapter/roadmap were audited. PROJECT-ADAPTER.md and docs/ENGINEERING-FACTORY-ROADMAP.md exist; repository SKILL.md is absent. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed.

QA-005 exact-head PR run [42099903280](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42099903280) completed successfully. Its job log explicitly records QA-020B3 PASS: the system credential prompt appeared; the DUMP-protected debug cancellation signal produced the prompt-error callback; the disposable test PIN returned the platform-reported DEVICE_CREDENTIAL result; cleanup ran; no trust store, permission grant or executor was connected. QA-011 reported blocked_service_disabled; QA-012 was structural semantics only, not spoken TalkBack acceptance. Phase 1 push/PR [42099893816](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42099893816) / [42099903266](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42099903266) passed with 433 Python tests each and Android Gradle/manifest/dependency gates. CI-003 push/PR [42099894002](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42099894002) / [42099903502](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42099903502) passed; independent runners and verifier reported reproducible unsigned APKs and release_ready=false.

SEC-020B4 moves owner trust-store inspection and commit off the main thread through a process-wide single-thread executor. A lifecycle operation gate rejects overlapping work and invalidates queued operations on cancellation/destruction. The worker reinspects the trust-store snapshot, recomputes the binding and Ready decision, checks device safety, then claims the commit boundary immediately before store.commit. Cancellation/destruction before that boundary suppresses commit. Once the authorized atomic transaction is claimed, it is allowed to finish; UI delivery is suppressed after Activity destruction. This is an explicit non-cancelable transaction boundary, not a claim that an already-started AtomicFile/Keystore operation can be rolled back.

PR #1 remains open and draft with zero review submissions and zero inline review threads. Main remains unchanged; the feature branch is unprotected and no repository rulesets were returned. No other worker branch was modified. Physical Pixel 9 Pro, StrongBox, spoken TalkBack and independent security acceptance remain unverified.


## Audit and implementation update — 2026-11-06, SEC-020B4A

The current audit baseline was `e03abc313ce322d02767a1c3edba181a4503f5d0` on the authorized branch. The complete recursive tree contained 254 entries, was not truncated, and contained no `SKILL.md`; this local adapter and the roadmap are present. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed.

The audit inspected the latest 12 feature-branch commits, all six open PRs (#1 and #3–#7), PR #1's exact head/base/draft state, reviews and inline threads, Phase 1/CI-003/QA-005 runs, Android architecture and existing tests. PR #1 targets unchanged `main` at `f3c9a701d2a337de8ef393ac14df044a79843d60`, remains draft and has zero submitted reviews or inline review threads. The feature branch is unprotected; no repository rulesets were returned. No other PR branch is modified.

At the audited head, Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR all completed successfully. QA-005 covered launcher/recovery, QA-006–QA-013, SEC-020B2 and QA-020B3. It did not execute SEC-020B4 trust-store inspection/commit on Android. QA-011 is an availability preflight only; QA-012 checks structural semantics only, not spoken TalkBack.

SEC-020B4A adds JVM tests for single-thread coordinator serialization, the cancellation-versus-commit-claim linearization race, and stale-token isolation. These are not Android Keystore, StrongBox, Activity instrumentation, Pixel 9 Pro or physical recovery tests. The executor remains disconnected from permission grants and agent execution. Exact-head Actions results for this new test commit must be checked before acceptance.


## Audit and implementation update — 2026-11-06, SEC-020B4B

The authorized branch was audited at `9fb8cd96fb5f1702efde0a5822a9c527e5a62189`; its complete recursive tree contained 255 entries. The latest 12 commits, six open PRs, PR #1 metadata/reviews/threads, Phase 1/CI-003/QA-005 runs, Android architecture, existing security tests and this adapter/roadmap were reviewed. The repository contains this adapter and the roadmap but no `SKILL.md`. The authorized Library search recorded above found no upstream shared package; that package remains unverified and is not claimed as installed.

All five exact-head Actions workflows passed: Phase 1 push/PR, CI-003 push/PR and QA-005 PR. Phase 1 ran Android unit/build/dependency checks and the Python policy suite; CI-003 independently reproduced the unsigned release build; QA-005 passed on a disposable API 35 x86_64 emulator through QA-020B2 and QA-020B3. The emulator did not exercise SEC-020B4 worker/Activity lifecycle. QA-011 and QA-012 are not spoken TalkBack acceptance.

SEC-020B4B adds static regression gates to the existing owner-authority source test: all trust I/O components must remain disconnected from agent/command execution, permission grants, screen capture/accessibility, device administration, telephony, camera/microphone, network and process-launch capabilities. The debug credential probe must remain absent from the main manifest and DUMP-protected in the debug manifest. These are source/manifest assertions, not runtime proof or independent security approval. No production behavior or permission is added.

PR #1 remains draft, open and unreviewed. The branch object reports unprotected; explicit protection details are inaccessible to this integration (HTTP 403), and no repository rulesets were returned. Other worker branches were not modified. All eight milestones remain as previously recorded; no milestone is complete.


## Audit and implementation update — 2026-11-06, CI-004 release manifest gate

The authorized feature branch was audited at 33d70c1462ee5a44c3a58edde6c02216dea63ccd. The complete recursive tree contained 255 entries; PROJECT-ADAPTER.md and the engineering roadmap were present; no repository SKILL.md was present. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed.

Open PRs #1 and #3–#7 were inspected. PR #1 remains a draft against main; no review submissions or inline review threads were present. The exact-head Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR workflows all completed successfully at 33d70c14. The Python policy suite reported 436 passing tests on push and PR; Android debug/release unit tests and builds, independent unsigned artifact reproducibility and the disposable API 35 x86_64 emulator smoke workflow passed. QA-011 remains an availability preflight, and QA-012 is structural semantics only; neither is spoken TalkBack acceptance. No physical Pixel 9 Pro test or independent security review occurred.

CI-004 adds a fail-closed check of the Gradle-merged release manifest to the existing two-runner CI-003 build. It rejects unreviewed/duplicate permissions, exported non-Home components, debug credential probes, unsafe backup/cleartext/debug flags, shared UID and instrumentation, and missing launcher/HOME filters. A deterministic manifest SHA-256 report is uploaded and compared across both independent runners. Sixteen focused local tests passed before submission; exact-head GitHub Actions remain the acceptance evidence.

No Android application behavior, permission, trust record, device setting, signing key, executor path, physical device or production deployment was modified. PR #1 remains draft. Independent security approval remains pending. M1/M2/M6 remain in progress, M3 partial, M4 not started, M5 not accepted, M7 blocked and M8 blocked. No milestone is complete.


## Audit and implementation update — 2026-11-06, CI-004B packaged APK manifest verification

The authorized feature branch was freshly audited at bfa3c8c1801c39ee48ac72d82c03a36c04d02d74. Its complete recursive tree contained 258 entries and was not truncated. The latest 12 commits, all six open PRs (#1 and #3–#7), PR #1 metadata/reviews/threads, exact-head Actions runs, Android/Kotlin/Python architecture, release workflow, manifest gate, tests and factory instructions were inspected. PROJECT-ADAPTER.md and the roadmap are present; no repository SKILL.md exists. The upstream shared factory package remains unverified and is not claimed as installed.

CI-004 exact-head evidence at bfa3c8c1 is complete: Phase 1 push [42131009261](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42131009261) and PR [42131015009](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42131015009) passed; each Python-policy job ran 452 tests, and Android unit/build, repeat debug build, strict dependency verification and negative control passed. CI-003 push [42131009270](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42131009270) and PR [42131014986](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42131014986) passed both independent release builders and the cross-runner verifier. The Gradle-merged release manifest gate passed on both builders with SHA-256 ae826c71392597b85c6c412dc6bcfa8c549c846f5be074b1eb5a5bb65129c071. QA-005 PR [42131015004](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42131015004) passed on the disposable API 35 x86_64 emulator through QA-020B3. QA-011 is availability-only and QA-012 structural-only, not spoken TalkBack acceptance. No physical Pixel 9 Pro validation occurred.

CI-004B adds final-APK binary manifest decoding with the Android SDK Command-Line Tools apkanalyzer manifest print command. The decoded package identity and security-relevant projection are checked against the Gradle-merged manifest; both are revalidated by the existing fail-closed policy. The report records decoder revision, raw XML hashes and canonical policy hashes, is included in each independent CI-003 artifact bundle/SHA256SUMS, and is byte-compared across runners. The existing CI-004 permission gate now rejects unknown uses-permission-* tag forms. This is build-time manifest consistency evidence, not runtime capability proof.

This run's new exact-head CI is the acceptance gate; no CI-004B result is claimed before it completes. PR #1 remains draft and unreviewed. No production behavior, permission, trust record, signing key, executor path, device setting or physical hardware was modified. Independent security approval remains pending. Milestones remain M1/M2/M6 IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7 BLOCKED and M8 BLOCKED; no milestone is complete.


### CI-004B first exact-head test correction — 2026-11-06

The first exact-head Phase 1 push and PR Python-policy jobs each discovered 466 tests: 465 passed and one workflow-source assertion errored. The assertion searched for the literal text "apkanalyzer manifest print", while the workflow correctly invokes the pinned-path variable as "$APKANALYZER" manifest print "$APK". The Android source/build jobs and CI-003 release builders were still running at the time of diagnosis; no APK decoder result is claimed from that attempt. The test was corrected to assert the actual explicit variable invocation and its APK argument. Exact-head reruns are required. This was a test expectation mismatch, not a release-manifest or application-code failure.


## Audit and implementation update — 2026-11-06, CI-004C Gradle-derived release identity

The authorized branch was audited at `1b4909e54b56cbf3c6573abf03c6de6002fb1fb3`. The complete recursive tree contained 261 entries and was not truncated. The latest 12 commits, six open PRs (#1 and #3–#7), PR #1 metadata/reviews/threads, exact-head Actions runs, Android/Kotlin/Python architecture, Gradle configuration, CI-003 workflow, CI-004/CI-004B gates, tests and factory instructions were inspected. `PROJECT-ADAPTER.md` and this roadmap are present; no repository `SKILL.md` exists. The authorized Library search recorded earlier found no upstream shared package; it remains unverified and is not claimed as installed.

At `1b4909e5`, Phase 1 push/PR, CI-003 push/PR and QA-005 PR all completed successfully. Phase 1 reported 466 Python tests on push and PR, Android debug unit/build and dependency-verification checks passed, CI-003 produced matching unsigned APK/SBOM/provenance and merged/packaged manifest reports across two builders, and QA-005 passed on a disposable API 35 x86_64 emulator. The CI-004B first attempt at `f645323e` had one Python workflow-source assertion mismatch (465/466); the assertion was corrected in `1b4909e5`, whose exact-head runs all passed. The prior CI-004B workflow links are recorded in the section above.

CI-004C removes the hard-coded `tech.mrnothing.os` expectation from the release workflow. AGP's Android Components API selects the single release variant and writes deterministic `release-variant-metadata.json` using the resolved `variant.applicationId`. The Gradle task fails closed if more than one release variant appears or the selected variant is not the unflavored `release` variant. A strict Python reader rejects missing, symlinked, oversized, malformed, duplicate-key, unknown-field, invalid-package and non-release metadata. The packaged APK gate validates both merged and packaged manifest package IDs against this Gradle-derived identity. CI-003 includes the metadata in each runner artifact and checksum inventory, records its identity and SHA-256 in provenance schema v2, validates the metadata against provenance on both bundles, and byte-compares it across independent runners. Negative controls cover a mismatched Gradle-derived ID, non-release variant, invalid ID, duplicate metadata keys and metadata tampering after provenance generation.

This is a build identity/provenance gate only. It does not change the application ID or Android runtime behavior, sign the APK, inspect DEX/native runtime capabilities, validate hardware-backed keys, test a physical Pixel 9 Pro or establish production readiness. Exact-head Phase 1, CI-003 and QA-005 workflows remain the acceptance gates for this commit. PR #1 remains open/draft/unreviewed against main. No other worker PR/branch was modified; main is unchanged; no force-push, merge, physical flashing, root escalation, production signing or deployment occurred.

Milestones remain M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. No milestone is complete. Independent security review, Pixel 9 Pro StrongBox/Keyguard and physical recovery, spoken TalkBack, supervised permission-bound execution, signed OTA and production release remain open.

## Audit and implementation update — 2026-11-06, CI-006 build-environment SBOM

The authorized branch was audited at `851c98c160565146952663a19c1418a4a007303a`; its complete recursive tree contained 263 entries and was not truncated. The latest 12 commits, six open PRs, PR #1 base/head/draft/reviews, exact-head GitHub Actions checks, CI-003 workflow and artifact logic, Android Gradle configuration, tests and roadmap were inspected. `PROJECT-ADAPTER.md` is present; root `SKILL.md` is absent (GitHub contents API 404). The upstream shared factory package remains unverified; this local adapter is not an installed copy.

At the audit baseline, Phase 1 push/PR both passed with 472 Python tests per run and Android unit/build/dependency checks. CI-003 push/PR passed both independent unsigned release builders and their cross-runner verifier. QA-005 PR passed its disposable API 35 x86_64 emulator smoke workflow. QA-011 remains availability-only; QA-012 remains structural-only, not spoken TalkBack acceptance. No physical Pixel 9 Pro or independent security approval is claimed.

CI-006 adds a scoped build-environment inventory and SPDX-2.3 SBOM to the existing CI-003 artifacts. It captures installed dpkg and pip packages, Android SDK package revisions, the verified Gradle distribution digest, JDK/Python runtime identities, direct AGP/Kotlin plugin versions, pinned GitHub Action commit SHAs, and GitHub runner image/OS identity. The inventory is digest-bound to the SPDX namespace and linked from provenance v2. Both independent CI-003 builders must emit byte-identical inventory/SBOM documents; a negative control rejects mutable action tags. The runtime SBOM remains a separate artifact.

The CI-006 scope is deliberately explicit: it does not claim to enumerate every hosted-runner toolcache file, every transitive Gradle plugin dependency or every file inside each Android SDK package. Exact-head CI is pending at submission. Keep PR #1 draft until the new Phase 1 and CI-003 push/PR jobs and independent verifier pass; independent security review remains a separate gate.

Specialist ownership is unchanged: Android, AI/agents, security, UX/accessibility, CI/QA, hardware/release, plus an independent supervisor/verifier. These are responsibilities, not a claim that separate agents or human reviewers have approved the change. No Android runtime capability, permission, trust record or agent executor is modified. No signing key, production deployment, root escalation, physical flashing, bootloader unlock or main merge is authorized.


## Audit and implementation update — 2026-11-06, CI-006A canonical SPDX integrity

The authorized branch was audited at 43a8aab3be49f0bbb8ecc602f47472b694f28181; its complete recursive tree contained 266 entries and was not truncated. The latest 12 commits, all six open PRs, PR #1 base/head/draft/review state, Phase 1/CI-003/QA-005 runs, CI-006 inventory/SBOM implementation, Gradle/Android architecture and existing tests were inspected. The local adapter and roadmap exist; no repository SKILL.md exists. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed.

At this baseline, Phase 1 push/PR passed with 490 Python tests on each event and Android unit/build/dependency checks passed. CI-003 push/PR passed both independent release builders and cross-runner verification. The CI-006 build-environment inventory contained 1,260 components; both builders produced identical inventory/SBOM digests and the verifier reported all build-environment equality checks true. The unsigned APK remains release_ready=false. QA-005 emulator validation was still in progress after launcher/recovery and QA-006–QA-011; no final emulator pass is claimed.

The CI-006 verifier previously compared package-URL sets and selected checksum values but did not enforce exact SPDX package metadata or relationship closure. CI-006A changes the verifier to validate inventory component identity, unique PURLs, digest shape, canonical ordering and exact component counts, then reconstruct the canonical SPDX-2.3 document from the inventory and require exact object equality. Five adversarial tests cover duplicate SPDX package records, package name tampering, relationship graph tampering, duplicate inventory PURLs and inconsistent counts. Exact-head Phase 1/CI-003 push/PR checks are pending; independent security review remains a separate gate.

Specialist responsibilities remain Android, AI/agents, security, UX/accessibility, CI/QA, hardware/release and an independent supervisor/verifier. Roles are responsibilities, not claims of separate-agent or human approval. No Android runtime capability, permission, trust record, executor, signing key, device setting, physical device or production deployment was changed. PR #1 remains draft; no other worker branch was modified; main remains unchanged. Upstream shared SKILL.md remains unverified.


### CI-006A fixture correction

The first submitted CI-006A commit over-escaped the Python date-regex and JSON fixture newline literals while generating the patch. The follow-up corrects the date regex to match the canonical UTC timestamp and writes real newline terminators in all five adversarial fixtures. No generator, inventory schema, workflow or Android runtime behavior changed. The corrected exact-head Phase 1/CI-003 runs are the acceptance evidence.


### CI-006A assertion correction

The first exact-head CI-006A run executed 495 tests and exposed one stale assertion message in the existing tampered-inventory test. The canonical SPDX validator rejected the modified inventory before the old namespace/hash-specific assertion text, so the implementation failed closed but the test expected only the previous wording. The assertion now accepts the new canonical-document rejection message as well. No production code or policy was weakened.


## Verification update — 2026-11-06, SEC-020B4C

The authorized branch audit at `1aa9d1247a46d8542a0f6c97828b151b2362b945` confirmed the SEC-020B4 JVM gate and worker-serialization tests existed, but no Android instrumentation source set exercised the actual Activity `onDestroy()` path. This run adds a platform-runner instrumentation test and wires `:app:connectedDebugAndroidTest` into QA-005 after the disposable emulator boots. The test blocks the single I/O worker, launches the real owner trust Activity, captures its queued operation token, destroys the Activity, verifies the token is invalidated/non-deliverable, releases the worker and drains the FIFO queue. It does not enter credentials or mutate trust. Upstream shared `SKILL.md` remains unverified; this local adapter is not an installed upstream package. Exact-head Android instrumentation and QA-005 results are required before acceptance.


### SEC-020B4C first-run compile correction

The first exact-head QA-005 run failed at `:app:compileDebugAndroidTestKotlin` because `android.test` is an optional Android platform test API and is not exposed by the default API-35 compile classpath. The Activity instrumentation test did not execute. The correction adds the installed SDK's `android.test.base.jar` and `android.test.runner.jar` only through `androidTestCompileOnly`, with a configuration-time presence check. The jars are not packaged into the app or test APK and no external Maven dependency is added. The QA workflow and Python regression tests enforce emulator-boot → instrumentation → launcher-smoke ordering. Re-run exact-head Phase 1, CI-003 and QA-005 before acceptance.


### SEC-020B4C lifecycle assertion correction

The second exact-head QA-005 attempt compiled the test source and ran it on the API-35 x86_64 emulator, but failed because `Activity.isDestroyed` was asserted immediately after `finish()`; the framework destruction callback is asynchronous. The test now observes `Application.ActivityLifecycleCallbacks.onActivityDestroyed` for the exact Activity instance using a five-second bounded latch, then verifies `isDestroyed` and gate invalidation. The observer is unregistered in `finally`; the blocked worker is also always released and drained. Exact-head rerun is required before acceptance.


## Engineering run update — 2026-11-06, SEC-020B4D

The latest audited feature head before implementation was `0a689cbdb64afd9921643116303f3924bc6509ac`; its complete recursive tree contained 272 entries. PR #1 was the only open PR whose head was the authorized branch; PRs #3–#7 target separate workstreams and were not modified. The current-head Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR workflows were inspected; QA-005 had completed successfully at run 42158804196. The local adapter and roadmap are present; repository SKILL.md is absent and the upstream shared package remains unverified.

SEC-020B4D adds a narrow Activity-facing trust-store port and a debug-only, non-exported test Activity host. Two instrumentation cases use a synthetic Ed25519 authority and an in-memory fake backend to block either final trust-state revalidation before commit claim or the commit operation after claim. They destroy the real Activity at each boundary and verify pre-claim mutation is suppressed, post-claim fake atomic completion is not falsely canceled, and destroyed-Activity UI delivery is suppressed. The QA-005 workflow sets a fixed synthetic emulator PIN through ordinary ADB shell before the instrumentation task and clears it in an EXIT/INT/TERM cleanup trap; both cases reuse it to exercise the actual DEVICE_CREDENTIAL callback. No real authority, user credential, StrongBox alias, AtomicFile, permission, executor, physical device or production release is involved.

The test host and fake backend slot are present only in the debug source set; the debug manifest entry is non-exported and absent from the main/release manifest. Exact-head CI is pending until the new instrumentation and static regression gates run. Independent security review remains pending. The upstream shared SKILL.md is not claimed as installed.


## Engineering run update — 2026-11-06, SEC-020B4D Android Ed25519 provider correction

The API-35 x86_64 QA-005 run 42165625523 reached the in-flight trust-transaction instrumentation but failed at the synthetic RFC 8032 public-key fingerprint setup: the platform-default Ed25519 KeyFactory did not import the external SPKI. The failure is treated as an Android provider-compatibility defect, not as a passing lifecycle test. The implementation switches both KeyFactory and Signature operations to a pinned Bouncy Castle 1.86 provider instance, without global Security provider registration. The dependency is pinned in Gradle verification metadata with SHA-256 for its JAR and POM, and its license is recorded. A JVM regression test checks the RFC 8032 fingerprint and verifies that the process-wide provider registry is unchanged. Exact-head Phase 1, CI-003 and QA-005 reruns are required before SEC-020B4D acceptance; the upstream shared SKILL.md remains unverified and uninstalled.


## Engineering run update — 2026-11-06, SEC-020B4D credential preflight correction

The audited authorized branch head was `30fea42e61330b7ec283a5aa6bbc346e6e44213b`. Exact-head Phase 1 passed (505 Python tests, Android unit/build/dependency checks); CI-003 passed both independent builders and verifier. QA-005 booted the API-35 x86_64 disposable emulator and compiled the instrumentation suite, but both SEC-020B4D commit-boundary tests failed before reaching the credential-confirmation binding. The assertion reported `credential confirmation was not initiated`; the later QA-005 steps were skipped. This is not a pass and does not establish a production trust-store defect.

This correction makes the instrumentation harness explicitly wake the disposable emulator, verify a secure credential exists, and check the real Android safety signals (device unlocked, keyguard unlocked, user unlocked, screen interactive). If and only if the emulator is actually keyguard-locked, the test waits for the visible SystemUI PIN field and enters the synthetic test PIN through that system-owned field. It never calls `wm dismiss-keyguard`, never enters a credential into an app-owned field, and reports status plus platform safety/credential availability diagnostics on failure. The existing credential-only BiometricPrompt remains the production factory under test.

Exact-head Phase 1, CI-003 and QA-005 reruns are required before SEC-020B4D acceptance. This remains disposable-emulator-only evidence; no physical Pixel 9 Pro, StrongBox, AtomicFile crash recovery, spoken TalkBack, independent human security approval or production readiness is claimed. Upstream shared `SKILL.md` remains unverified and is not claimed as installed.


## SEC-020B4D exact-head QA failure analysis and diagnostic correction — 2026-11-06

At branch head 2299b723621f654bb3782f8fa0371a13f8b37122, Phase 1 push [42168597642](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168597642) and PR [42168602224](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168602224) passed; each Python suite ran 506 tests, and Android debug unit/build/dependency checks passed. CI-003 push [42168597742](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168597742) and PR [42168602103](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168602103) passed independent builders and cross-runner verification. QA-005 [42168602258](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168602258) booted the disposable API 35 emulator, compiled instrumentation, and began the after-commit-claim test; that test failed, and later QA steps were skipped. The uploaded diagnostics did not include the AndroidJUnitRunner XML/HTML result bundle, and the 300-line logcat tail did not expose the assertion cause. SEC-020B4D remains unaccepted.

The next correction broadens credential UI detection to inspect accessible Android windows and recognize the known auth_credential_input and lockPassword fields only when hosted by com.android.systemui or com.android.settings. The test now waits for the Activity's explicit final-revalidation status after submitting the synthetic emulator PIN, then reports the Activity status and both boundary latch states if the fake backend is not reached. This narrows the failure signal between system credential UI detection, credential callback acceptance and the trust I/O boundary; it does not relax credential-only authentication or the device safety gate.

The QA-005 always-run evidence step now preserves Android connected-test XML/HTML reports from both Gradle report/output locations and captures a larger 2,000-line all-buffer logcat tail. These diagnostics are needed to distinguish a test assertion from an instrumentation-process crash. No production credential, trust mutation, Android permission, agent execution, privileged shell, physical device or production release is involved. Exact-head Phase 1, CI-003 and QA-005 reruns remain required; upstream shared SKILL.md remains unverified and is not claimed as installed.


## Engineering Factory update — Android 15 Keyguard PIN selector correction (2026-11-06)

Audit head: `23993daed4e213b95cda115ca8700b4b92211174`. The complete recursive tree contains 276 entries and is not truncated. The 15 latest feature-branch commits, all six open PRs (#1 and #3–#7), PR #1 metadata/reviews, exact-head Actions runs, QA-005 job steps/logs/artifact metadata, Android instrumentation, credential prompt/safety gate, trust Activity, coordinator/store, workflow and factory docs were inspected. `PROJECT-ADAPTER.md` and the roadmap are present; repository `SKILL.md` is absent. The upstream shared package remains unverified and is not claimed as installed.

QA-005 run [42174961897](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42174961897) failed both SEC-020B4D tests before the fake-store boundary. Logs show the emulator was secure, awake and credential-capable, but the lockscreen PIN selector was not detected. Android 15 AOSP source confirms `pinEntry` is a `com.android.keyguard.PasswordTextView`, not an EditText; the password field is `passwordEntry`/EditText. The debug-only detector now uses exact system-package, resource-ID and class-name pairs for both forms, and a Python regression test locks those mappings. No production runtime behavior or permissions change.

At the audited head, Phase 1 push/PR and CI-003 push/PR passed; each Python suite reported 507 tests. QA-005 failed and later QA steps were skipped. The new correction is pending exact-head Phase 1, CI-003 and QA-005 verification. PR #1 remains open/draft/unreviewed against unchanged main. PRs #3–#7 and their branches remain untouched. No root escalation, physical flashing, production signing/deployment or merge occurred. Milestones remain M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED.


## Engineering Factory update — API 35 lockscreen PIN-pad reveal (2026-11-06)

Audit head: `e8d255c24db2670adec78d5dc3d505acedc9c29c`. The complete recursive tree contains 276 entries and is not truncated. The 12 latest feature-branch commits, all six open PRs (#1 and #3–#7), PR #1 head/base/draft/review state, exact-head Actions runs/jobs, QA-005 JUnit XML, Android instrumentation, debug-only credential probe, trust Activity/coordinator/store, workflow, adapter and roadmap were inspected. `PROJECT-ADAPTER.md` and the roadmap are present; repository `SKILL.md` is absent. The upstream shared package remains unverified and is not claimed as installed.

At this head, Phase 1 push [42181487968](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181487968) and PR [42181494281](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181494281) passed; each Python policy job ran 508 tests and both Android jobs passed. CI-003 push [42181488047](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181488047) and PR [42181494488](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181494488) passed both independent builders and the independent verifier. QA-005 [42181494325](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181494325) failed both SEC-020B4D cases during lockscreen preflight; the queued-activity destruction instrumentation passed. The JUnit XML and job log show a secure, interactive, locked, credential-capable emulator with no visible SystemUI PIN field. The workflow cleared the synthetic PIN successfully. Later launcher/accessibility QA steps were skipped.

The selector mapping correction from the previous commit was present. The remaining harness gap was that `KEYCODE_WAKEUP` exposed the lockscreen but no normal swipe-up gesture was issued to reveal the PIN pad. This run adds a bounded display-relative swipe through instrumentation UI automation only when the secure Keyguard is locked and the exact system credential field is not already visible. The test still requires an exact visible SystemUI package/resource-ID/class match before entering the synthetic PIN. A cancellation event is sent if the injected gesture fails partway. No Keyguard dismissal API, root, production change, permission, trust-store mutation or executor path is introduced.

Exact-head Phase 1, CI-003 and QA-005 reruns are required. PR #1 remains open/draft/unreviewed against main; no merge. PRs #3–#7 remain untouched. Branch protection is reported disabled by the branch endpoint; no protection enforcement is assumed. Milestones remain M1 IN PROGRESS; M2 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M6 IN PROGRESS; M7 BLOCKED; M8 BLOCKED. Independent human security review and physical Pixel 9 Pro validation remain pending.


## Engineering Factory update — unprivileged Android input swipe correction (2026-11-06)

Audit head: `34b34e1da3158c5c0497142de92391295f8b31a7`. The recursive tree remains 276 entries and complete. The prior run's Phase 1 push/PR and CI-003 push/PR all passed; each Python suite ran 509 tests. CI-003 verified byte-identical unsigned release APKs on two independent runners (7,829,060 bytes; SHA-256 `3c09c4b4c7956cb7e2a90fdc96c9ab909f53f4526c8439ed25b0aae78c49f1ea`; normalized SHA-256 `9e6c4b9489af0f8b07f1d5fdae1d2ac6746041686d84fded9c0cecd4ddbc97d1`); scoped environment inventory: 1,260 components; `release_ready=false`.

QA-005 [42183562453](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183562453) booted API 35 and ran three instrumentation tests. The queued-inspection lifecycle test passed; both SEC-020B4D commit-boundary tests failed before the credential prompt/fake-store boundary. The previous `UiAutomation.injectInputEvent` swipe was accepted but did not expose the SystemUI PIN field. The synthetic emulator PIN cleanup succeeded; later QA steps were skipped. Artifact [13486851509](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183562453/artifacts/13486851509) contains JUnit XML and device logs.

This correction uses the Android `input swipe` utility from the test's ordinary `uid=2000(shell)` identity, after verifying that identity, with display-relative coordinates. It runs only when Keyguard is locked and no exact system credential field is already visible. The existing strict SystemUI package/resource-ID/class selector remains mandatory before the synthetic PIN is entered. No root, Keyguard dismissal, credential bypass, production change, permission, trust mutation or executor path is introduced.

The new exact-head Phase 1/CI-003/QA-005 workflows must all be inspected. SEC-020B4D remains NOT ACCEPTED until both commit-boundary cases and the full QA sequence pass. PR #1 remains open/draft/unreviewed; PRs #3–#7 untouched. Branch protection is disabled according to the branch endpoint. Milestones remain M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7/M8 BLOCKED. Upstream shared `SKILL.md` remains unverified; no installation is claimed.


## Engineering Factory update — credential UI failure diagnostics (2026-11-06)

At head `e5a313ac6c942b982739294e097daa90c6eadcf4`, Phase 1 push/PR [42184476741](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184476741) / [42184482244](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482244) passed (509 Python tests each; Android build/JVM checks passed). CI-003 push/PR [42184476880](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184476880) / [42184482249](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482249) passed independent reproducibility.

QA-005 [42184482208](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482208) booted API 35 and ran three instrumentation tests. The queued Activity lifecycle case passed; both commit-boundary cases failed before prompt display after the unprivileged `input swipe` returned without a reported shell error. Synthetic PIN cleanup succeeded; later QA steps were skipped. Artifact [13487605359](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482208/artifacts/13487605359).

The next implementation is diagnostics-only: capture a bounded UiAutomation accessibility-window/node snapshot and filtered window-focus summary on failure, plus shell identity/display/swipe coordinates. The snapshot is capped at 80 nodes/9 KB and recycles each AccessibilityNodeInfo. No further gesture changes are justified until evidence shows whether the lockscreen root is visible and what window owns focus. No production trust behavior, permission, root, credential bypass, trust mutation or executor path is changed.

Exact-head Phase 1, CI-003 and QA-005 must be rechecked. SEC-020B4D remains NOT ACCEPTED until both commit-boundary tests and the full QA sequence pass. PR #1 remains open/draft/unreviewed; PRs #3–#7 untouched. Branch protection remains disabled per branch endpoint. Upstream shared SKILL.md remains unverified.


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


## Engineering Factory run — SEC-020B4D exact-head acceptance and SEC-020B5 AtomicFile recovery tests (2026-11-06)

**Audit baseline:** branch `feat/phase1-agentic-phone`, exact starting head `ceebf9fb24d46c2156d584a1b8995e8a5bbc0745`; recursive Git tree contains 276 entries and is not truncated. `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` are present; no repository `SKILL.md` exists. The upstream shared package remains unverified and is not claimed as installed. Open PRs #1 and #3–#7 were inspected. PR #1 remains draft/open against `main`, with zero submitted reviews and zero inline review threads. No other PR branch was modified.

**Exact-head SEC-020B4D / QA-005 acceptance at `ceebf9fb24d46c2156d584a1b8995e8a5bbc0745`:**

- Phase 1 push [42200088688](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200088688) and PR [42200100036](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200100036) completed successfully. Both Python-policy jobs ran 515 tests and reported `OK`. Android jobs completed `:app:testDebugUnitTest`, `:app:assembleDebug`, same-run repeat debug APK comparison, strict Gradle dependency verification and the modified-dependency negative control. The source Android manifest security gate passed.
- CI-003 push [42200088574](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200088574) and PR [42200100017](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200100017) completed successfully. Independent runners produced byte-identical unsigned release APKs (7,829,060 bytes; SHA-256 `3c09c4b4c7956cb7e2a90fdc96c9ab909f53f4526c8439ed25b0aae78c49f1ea`; normalized-entry SHA-256 `9e6c4b9489af0f8b07f1d5fdae1d2ac6746041686d84fded9c0cecd4ddbc97d1`). Runtime inventory and SPDX runtime SBOM matched. The verifier explicitly reports `reproducible=true` and `release_ready=false`; artifacts are unsigned.
- QA-005 PR [42200100094](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200100094) completed successfully. All 21 workflow steps succeeded, including API 35 x86_64 emulator boot, the three-test SEC-020B4D instrumentation step, launcher runtime/recovery, QA-006 through QA-013, QA-020B2 and QA-020B3, diagnostics and evidence upload. The log reports three tests started/finished, Gradle `BUILD SUCCESSFUL`, and `Lock credential cleared`. Evidence artifact [13493729544](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42200100094/artifacts/13493729544), SHA-256 `0eba705b67fbb6673504bff1c794fae5abb681c008973aef8854ac63eacb677f`.
- QA-011 is a read-only TalkBack availability preflight and reported `blocked_service_disabled`; QA-012 is structural semantics only. Spoken TalkBack navigation is not accepted.

This supersedes the prior stale pending note for `ceebf9fb24d46c2156d584a1b8995e8a5bbc0745`: SEC-020B4D is accepted for the tested API 35 x86_64 disposable-emulator lifecycle path only. It does not establish StrongBox, Android Keystore hardware behavior, AtomicFile power-loss durability, Pixel 9 Pro compatibility, spoken TalkBack, human security approval or production readiness. The existing QA workflow uses `sudo chmod 666 /dev/kvm` on its ephemeral GitHub-hosted runner to expose KVM; no root operation or credential action was performed on a physical Android device.

**Next bounded task — SEC-020B5:** add API-35 instrumentation tests for the existing `AndroidAtomicAuthorityRecordPersistence` adapter using a temporary app-private test directory. Cover atomic round-trip/replacement, interrupted replacement backup restoration, interrupted first-write classification, oversized stored records and invalid write bounds. No production persistence code or trust semantics are changed. The interruption case closes an unfinished `AtomicFile.startWrite()` stream without `finishWrite()`/`failWrite()`; it is a deterministic interruption-window test, not a real process-kill or power-loss simulation. Exact-head CI is pending for the new test commit. See `docs/SEC-020B5-ATOMICFILE-RECOVERY.md`.

**Milestones remain:** M1/M2/M6 IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7/M8 BLOCKED. No milestone is complete. Independent human security review, physical Pixel 9 Pro/StrongBox validation, spoken TalkBack, signed release, OTA and deployment remain outstanding.


## Audit and correction — 2026-11-06, SEC-020B5 first-write semantics

The exact audited branch head was 67252b5d4418bd5419a70dafea943d04f8d91c11; the recursive Git tree contained 278 entries. The local adapter and roadmap are present, repository SKILL.md is absent, and the upstream shared factory package remains unverified and is not claimed as installed. The six open PRs (#1, #3, #4, #5, #6 and #7) were reviewed; PR #1 remains the phase-1 draft. The latest exact-head Phase 1 push/PR and CI-003 push/PR workflows passed, but QA-005 run [42203152698](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42203152698) failed one new SEC-020B5 instrumentation assertion.

The failure was in the test's assumption, not production code: an interrupted first Android AtomicFile write has no previous base to restore. Android discards the uncommitted staging file and the persistence adapter correctly reports Missing. The trust-store coordinator has the generation marker first, so a nonzero marker with a missing active record must produce RecoveryRequired(ACTIVE_RECORD_MISSING), not Empty.

The test is corrected to assert that two-layer behavior using a synthetic marker-only crypto fixture. No production Android source, permissions, Keystore policy or trust transition was changed. Exact-head CI and emulator rerun are pending. Independent human security approval, spoken TalkBack, physical Pixel 9 Pro/StrongBox and production readiness remain unverified.


## Engineering Factory run — 2026-11-06, SEC-020B5 acceptance and SEC-020B6

**Audit:** branch `feat/phase1-agentic-phone`, head `c80634ec871516e829fb18025de8af732fee422f`; complete recursive tree 279 entries, not truncated. `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` exist. No repository `SKILL.md` exists. The upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed.

**Pull requests:** six open PRs (#1, #3, #4, #5, #6, #7). PR #1 remains open/draft against `main`, with current head c80634ec and zero submitted reviews or inline review threads. Other PR branches were not changed.

**SEC-020B5:** accepted for the exact-head API 35 x86_64 disposable-emulator AtomicFile path. Phase 1 push/PR each passed 518 Python tests and Android unit/build/dependency/manifest gates. CI-003 push/PR independent verification passed; unsigned APKs were byte-identical at 7,829,060 bytes with SHA-256 `3c09c4b4c7956cb7e2a90fdc96c9ab909f53f4526c8439ed25b0aae78c49f1ea`. QA-005 passed all 21 workflow steps; eight instrumentation tests started and finished successfully, including three SEC-020B4D and five SEC-020B5 tests. Synthetic PIN cleanup succeeded. Detailed run IDs and limitations are in the roadmap and SEC-020B5 document.

**SEC-020B6:** an isolated test-alias namespace and eight AndroidKeyStore failure-mode instrumentation cases have been added; a Python source-policy suite protects production alias defaults and StrongBox-only behavior. Production construction remains no-argument with the original aliases. Exact-head CI is pending; do not accept SEC-020B6 until Phase 1, CI-003 and QA-005 all pass.

**Safety/evidence:** no production authority was enrolled, no user device or production alias was touched, no permission was granted, and no root/flashing/deployment occurred. Emulator StrongBox behavior, physical Pixel 9 Pro, spoken TalkBack, actual process-kill/power-loss durability, independent human security approval and production release remain unverified. QA-011/012 are not spoken TalkBack acceptance. No milestone is complete.

**Next bounded task:** after SEC-020B6 exact-head CI, add deterministic KeyInfo/Keystore provider-failure injection for metadata exceptions and missing AES-key-with-valid-marker states; actual StrongBox/reboot/recovery remains a supervised M7 Pixel 9 Pro hardware gate.


## SEC-020B6 emulator fixture correction — 2026-11-06

At head `28065d7416c2aa89ffc17ed3dcf4614f2a34e733`, Phase 1 push/PR passed with 524 Python tests each and Android unit/build/dependency gates. CI-003 push/PR passed independent-runner verification; unsigned APKs were byte-identical (7,829,728 bytes; SHA-256 `09623ce52db112aab99a23b08196b260e9fab02456e76a41d970c14edbc69510`). QA-005 run [42220218287](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42220218287) started 16 instrumentation tests; two SEC-020B6 tests failed before crypto assertions because the synthetic Ed25519 helper selected the uninitialized AndroidKeyStore provider. The other 14 tests reported no failures; fail-fast skipped later QA stages. Diagnostics uploaded and synthetic lock credential cleanup reported success.

The fixture now selects an explicit Bouncy Castle provider instance for the in-memory Ed25519 key pair. This is test-only; production Keystore policy and aliases are unchanged. SEC-020B6 remains unaccepted until exact-head QA-005 and all Phase 1/CI-003 reruns pass.


## Audit update — 2026-11-06, SEC-020B6 acceptance and SEC-020B6A

The latest audit was performed at `83a3aa2e90e89b29bae4f9c2b14cd402f084ebc7`. The recursive tree contained 282 entries and was not truncated; six open PRs were reviewed; PR #1 remains draft with no reviews; the branch is unprotected and repository rulesets are empty. This local adapter and the engineering roadmap are present; repository SKILL.md is absent; the upstream shared factory package remains unverified and is not claimed as installed.

SEC-020B6 passed exact-head Phase 1 push/PR, CI-003 push/PR and QA-005. The API 35 x86_64 disposable emulator ran 16 instrumentation tests with zero failures or skips, including three SEC-020B4D, five SEC-020B5 and eight SEC-020B6 cases. QA-011 remains a disabled-service preflight and QA-012 remains structural semantics only. CI-003 verified byte-identical unsigned APKs and reports release_ready=false.

SEC-020B6A adds an internal KeyInfo-reader injection seam with the existing AndroidKeyStore implementation as the production default. New tests inject checked/runtime metadata exceptions and verify that a missing AES alias with a generation marker produces RecoveryRequired rather than Empty. The missing-AES test uses synthetic metadata and is not StrongBox evidence. Exact-head Phase 1, CI-003 and QA-005 reruns are pending.

**Next bounded task:** after SEC-020B6A acceptance, test Keystore load and alias-enumeration failures. Keep M1/M2/M6 in progress, M3 partial, M4 not started, M5 not accepted, M7 blocked pending Pixel 9 Pro access and M8 blocked. No milestone is complete. Independent human security review remains pending.


## Engineering Factory audit and implementation — 2026-11-06, SEC-020B6A acceptance / SEC-020B6B

The latest audited head was `f6e4099ae991eba9b7e8a56a674b08efd479c7ed`; its complete recursive tree contains 282 entries and is not truncated. `PROJECT-ADAPTER.md` and the engineering roadmap exist; repository `SKILL.md` is absent. The upstream shared factory package remains unverified and is not claimed as installed. Six PRs (#1, #3, #4, #5, #6, #7) are open/draft. PR #1 is open/draft against `main`, with the authorized branch as head and no submitted reviews or inline review threads. The rulesets endpoint is empty. The branch-protection endpoint returned 403 for this integration, so branch protection is not independently verified. No other PR branch was modified.

SEC-020B6A passed exact-head Phase 1 push/PR, CI-003 push/PR and QA-005. Python policy ran 526 tests. CI-003 verified byte-identical unsigned APKs (7,830,680 bytes; SHA-256 `60f0df5a92ebed50e1ddf1885e56e5b12ceb25c19263f8910943d832d53fb53f`), matching normalized contents, runtime inventory, SPDX runtime SBOM and scoped CI-006 build-environment inventory. QA-005 passed 19 instrumentation tests with zero failures/errors/skips on an API 35 x86_64 disposable emulator, plus QA-006–QA-013 and QA-020B2/B3. QA-011 found TalkBack disabled; QA-012 is structural only. No physical Pixel/StrongBox or human security review is implied.

SEC-020B6B adds an internal `AndroidAuthorityKeyStoreReader` seam. The production default still loads `AndroidKeyStore` and delegates alias enumeration to the platform `KeyStore`; production construction remains no-argument with unchanged aliases. Five isolated instrumentation cases inject GeneralSecurityException, IOException and runtime failures during load, plus GeneralSecurityException and runtime failures during alias enumeration. Each verifies `Unavailable`, refuses marker creation and leaves test aliases absent. Exact-head Phase 1, CI-003 and QA-005 validation are pending.

**Next bounded task:** after SEC-020B6B acceptance, test marker/AES `KeyStore.getKey` failures through a narrow read seam. Physical StrongBox, Pixel 9 Pro, reboot/recovery and production release remain separate supervised gates.


## Engineering Factory audit — 2026-11-06, SEC-020B6B acceptance and SEC-020B6C

The authorized branch was audited at `83bb54904e7f9db15ac42a532f96dbededc91bca`: recursive tree 282 entries (not truncated), latest 20 branch commits inspected, 223 commits ahead of `main`, 0 behind. `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` are present. No repository `SKILL.md` exists; the upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. Six PRs (#1, #3, #4, #5, #6, #7) are open/draft. PR #1 targets `main`, matches this branch, and has no submitted reviews or inline threads. The branch API reports `protected=false`; repository rulesets are empty. No other PR branch was changed.

SEC-020B6B exact-head evidence:
- Phase 1 push/PR runs 42226887109 and 42226898225 passed; each Python policy suite ran 528 tests. Android debug unit/build, repeat-build, dependency verification/negative control and manifest security checks passed.
- CI-003 push/PR runs 42226887105 and 42226897830 passed. Independent unsigned APKs were byte-identical (7,831,748 bytes; SHA-256 `3008fcdc6a737aaa9b200565f5535abe84ad2dcd0731f8cd0811c73a4a16627f`; normalized entries `600e753c6aebf12cc8b8b6774910a30ee57cfe44f389acd473be4c433c7acf15`). Runtime inventory and SPDX runtime SBOM matched; `reproducible=true`, `release_ready=false`. CI-006's 1,260-component inventory is scoped, not a complete host-image SBOM.
- QA-005 run 42226897923 attempt 2 passed all emulator-smoke steps on a disposable API 35 x86_64 emulator. Attempt 1 had a SEC-020B4D credential callback failure; a failed-job-only retry passed without source changes. Evidence artifact 13511926456 (SHA-256 `6f7261289126bf0358afd93ae113e1bc636c6daa20834eccadda4a4be5f52ab0`). QA-011 remains service-disabled preflight; QA-012 is structural only, not spoken TalkBack.

SEC-020B6B is accepted only for its emulator Keystore load/alias-enumeration failure scope. It is not Pixel 9 Pro or physical StrongBox evidence.

SEC-020B6C adds an internal KeyStore `getKey` seam whose production implementation delegates to AndroidKeyStore `KeyStore.getKey(alias, null)`. Four isolated tests inject marker/AES key retrieval failures via `UnrecoverableKeyException` and `ProviderException`. Marker retrieval failure must classify the store as Unavailable and block generation advancement; AES retrieval failure must reject encrypt/decrypt and expose RecoveryRequired for a present envelope, never Empty/Active. No production alias, key, authority, permission, trust state or executor is changed. Test aliases are UUID-scoped and cleaned. Exact-head CI is pending.

No milestone is complete. M1/M2/M6 remain IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED pending physical Pixel 9 Pro access; M8 BLOCKED. Independent human security review, spoken TalkBack, physical StrongBox/reboot recovery, signed release and OTA rollback remain outstanding.


## Engineering Factory audit and implementation — 2026-11-06, M7 offline Pixel 9 Pro preflight

The authorized branch was audited at `520686472371c3e1ae609911bd78eae687b2b8a7`. The complete recursive tree contained 283 entries and was not truncated; the latest 20 commits, six open pull requests, current workflow runs, Android/Python architecture, QA-011/QA-012, and existing project instructions were inspected. `PROJECT-ADAPTER.md` and the engineering roadmap are present. Repository `SKILL.md` is absent (GitHub contents lookup returned 404); the upstream shared Universal Autonomous Engineering Factory package remains unverified and is not claimed as installed. PR #1 is the existing draft umbrella against `main` and matches the authorized branch. PRs #3–#7 remain separate workstreams and were not modified. The branch API reports `protected=false`; repository rulesets are empty. The branch-protection detail endpoint returned 403 to this integration, so required-review enforcement cannot be established.

All five exact-head workflows for `520686472371c3e1ae609911bd78eae687b2b8a7` passed: Phase 1 push/PR runs 42253179947 and 42253188165; CI-003 independent unsigned reproducibility push/PR runs 42253179969 and 42253188174; QA-005 disposable emulator PR run 42253188203. Phase 1 Python security/static checks and Android debug unit/build/repeat-build/dependency-negative-control/manifest gates passed. CI-003's two builders and independent verifier passed. QA-005's emulator smoke steps passed, including the existing QA-011 read-only TalkBack preflight and QA-012 structural semantics check; neither is spoken TalkBack acceptance. No physical device was connected.

Existing QA-011 is specifically a TalkBack package/service preflight; SEC-014D is an in-app Keyguard/device-lock preview gate. Neither performs the M7 exact-model/bootloader/Verified Boot/StrongBox-feature snapshot validation. The new `scripts/m7_pixel9pro_preflight.py` validates an operator-supplied redacted JSON snapshot offline and never invokes ADB, shell, fastboot or device commands. Its 18 synthetic tests cover exact Pixel 9 Pro/`caiman` identity, API floor, connected/authorized ADB state, locked bootloader, green Verified Boot, locked vbmeta, emulator rejection, StrongBox feature presence, malformed/missing input and identifier non-disclosure. A passing result is only `ready_for_supervised_hardware_session`; `acceptance_passed` and `strongbox_key_security_level_verified` remain false. It cannot complete M7.

Local validation executed: `python3 -m unittest -v tests/test_m7_pixel9pro_preflight.py` — 18 passed. Exact-head GitHub CI for the new commit is required before accepting the utility. No ADB connection, installation, permission change, reboot, root, flashing, key operation or physical hardware validation was performed. Independent human security review remains pending.


## Engineering Factory audit and implementation — 2026-11-07, AGENT-004H durable action reservation

The authorized branch was audited at 52e9300433a8ee45512d2249c53cbf6f9af5ec4c. The complete recursive tree contained 299 entries; the latest 20 commits, all six open PRs, PR #1 diff/reviews/threads/comments, exact-head Actions jobs, project adapter, roadmap, M3 execution contract, owner-consent transport, existing replay ledger, Android CommandRouter and test-discovery script were inspected. PR #1 remains the open draft umbrella against main and matches the authorized branch. PRs #3–#7 are separate workstreams and were not modified. The branch reports protected=false and the repository rulesets endpoint is empty. No repository SKILL.md exists. The upstream shared factory package remains unverified and is not claimed as installed.

The exact-head baseline at 52e9300433a8ee45512d2249c53cbf6f9af5ec4c passed all five workflows: Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR. Both Phase 1 Python jobs ran 614 tests; Android debug unit/build/dependency gates passed. CI-003 independently verified byte-identical unsigned APKs and matching scoped runtime SBOM/provenance; release_ready=false. QA-005 emulator workflow passed, but QA-011 reported blocked_service_disabled and QA-012 remained structural-only, not spoken TalkBack acceptance. No physical Pixel was accessed.

The existing DurableReplayLedger stores a generic device/command replay marker and is not sufficient for final side-effect idempotency. AGENT-004H adds a separate durable action reservation state machine bound to owner/device/session, capability nonce, protocol/action/argument digest, signed validity window, transport certificate, credential generation and consent-key digest. It uses a domain-separated deterministic key, a unique owner/device/nonce constraint, SQLite WAL/FULL transactions, bounded capacity and fail-closed storage behavior. Duplicate bindings cannot dispatch twice; changed bindings conflict; DISPATCH_STARTED survives restart and is never automatically reclaimed; uncertain outcomes are terminal. The ledger stores no raw action arguments or results.

The new ledger is a storage primitive only. It is not connected to the mTLS adapter, Android CommandRouter, runtime permissions or any executor. The future adapter must create reservation requests only from retained verifier-created capability records. A fresh Android permission/role query must remain a separate final gate immediately before any platform call. No listener, permission declaration/grant, shell bridge, device action, hardware operation or production deployment was added.

Local scratch validation of the new module/test pair: compileall passed; 35 focused unittest cases passed. This was not a full repository checkout/preflight. Exact-head GitHub Actions for the new commit and QA-005 rerun are pending. Independent human security review remains pending. No milestone is complete. M1/M2/M6 remain IN PROGRESS; M3 PARTIAL; M4 NOT STARTED; M5 NOT ACCEPTED; M7 BLOCKED; M8 BLOCKED.


## Engineering Factory audit and implementation — 2026-11-07, AGENT-004L owner Accessibility disclosure

The authorized branch was audited at 43ad1c83fa46d3d3305d5a96948cb171d8f0e8f7: recursive tree 312 entries (not truncated), latest 20 commits inspected, 260 commits ahead of main, zero behind. Six PRs (#1, #3–#7) are open/draft. PR #1 is the open draft umbrella against main, matches the branch and has no submitted reviews or inline threads. Branch metadata reports protected=false; rulesets are empty; branch-protection detail returned 403, so enforcement is unverified. PROJECT-ADAPTER.md exists, repository SKILL.md is absent, and the upstream shared factory package remains unverified/not installed.

The exact-head baseline passed all five workflows (Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR). Both Python policy jobs ran 668 tests and passed; Android debug unit/build/repeat-build/dependency checks passed; independent unsigned release reproducibility passed; all QA-005 emulator steps passed. QA-011 remains a TalkBack availability preflight and QA-012 structural semantics only.

AGENT-004L adds a non-exported owner-visible Accessibility disclosure screen, read-only exact-component status reader, explicit Settings handoff, launcher entry and JVM/instrumentation/Python boundary tests. The current manifest still declares no AccessibilityService or MediaProjection service and no new permission. No programmatic enable/disable, permission prompt, screen capture, gesture, executor or CommandRouter integration was added. Local pure-JVM harness passed five state scenarios. Exact-head CI for the new commit is pending at submission; no local Android Gradle/emulator run is claimed because the local container has no Android SDK. Independent security/accessibility review remains pending.
