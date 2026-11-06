# AGENT-004F — deterministic adversarial consent-envelope corpus

**Scope:** test-only hardening on `feat/phase1-agentic-phone`.
**Status:** deterministic parser and signature-mutation corpus added; exact-head CI is the acceptance gate.

## Purpose

Extend AGENT-004A parser coverage without changing production protocol behavior or introducing runtime dependencies. The test corpus uses synthetic identities, a generated software P-256 key, a temporary SQLite replay ledger and fixed test time. It never requests Android permissions or executes actions.

## Coverage

Six deterministic test methods cover:

- Valid pretty-printed JSON and the exact 4,096-byte envelope limit.
- Empty, whitespace-only, NUL, malformed UTF-8, UTF-8 BOM, scalar/list roots, duplicate outer and payload keys, unknown outer fields, non-object payloads, non-string signatures, excessive nesting and oversized envelopes.
- Payload type confusion, changed identity/action/nonce/timestamps, missing fields and unknown fields.
- NaN and positive/negative infinity in signed timestamp fields.
- Invalid Base64URL alphabets, padding, length bounds, noncanonical pad bits and malformed DER signatures.
- A one-character mutation at every position of a valid Base64URL signature, followed by a valid verification proving failed mutations did not consume the nonce.

The tests assert fail-closed admission outcomes; they do not overfit every malformed case to one internal error string unless the parser contract specifically requires it.

## Boundaries

- No production parser code changed.
- No network transport, enrollment registry, Android Keystore, StrongBox, biometric prompt or physical Pixel is exercised.
- The test key is generated in-process and is not an enrolled or production key.
- The positive result remains `ADMITTED_NO_EXECUTION`; this is not permission to invoke an Android action.
- Passing this corpus does not establish authenticated-session provenance, production attestation, distributed replay protection or independent security approval.

Keep M3 partial and M6 in progress. The next security integration gate remains AGENT-004D: authenticated transport provenance and a trusted enrollment registry.
