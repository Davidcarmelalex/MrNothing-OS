# Secure command protocol — engineering prototype

This module adds canonical JSON HMAC-SHA256 request signatures, timestamps, constant-time signature comparison, and a bounded in-memory replay cache.

**It is not yet a production pairing protocol or network server.** The verification key must be generated and stored outside the repository. Never place owner credentials, tokens or device secrets in an LLM prompt. An HMAC key is shared by both sides; production should consider asymmetric device-bound keys, Android Keystore, authenticated enrollment, key rotation and revocation.


## Strict canonical payload boundary (SEC-015)

The signed admission path accepts only exact JSON-native values: objects with
string keys, arrays, strings, booleans, null, integers and finite floats.
Python-only tuples, custom containers, non-string object keys, NaN/Infinity,
more than 32 nested levels, or more than 4,096 total JSON nodes are rejected
before signature verification. The canonical signed envelope is capped at
8,192 bytes. These limits bound parser/canonicalization work and prevent
different runtimes from interpreting Python-only values differently.

This is still a transport-neutral admission prototype. The SQLite replay
ledger is single-host, and the caller must supply an authenticated transport
identity and a unique device key. No command is executed by this module.

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
