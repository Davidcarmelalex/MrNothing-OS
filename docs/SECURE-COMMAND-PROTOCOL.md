# Secure command protocol — engineering prototype

This module adds canonical JSON HMAC-SHA256 request signatures, timestamps, constant-time signature comparison, and a bounded in-memory replay cache.

**It is not yet a production pairing protocol or network server.** The verification key must be generated and stored outside the repository. Never place owner credentials, tokens or device secrets in an LLM prompt. An HMAC key is shared by both sides; production should consider asymmetric device-bound keys, Android Keystore, authenticated enrollment, key rotation and revocation.


## Strict canonical payload boundary (SEC-015)

The signed admission path accepts only exact JSON-native values: objects with
string keys, arrays, strings, booleans, null, integers and finite floats.
Python-only tuples, custom containers, non-string object keys, NaN/Infinity,
more than 32 nested levels, more than 4,096 total JSON nodes, or more
than 16,384 aggregate string/key code points are rejected before signature
verification. Action names are limited to 128 characters. The canonical signed
envelope is capped at 8,192 bytes. These limits bound structural and scalar
preflight work and prevent different runtimes from interpreting Python-only
values differently.

This is still a transport-neutral admission prototype. The SQLite replay
ledger is single-host, and the caller must supply an authenticated transport
identity and a unique device key. No command is executed by this module.

## Owner-UI capability verifier (SEC-014B)

core/owner_consent_verifier.py is a separate in-memory admission prototype
for one-use read_screen, navigate and scroll capabilities. It binds each
capability to the configured device, owner, session, action, random process
epoch and a maximum 30-second monotonic-time window. It never issues
capabilities, grants Android permissions or executes actions.

The verifier bounds both consumed nonce markers and revoked session IDs. A
duplicate revocation is idempotent. If a new revocation arrives after the
revocation registry reaches its configured capacity, the verifier enters a
deny-all state for the current epoch; it does not silently omit the requested
revocation. A new process epoch invalidates every prior-process capability.
The revocation registry itself is not persistent, and the HMAC key/context
must still come from a trusted host. This is not the production Android
Keystore signing or authorization boundary.

## Envelope
```json
{"command_id":"unique-id","issued_at":1000,"action":"get_battery","arguments":{},"signature":"hex-hmac"}
```

## Required execution sequence
1. Authenticate transport and owner identity.
2. Verify signature, freshness and replay protection.
3. Validate action and arguments against the Hermes allowlist.
4. Apply device-side authorization and request human approval for sensitive actions.
5. Execute through constrained Android APIs and record a privacy-preserving audit result.

**Limitations:** ReplayGuard state is process-local and resets on restart; no persistence or distributed coordination. No network endpoint is deployed. Do not claim full security or device pairing based on these tests.
