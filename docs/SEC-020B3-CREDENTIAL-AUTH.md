# SEC-020B3 — device-credential-only system authentication

**Status:** implementation submitted on `feat/phase1-agentic-phone`; exact-head CI and emulator rerun pending.

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
enrollment service, command router or executor is connected. Existing synchronous
trust-store I/O remains a separate lifecycle-safe serialization review item.

## Verification requirements

- JVM policy tests cover API 29 refusal, API 30+ support, device-credential
  acceptance, and biometric/unknown/unexpected result rejection.
- Python source gates enforce credential-only authenticator configuration,
  removal of the deprecated Intent/result flow, and cancellation ordering.
- Exact-head Phase 1 and CI-003 workflows must pass.
- QA-005 must rerun on its disposable API 35 x86_64 emulator. Its unsecured
  emulator must remain denied before any credential prompt; this does not prove
  a successful system credential interaction.
- Independent security review and physical Pixel 9 Pro validation remain
  separate required gates.
