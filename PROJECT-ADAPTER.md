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
