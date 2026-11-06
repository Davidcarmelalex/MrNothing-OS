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
