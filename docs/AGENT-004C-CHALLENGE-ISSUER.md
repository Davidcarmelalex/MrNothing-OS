# AGENT-004C — Host-side owner-consent challenge issuer

**Scope:** bounded Python library primitive on feat/phase1-agentic-phone. This is not a network service, enrollment authority, or command executor.

## Implemented contract

The issuer accepts three host-controlled inputs: a transport-adapter session assertion, a read-only enrolled-device registry, and a trusted host timestamp. It only issues challenges for the existing allowlisted screen actions: read_screen, navigate, and scroll.

- Generates a 128-bit nonce with Python secrets.token_hex(16) by default.
- Requires a canonical P-256 (secp256r1) SubjectPublicKeyInfo DER key from the registry.
- Binds owner ID, device ID, session ID, action, nonce, issue time and expiry.
- Caps challenge lifetime at 30 seconds and never lets a challenge outlive its authenticated session.
- Rejects invalid, inactive, mismatched, unsupported or unavailable registry records.
- Rejects invalid clocks, session timestamps, nonce output and non-P-256 keys.
- Keeps the existing verifier's SQLite DurableReplayLedger responsible for atomic one-use consumption.

## Trust boundary and limitations

AuthenticatedOwnerSession is a frozen data-transfer object, not an unforgeable authentication token. Any code in the Python process can construct it. The caller must create it only after a trusted transport adapter authenticates the peer and validates a live server-side session. Never populate it from request JSON, an LLM, or a tool result.

OwnerConsentRegistry is an interface only. No persistent registry implementation, enrollment endpoint, certificate-chain/attestation verifier, device revocation service, authenticated network transport, rate limiter, audit log, or caller integration is included. The issuer validates public-key type and canonical DER encoding, not the provenance of the key. Registry provenance must be established by a separately reviewed enrollment system.

The issuer is stateless. A cryptographically random nonce is returned with the challenge; the existing verifier consumes it atomically in the durable replay ledger after signature and challenge matching. The issuer does not grant Android permissions or execute actions.

## Acceptance evidence

The new unit tests cover valid challenge binding, 128-bit nonce format, session-expiry capping, signed-64-bit boundary behavior, expired/future sessions, invalid identifiers and clocks, unsupported actions, nonce-source failure, unknown/inactive/mismatched devices, registry failure, and RSA/P-384/malformed key rejection.

These tests do not prove transport authentication, hardware attestation, persistent registry behavior, or Pixel hardware operation. Keep M3 partial and M6 in progress. Independent security review remains required.
