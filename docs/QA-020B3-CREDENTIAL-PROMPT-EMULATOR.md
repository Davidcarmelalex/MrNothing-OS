# QA-020B3 — device-credential prompt runtime probe

**Target:** disposable Android API 35 x86_64 emulator only.  
**Purpose:** exercise the exact platform prompt factory used by the production owner-authority Activity.

## Design

- Production OwnerAuthorityTrustActivity and the debug-only probe share OwnerCredentialPromptFactory.
- The factory sets DEVICE_CREDENTIAL as the only allowed authenticator; no biometric OR, negative-button fallback or software fallback is configured.
- The probe is in src/debug only, requires android.permission.DUMP to launch, and is absent from the main/release manifest.
- The probe uses the existing API-level and secure/unlocked/interactive safety gates and checks the platform callback's authenticationType.
- It has no trust-store reference, permission grant, network, command router or agent executor.

## Runtime procedure

1. Require ANDROID_SERIAL to match emulator-*, ro.kernel.qemu=1, API 30+, and ordinary adb shell UID 2000.
2. Configure a fixed test-only PIN on the freshly created AVD using locksettings set-pin; do not overwrite an existing credential.
3. Launch the debug-only probe.
4. Open the system credential UI and verify that the PIN/password prompt is visible.
5. Send an explicit broadcast to the debug-only OwnerCredentialPromptProbeCancelReceiver, protected by android.permission.DUMP. The receiver cancels the probe's active CancellationSignal; require the platform prompt-error callback and verify the credential prompt disappears. No coordinate is guessed and no credential is entered on this path.
6. Open the prompt again, enter only the synthetic test PIN, and require DEVICE_CREDENTIAL_ACCEPTED.
7. Clear the test PIN with locksettings clear --old in an EXIT/INT/TERM cleanup trap.

No adb root, su, fastboot, bootloader unlock, physical device, trust-store commit, permission grant or executor is used. The AVD is disposable and is not an owner device.

## Acceptance and limits

- Static Python gates prove the probe exists only in the debug manifest, requires DUMP, shares the production prompt factory and contains no trust/execution path.
- The runtime workflow must show prompt visibility, cancellation error, successful device-credential result type and test-PIN cleanup.
- This does not exercise SEC-020B1 StrongBox marker/encryption, the full SEC-020B2/B3 trust transaction, Pixel 9 Pro hardware, spoken TalkBack or production readiness.
- If emulator shell locksettings is unavailable, the test must fail closed and report the blocker; it must not escalate privileges or substitute a physical device.


## QA-020B3 cancellation-harness correction — 2026-11-05

Exact-head run [42067990751](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42067990751) passed the debug build, emulator boot, QA-005 through QA-013, and QA-020B2, then failed in the QA-020B3 cancellation assertion. Artifact [13434834475](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42067990751/artifacts/13434834475) shows the platform credential prompt opened successfully. Sending KEYCODE_BACK left the SystemUI credential surface visible for all 25 status polls, so the app status TextView was correctly absent from the captured hierarchy. The test PIN was cleared successfully by the EXIT cleanup trap.

The captured SystemUI hierarchy exposes a clickable full-screen background node (com.android.systemui:id/background) with content description Tap to cancel authentication. The corrected helper requires that exact package, resource ID, class, description, clickability and visibility, then derives a safe tap point strictly above the credential panel. On the captured API 35 hierarchy it resolves to 540 31. The smoke test now taps that explicit system cancellation surface, waits for the app's prompt-error callback, and only then repeats the prompt for the test-PIN success path.

Three additional parser tests cover safe-point derivation, missing/ambiguous targets, non-clickable surfaces and absence of a safe margin. The local focused suite passed 14 tests; shell syntax and Python compilation passed; the actual failed-run hierarchy resolved to 540 31. These local checks do not replace the required exact-head GitHub emulator rerun. The initial failure is a test-harness cancellation-method defect; it does not establish an application authentication defect.


## QA-020B3 cancellation harness correction — 2026-11-06

Exact-head QA-005 run 42095108551 at 8b875fd23d86df525f17d942b74d684682064de2 failed only at cancellation. The SystemUI prompt opened; side-gutter point (133,1033) left the prompt visible for all 25 status polls while the credential field remained empty. The disposable test PIN cleanup completed; no credential was submitted.

The coordinate-based SystemUI tap is withdrawn. A debug-only receiver protected by android.permission.DUMP now cancels the probe's active CancellationSignal. The runtime gate requires the prompt-error callback and prompt disappearance, then reopens the prompt and checks the test-only PIN returns DEVICE_CREDENTIAL_ACCEPTED. This is a programmatic cancellation-signal test, not proof that a user tap on SystemUI's outside-cancel surface works; that separate interaction remains unverified and requires an accessibility-action/UIAutomator test. The receiver/control are debug-only and have no trust-store, permission-grant, network, command-router or executor path. Exact-head CI and emulator rerun remain required.
