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
