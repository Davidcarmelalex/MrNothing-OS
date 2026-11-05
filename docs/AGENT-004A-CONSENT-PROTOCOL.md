# AGENT-004A — Cross-platform owner-consent protocol primitive

**Scope:** `feat/phase1-agentic-phone` only.
**Status:** verifier and canonicalization primitive implemented; Android signing and production integration remain blocked.

## Purpose

Replace the HMAC-only test prototype as the future Android owner-consent wire format with a versioned P-256 ECDSA capability envelope. The Android enrollment code already creates a non-exportable StrongBox-backed P-256 key after local owner credential confirmation. This task does **not** use that key yet; it defines matching canonical bytes and a Python verification boundary first.

## Wire contract

The signed payload has exactly these fields:

- `version` — integer `1`
- `device_id`
- `owner_id`
- `session_id`
- `action` — one of `read_screen`, `navigate`, `scroll`
- `nonce` — host-issued unpredictable identifier, at least 128 bits
- `issued_at_epoch_ms`
- `expires_at_epoch_ms`

Canonical payload bytes are UTF-8/ASCII JSON with lexicographically sorted keys, no insignificant whitespace, ASCII-only identifier values, and no additional fields. The shared Java-Properties fixture at `android/app/src/test/resources/owner-consent-v1.properties` is consumed by both Kotlin and Python tests.

The outer envelope is JSON with exactly `payload` and `signature`. `signature` is the unpadded Base64URL encoding of the DER-encoded ECDSA P-256 signature over the canonical payload, using SHA-256. The public key is **not** trusted from the envelope.

## Trust boundaries

The verifier requires all of the following from its trusted caller:

1. `transport_authenticated=True`, established outside the model/agent.
2. A `ConsentChallenge` object issued by the trusted host, not parsed from LLM/tool input.
3. The enrolled P-256 SubjectPublicKeyInfo DER from a trusted device/owner registry.
4. `now_epoch_ms` from the trusted verifier clock.

The signed payload must exactly match the host's expected challenge fields. The host challenge issuer must bind device, owner, session, action, issue/expiry times and a cryptographically random nonce. The verifier rejects a challenge lifetime greater than 30 seconds, expired/future challenges, malformed/duplicate JSON keys, unknown fields, non-P-256 keys, invalid signatures and unauthenticated transport. Both epoch-millisecond fields are restricted to `0..Long.MAX_VALUE`; this is required because Kotlin represents them as signed `Long` values. Python rejects out-of-range integers before signing or verification, and the shared test coverage exercises the maximum representable expiry boundary.

After signature verification, the existing `DurableReplayLedger` atomically consumes `(consent-v1:<device_id>, nonce)`, using a separate device namespace so command IDs cannot collide with consent nonces. Its configured retention must be at least 30 seconds. The ledger capacity is still shared, so exhaustion can deny consent admission; it never permits it. Database errors, replay and capacity exhaustion fail closed.

## Implemented files

- `core/owner_consent_protocol.py` — strict envelope parser, canonicalizer, P-256 verifier and durable one-use nonce consumption.
- `android/app/src/main/java/tech/mrnothing/os/OwnerConsentCanonicalizer.kt` — matching pure Kotlin canonicalizer; it does not sign.
- `tests/test_owner_consent_protocol.py` — synthetic P-256 positive/negative, replay, malformed-input and key-type tests.
- `android/app/src/test/java/tech/mrnothing/os/OwnerConsentCanonicalizerTest.kt` — shared canonical fixture and validation tests.
- `android/app/src/test/resources/owner-consent-v1.properties` — single cross-language canonical test vector.
- `requirements-security-ci.txt` — exact CI dependency pin for `cryptography==50.0.2`.

## Explicit non-goals and blockers

This is **not** a production consent issuer or action executor.

- Android StrongBox signing is not implemented.
- The trusted challenge issuer and device/owner public-key registry are not implemented.
- The Kotlin canonicalizer does not invoke Android Keystore.
- The existing HMAC `ConsentVerifier` remains a separate offline prototype; do not treat it as the production Android protocol.
- The new verifier is not connected to `CommandRouter`, HERMES execution, accessibility, screen capture or any device action.
- There is no official production key, attestation root or remote enrollment service in this change.
- Wall-clock timestamps are trusted-host challenge fields; clients cannot choose or extend them. A production issuer must provide a bounded, authenticated challenge and protect its clock assumptions.

## Acceptance gates

1. Python verifier tests pass under the pinned cryptography dependency.
2. Kotlin/JVM canonicalization tests match the exact shared fixture.
3. Full Python preflight, Android/JUnit build and reproducibility checks pass on the exact commit.
4. Independent security review confirms the challenge/public-key provenance, nonce entropy, canonicalization and replay semantics.
5. A later task implements Android Keystore signing with deliberate per-use owner authentication and tests that do not pretend JVM tests exercise StrongBox.
6. A later integration task wires the verifier into a supervised consent state machine without granting Android permissions or executing commands implicitly.

Until gates 4–6 are satisfied, this protocol remains an isolated security primitive. No milestone is marked complete by this work.
