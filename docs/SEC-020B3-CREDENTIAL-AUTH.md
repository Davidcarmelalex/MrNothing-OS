# SEC-020B3 — device-credential-only system authentication

**Status:** SEC-020B3 implementation and exact-head CI accepted. QA-020B3 adds a debug-only disposable-emulator probe for the shared platform prompt; it does not exercise the StrongBox-backed trust-store commit.

## Scope

Replace the deprecated `KeyguardManager.createConfirmDeviceCredentialIntent` plus
`startActivityForResult` flow in SEC-020B2 with the platform
`android.hardware.biometrics.BiometricPrompt` API. This implementation deliberately
uses the platform API rather than adding a new AndroidX dependency, keeping the
strict Gradle dependency-verification graph unchanged.

## Authentication policy

- Requires Android API 30 or later. API 29 fails closed; there is no deprecated
  Keyguard Intent fallback.
- Calls `BiometricManager.canAuthenticate(DEVICE_CREDENTIAL)` before showing UI.
- Configures `setAllowedAuthenticators(DEVICE_CREDENTIAL)` as the only allowed
  authenticator. It does not OR in biometric authenticators and sets no negative
  button or software fallback.
- Accepts the callback only when `AuthenticationResult.authenticationType`
  equals `AUTHENTICATION_RESULT_TYPE_DEVICE_CREDENTIAL`. Biometric, unknown,
  unexpected and pre-API-30 results are rejected.
- Requires the existing secure/unlocked/interactive device preflight before
  prompting and repeats it after the callback.

The API 30 gate is compatible with the Pixel 9 Pro's Android 14+ launch baseline.
Actual Pixel credential UI behavior remains unverified until physical-device testing.

## Transaction and lifecycle

The existing one-shot 30-second confirmation binding remains bound to the
imported-field digest, trust mode and trust-store snapshot. The callback must
still consume that state, reparse the import, reinspect the trust store, compare
the binding, prepare a SEC-020A Ready decision and commit through SEC-020B1.

A `CancellationSignal` is retained while the prompt is active. Explicit cancel
and Activity destruction revoke the one-shot state and clear the pending binding
before canceling the signal, so any resulting late callback is inert. Prompt
errors consume the request as denied. Authentication failure never commits.

## Security boundary

No Android permission was added or removed. No authority material, private key,
credential or secret is stored in the callback. No network, permission grant,
enrollment service, command router or executor is connected. The debug-only QA probe is deliberately isolated from the trust store. Existing synchronous trust-store I/O remains a separate lifecycle-safe serialization review item.

## Verification requirements

- JVM policy tests cover API 29 refusal, API 30+ support, device-credential
  acceptance, and biometric/unknown/unexpected result rejection.
- Python source gates enforce credential-only authenticator configuration,
  removal of the deprecated Intent/result flow, and cancellation ordering.
- Exact-head Phase 1 and CI-003 workflows must pass.
- QA-005 first runs QA-020B2 on the fresh unsecured API 35 x86_64 emulator and verifies denial before a prompt. QA-020B3 then configures a fixed test-only PIN through ordinary adb shell (uid 2000), exercises cancellation and successful DEVICE_CREDENTIAL callback on a debug-only probe using the same prompt factory as production, and clears the PIN in an EXIT trap. It does not invoke the trust store or prove StrongBox-backed commit.
- Independent security review and physical Pixel 9 Pro validation remain
  separate required gates.


## QA-020B3 prompt-runtime evidence boundary

The production Activity and the debug-only probe share OwnerCredentialPromptFactory, which configures only BiometricManager.Authenticators.DEVICE_CREDENTIAL. The probe Activity is declared only in src/debug/AndroidManifest.xml, protected by android.permission.DUMP, and absent from the main/release manifest. Its source has no trust-store, permission-grant, command-router or executor reference.

On the disposable API 35 x86_64 AVD, QA-020B3 sets a fixed synthetic PIN as ordinary adb shell UID 2000, proves the system PIN prompt appears, verifies Back/cancel returns an error rather than success, then verifies the platform callback reports AUTHENTICATION_RESULT_TYPE_DEVICE_CREDENTIAL after the test PIN. An EXIT/INT/TERM cleanup clears the test PIN. The script never runs adb root, su, fastboot, flashing or physical-device commands.

This validates the shared prompt factory and Android system UI callback only. It does not bypass or mock the StrongBox-backed trust store, commit an authority, establish Pixel 9 Pro behavior, or replace independent security review.
