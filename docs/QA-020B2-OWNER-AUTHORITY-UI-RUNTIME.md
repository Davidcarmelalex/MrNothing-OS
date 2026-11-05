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
