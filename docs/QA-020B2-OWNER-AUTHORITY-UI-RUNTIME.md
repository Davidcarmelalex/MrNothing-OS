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
