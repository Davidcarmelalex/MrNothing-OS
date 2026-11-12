# QA-020B2 — owner authority trust UI runtime smoke

**Scope:** disposable Android x86_64 emulator only; SEC-020B2 OwnerAuthorityTrustActivity.

## Purpose

Exercise the newly added owner-facing authority trust Activity through its real launcher navigation path. This closes the previous gap where SEC-020B2 had JVM parser/state tests and source gates but the emulator workflow did not open the Activity.

## Runtime checks

1. Launch MainActivity and open the non-exported trust Activity using its visible launcher action.
2. Verify the title, five field labels, five editable fields, and one supported initial trust state (empty or unavailable on a fresh AVD).
3. Tap fingerprint preview with empty input and require the parser to refuse the candidate.
4. Tap the trust confirmation action. A fresh disposable AVD has no configured secure lock, so OwnerCredentialSafetyGate must refuse before a system credential prompt. If a secure credential screen unexpectedly appears, the test sends only Back and verifies cancellation; it never enters a PIN, password or pattern.
5. Tap Cancel and clear; verify all five fields are empty and the trust-state label is unchanged.
6. Return to the launcher and verify the launcher title is present.

## Safety constraints

- The script refuses any serial that is not emulator-* and checks ro.kernel.qemu=1.
- No authority key, fingerprint, rotation signature, PIN, password or pattern is entered.
- No Android permission is granted, no role is changed, and no network or agent executor is invoked.
- No Keystore alias is created or deleted by the intended negative path. StrongBox availability is not inferred from the emulator result.
- The test does not attempt a successful credential confirmation or trust-store commit.

## Acceptance evidence

The CI workflow step is QA-020B2: owner authority trust UI runtime (emulator only). Its uploaded hierarchy snapshots and result record are diagnostics, not release artifacts. The Python helper tests validate strict hierarchy assertions and emulator-only script guards.

**Limitations:** this does not prove real Keyguard success, StrongBox behavior, Android AtomicFile crash recovery, TalkBack spoken navigation or Pixel 9 Pro compatibility. Those remain separate hardware/accessibility/security gates. Exact-head CI is pending when this specification is first committed.


## Runtime harness correction

The first emulator attempt successfully launched the owner trust Activity. Its UIAutomator dump showed the initial status message is below the ScrollView viewport and is not included in the first hierarchy snapshot. The helper was corrected to validate the visible title, trust state, labels and fields without requiring that off-screen status. The action-specific status assertions remain. This is a test-harness correction; Android app behavior was not changed. Exact-head rerun is pending.


## QA-020B2 harness correction — populated-field cancellation (2026-11-05)

The exact-head emulator run 42047955324 reached the owner trust Activity and passed launcher navigation, empty-input preview refusal, insecure-device credential denial, and all preceding QA-005 checks. It failed only at the Cancel assertion. Artifact 13425996691 showed two harness assumptions were wrong: UIAutomator exposes an empty EditText's hint in its text attribute, and the post-cancel hierarchy was still scrolled to the bottom, so only three of five fields were present. The Android Activity's cancelPending(true) path explicitly clears all five EditText values; no application defect was demonstrated.

The harness is strengthened rather than weakening the assertion. It now enters five fixed, deliberately invalid, non-secret dummy strings into the five fields, verifies those exact values, invokes Cancel, scrolls to the top, and requires all five EditText nodes to return to their exact empty-field hints while the trust-state label remains unchanged. It never previews or confirms the dummy material, never supplies a valid key/fingerprint/signature, and never enters a credential. This remains a disposable emulator-only test and does not prove successful Keyguard confirmation, StrongBox, physical Pixel 9 Pro behavior or production safety.


### QA-020B2 snapshot split

The corrected smoke harness captures the Cancel result immediately while the lower status TextView is visible, then scrolls to the top for the five empty-field hints and trust-state comparison. These assertions use separate hierarchy snapshots because the status and all five fields do not share a single scroll viewport.


## Exact-head QA-020B2 acceptance — 2026-11-05

The final QA-020B2 correction at source/test head 9eb814c3a2176f9be552372c5d6f078774edb7dd passed the complete exact-head validation set:

- Phase 1 push run 42051143160 and PR run 42051155411: PASS. Both reported 416 Python tests passed; Android manifest security gate passed; Gradle :app:testDebugUnitTest and :app:assembleDebug passed; repeat debug APK was byte-identical within each runner; strict dependency verification and the modified-artifact negative control passed.
- CI-003 push run 42051143237 and PR run 42051155321: PASS. Independent runners produced byte-identical unsigned APKs (2,196,905 bytes, 13 entries; SHA-256 c58ac03288ff210c03036645ee26e5c70925972b4b7356567c3021b6e6031d1e), identical normalized contents (b11c9f6ab88743d690dfa556f4f086126bbd8a1165aaa02f29c5c81cf718b396), runtime inventory (a8a1b16dd1cefb90d14426c477e924a3710c7a160def52a2ece3a6d55c266e44) and SPDX runtime SBOM (c4d577f316439ed5445e5fd553a01c4eea0c54c135420b416792bbaad07a1b3d). Both verifiers reported reproducible=true and release_ready=false.
- QA-005 disposable x86_64 emulator PR run 42051155383: PASS. QA-005, QA-006 through QA-010, QA-013 and QA-020B2 passed. QA-011 reported blocked_service_disabled (not TalkBack acceptance); QA-012 passed structural semantics only (not spoken TalkBack). QA-020B2 artifact 13426024605 contains the five synthetic invalid field values, separate Cancel-status snapshot and post-cancel empty-hint snapshot. The log records: all five fixed invalid dummy fields were cleared; trust state unchanged; launcher restored.

The original QA-020B2 failure at run 42047955324 was a hierarchy-harness defect, not an application defect: empty EditText nodes expose hints as their UIAutomator text and the lower viewport contained only three fields. The corrected test proved all five fields were populated with fixed invalid test strings, then cleared by Cancel. It did not preview or confirm those values, enter credentials, mutate the trust store, grant permissions or invoke an executor.

This evidence is disposable-emulator-only. It does not establish Pixel 9 Pro StrongBox/Keyguard behavior, physical crash recovery, spoken TalkBack, independent security approval or production readiness. No milestone is complete; M1/M2/M6 remain IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT ACCEPTED, M7 BLOCKED and M8 BLOCKED. The upstream shared SKILL.md remains unverified and is not claimed as installed.
