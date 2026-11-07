# SEC-017 — Signed durable owner/device enrollment registry

**Branch:** \`feat/phase1-agentic-phone\`  
**Scope:** Host-side registry only. No listener, public endpoint, Android client-certificate provisioning, permission grant or command execution.

## Purpose

AGENT-004C and AGENT-004D previously consumed separate registry interfaces. A transport certificate could therefore be mapped independently from the per-use owner-consent P-256 public key. SEC-017 implements both interfaces over one durable SQLite owner/device record and binds each lookup to a credential generation.

## Signed enrollment authority

- The registry is configured with one externally pinned Ed25519 public key in canonical SPKI DER and a matching authority key identifier.
- The corresponding private key is intended to remain offline. No private key, production key or default authority is embedded in this repository.
- The authority signs a canonical JSON payload. The envelope is bounded to 4 KiB, rejects duplicate JSON keys and non-finite numbers, and requires canonical unpadded Base64URL signature/key encodings.
- Statements are valid for at most five minutes and must be current according to a trusted host clock.
- Payload timestamps and credential generations are bounded to signed 64-bit integer ranges.
- Only P-256 canonical SPKI DER is accepted for the owner-consent signing key.
- The mTLS credential is represented by the SHA-256 fingerprint of the exact leaf-certificate DER bytes.

Operations:

1. **enroll** — first record for a device, generation 1.
2. **rotate** — replace both transport certificate and consent public key together, advancing the generation exactly once.
3. **revoke** — signed revocation of the current credential pair, advancing the generation and retaining history.

The same transport fingerprint or consent public key cannot be bound to another device. A rotation cannot silently retain either half of the old credential pair.

## Persistence and failure behavior

- First database creation requires \`initialize(explicit_first_install=True)\` from a trusted provisioning path.
- Existing missing, corrupt, wrong-schema, symlinked or group/world-accessible databases fail closed; normal startup does not recreate or repair them.
- POSIX database files are created with mode 0600.
- SQLite uses a bounded busy timeout, DELETE journal mode and synchronous FULL.
- Enrollment, rotation/revocation state changes and append-only history entries are committed in one \`BEGIN IMMEDIATE\` transaction.
- Unique constraints and generation checks reject duplicate enrollment IDs, stale rotations, reused credentials and concurrent duplicate application.
- Capacity is bounded to 5,000 device records, 8,000 history entries and a 4 MiB database file.

## Integration with AGENT-004C/004D

\`SQLiteOwnerEnrollmentRegistry\` implements both existing registry interfaces:

- \`lookup_active_certificate(fingerprint)\` returns the enrolled owner, device and credential generation for AGENT-004D.
- \`lookup_active_device(device_id)\` returns the same record's P-256 consent public key, transport fingerprint and credential generation for AGENT-004C.

AGENT-004D now places the transport fingerprint and generation into the internally created session. AGENT-004C requires the subsequent consent-registry lookup to match both values. If a rotation occurs between those two lookups, challenge issuance fails with \`CREDENTIAL_GENERATION_CHANGED\` instead of combining credentials from different generations.

## Verification

The new registry suite covers signed enrollment, authority/signature mismatch, expiry/future/overlong statements, duplicate JSON keys, oversized envelopes, malformed fingerprints, digest mismatch, RSA/P-384 rejection, duplicate enrollment, credential uniqueness, exact-generation rotation, signed revocation, re-enrollment after revocation, concurrent duplicate application, file permissions, symlinks, missing databases and corruption without reset.

Two issuer regressions verify that credential-generation snapshots must match across the transport and consent lookups.

Tests use ephemeral Ed25519 and P-256 software keys and synthetic certificate fingerprints. They do not prove StrongBox operation, Android client certificate provisioning, real attestation, secure offline key custody or physical-device behavior.

## Explicit remaining limitations

- No production enrollment-authority public key has been provisioned.
- No owner-approved Android enrollment ceremony signs these statements yet.
- No public or local network endpoint is connected to the registry.
- The registry's history is SQLite-local. Restoring an older whole-database backup can roll back revocation/history; there is no hardware-backed monotonic counter or remote anchor.
- The verifier does not yet re-check the active credential generation at signature-consumption time. A previously issued challenge may remain usable until its maximum 30-second expiry unless a verifier-time registry check is added.
- No rate limiter, operational audit pipeline, Android client-certificate issuance, remote attestation or command executor is connected.

SEC-017 therefore advances M6 evidence but does not complete M3, M4, M6 or any release milestone. Independent security review remains mandatory.
