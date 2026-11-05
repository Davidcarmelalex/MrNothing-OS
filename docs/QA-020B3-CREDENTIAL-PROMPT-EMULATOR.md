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
5. Press Back and require an error callback; cancellation must not be accepted.
6. Open the prompt again, enter only the synthetic test PIN, and require DEVICE_CREDENTIAL_ACCEPTED.
7. Clear the test PIN with locksettings clear --old in an EXIT/INT/TERM cleanup trap.

No adb root, su, fastboot, bootloader unlock, physical device, trust-store commit, permission grant or executor is used. The AVD is disposable and is not an owner device.

## Acceptance and limits

- Static Python gates prove the probe exists only in the debug manifest, requires DUMP, shares the production prompt factory and contains no trust/execution path.
- The runtime workflow must show prompt visibility, cancellation error, successful device-credential result type and test-PIN cleanup.
- This does not exercise SEC-020B1 StrongBox marker/encryption, the full SEC-020B2/B3 trust transaction, Pixel 9 Pro hardware, spoken TalkBack or production readiness.
- If emulator shell locksettings is unavailable, the test must fail closed and report the blocker; it must not escalate privileges or substitute a physical device.
