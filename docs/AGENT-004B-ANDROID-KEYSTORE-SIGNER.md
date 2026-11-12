# AGENT-004B — AndroidKeyStore per-use P-256 signer

**Scope:** feat/phase1-agentic-phone  
**Status:** isolated signer primitive and JVM envelope tests added; no trusted challenge issuer, public-key registry, executor integration or physical StrongBox validation.

## Purpose

Use the existing mrnothing_owner_consent_p256_v1 AndroidKeyStore alias for a one-use P-256 ECDSA signature over the AGENT-004A canonical payload. Do not generate, rotate, replace or export a key in this task.

## Preconditions and signing sequence

1. Require Android 12+ and a foreground, non-finishing Activity on the main thread.
2. Require OwnerCredentialSafetyGate.isSafe(activity).
3. Require OwnerKeystorePreflight.inspectExisting() to report the existing key as P-256, StrongBox-backed, owner-authentication-required and per-use.
4. Load only the fixed AndroidKeyStore alias; fail closed if the entry or certificate is absent.
5. Canonicalize the bounded OwnerConsentFields payload and initialize SHA256withECDSA with the non-exportable private key.
6. Bind the initialized Signature to the framework BiometricPrompt.CryptoObject.
7. Request only BIOMETRIC_STRONG | DEVICE_CREDENTIAL, matching the authenticators allowed when the key was enrolled. No weak-biometric or software-key fallback is present.
8. After onAuthenticationSucceeded, re-check activity/device safety, sign, verify the produced signature locally against the alias certificate, and emit the AGENT-004A envelope.
9. Cancellation, prompt errors, missing crypto objects, unsafe state and keystore errors produce refusal. A process-level guard permits only one signing prompt at a time.

The system prompt displays the requested action, device identifier and session identifier. setConfirmationRequired(true) is a system hint, not a guarantee that every modality will require an extra confirmation gesture.

## Manifest policy

The only new manifest permission is android.permission.USE_BIOMETRIC. The source-manifest gate now allowlists exactly this permission, rejects duplicates and continues rejecting every unreviewed permission. No accessibility, overlay, screen-capture, contacts, telephony, SMS, location or storage permission is added.

## Explicit non-goals and limitations

- No challenge issuer or authenticated transport is implemented here.
- No trusted device/owner registry is implemented; the signer accepts typed fields and must only be called by a future trusted coordinator, never directly from model/tool input.
- This signer does not grant Android permissions, read screens, navigate UI or execute commands.
- The Python verifier remains responsible for matching the host-issued challenge, expiry and durable one-use nonce consumption.
- The signed-64-bit timestamp correction is tracked in open draft PR #7 and is not yet part of this development-branch baseline.
- JVM tests exercise envelope formatting only. They do not exercise AndroidKeyStore, BiometricPrompt, StrongBox, hardware authentication or Pixel 9 Pro behavior.
- A real Pixel 9 Pro test must prove enrollment, per-use prompt binding, credential fallback, cancellation, signature verification and refusal when StrongBox is unavailable.

## Tests added

- Exact canonical payload embedding.
- Unpadded Base64URL signature encoding.
- DER signature length bounds.
- Invalid challenge rejection.
- Source checks for fixed alias, StrongBox preflight, CryptoObject binding, cancellation and no executor wiring.
- Manifest permission allowlist and duplicate/unreviewed permission rejection.

## Acceptance still required

Independent security review; trusted challenge issuer and device/owner registry; explicit user-facing challenge preview; authenticated transport; host-side freshness/replay checks; Android instrumentation tests on supported API levels; and physical Pixel 9 Pro StrongBox validation. Keep M3 partial and M6 in progress. Do not connect to CommandRouter or HERMES execution until a separately reviewed supervised state machine enforces the complete protocol.
