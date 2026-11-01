# Secure command protocol — engineering prototype

This module adds canonical JSON HMAC-SHA256 request signatures, timestamps, constant-time signature comparison, and a bounded in-memory replay cache.

**It is not yet a production pairing protocol or network server.** The verification key must be generated and stored outside the repository. Never place owner credentials, tokens or device secrets in an LLM prompt. An HMAC key is shared by both sides; production should consider asymmetric device-bound keys, Android Keystore, authenticated enrollment, key rotation and revocation.

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
