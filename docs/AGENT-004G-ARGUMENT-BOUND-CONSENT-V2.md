# AGENT-004G — Argument-bound owner consent protocol v2

**Status:** implementation submitted; exact-head CI and independent review pending. Cross-platform canonicalization, host challenge issuance and signature verification are isolated admission primitives. No Android action capability, device executor, listener or production caller is connected.

## Security objective

Protocol v1 signs owner/device/session/action/nonce/time but does not sign action arguments. V1 therefore remains restricted to the existing read_screen empty-argument no-op capability path. V2 adds a domain-separated SHA-256 digest of a strict canonical argument object to the signed challenge.

The owner-visible Android BiometricPrompt description displays the exact canonical JSON argument object used to calculate the digest before the per-use signature is emitted. The signer still only signs; it does not execute an action or grant a permission.

## V2 wire change

V2 adds exactly one signed payload field: arguments_sha256, the lowercase hexadecimal SHA-256 of the domain-separated canonical action arguments.

Digest input:

    mrnothing-owner-action-arguments-v2\0 + action ID + \0 + canonical ASCII JSON

The shared fixture android/app/src/test/resources/owner-consent-v2.properties is consumed by Python and Kotlin tests. V1 canonical bytes and the v1 fixture remain unchanged.

## Initial closed argument schemas

| Action | Exact arguments |
|---|---|
| read_screen | {} |
| navigate | {"target_package":"com.example.notes"} with a bounded Android package-name pattern |
| scroll | {"direction":"up" or "down","distance_dp":1..1000} |

Unknown keys, extra keys, nested values, wrong primitive types, booleans in integer fields, invalid package names, unknown actions and oversized canonical JSON are rejected. Canonical JSON uses sorted keys, compact separators, ASCII output and no non-finite numbers.

## Current enforcement

- Host challenge issuance computes the v2 digest from the exact action arguments.
- Python challenge validation requires a lowercase 64-character digest for v2 and forbids that field for v1.
- Envelope parsing selects the exact v1 or v2 key set; unknown/missing fields fail closed.
- Signature verification compares every payload field with the host-issued challenge before atomic nonce consumption.
- Kotlin canonicalization recomputes the digest from a closed typed argument model and refuses if it differs from the host digest.
- The Android per-use signer includes the same canonical JSON in the owner-visible system authentication prompt.
- The live mTLS adapter can issue and verify v2 challenges, but verify_and_issue_capability explicitly returns V2_CAPABILITY_NOT_INTEGRATED. The opaque no-op capability path remains v1/read_screen/empty-arguments only.

## Tests added

- Shared v1 and v2 cross-platform fixtures.
- Strict action argument schema and canonical digest tests.
- Signed v2 admission and replay rejection.
- Payload digest tampering rejection without nonce consumption.
- Live synthetic mTLS v2 challenge verification.
- Explicit refusal to mint an action capability from v2 until a separately reviewed capability/argument integration exists.
- Android JVM tests verify v2 canonicalization and envelope encoding; they do not exercise AndroidKeyStore, StrongBox or the system biometric UI.

## Explicit limitations

This is not a production executor or permission integration. No screen capture, navigation, scrolling, accessibility action, package launch, shell, call, message, network listener, remote service, Android runtime permission grant or device-side effect is connected. The v2 capability path remains deliberately disabled. Synthetic keys and certificates are test-only. Independent security review, real Pixel 9 Pro/StrongBox validation and a separately designed atomic final authorization/idempotency reservation remain required before any real executor can be considered.
