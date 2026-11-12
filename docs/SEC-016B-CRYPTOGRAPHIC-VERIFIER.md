# SEC-016B — Cryptographic trust-manifest verifier

**Status:** Implemented on the SEC-016A scoped branch; CI and independent security review are required. This is not production trust-anchor provisioning.

## Scope

The verify_trust_manifest function authenticates the SEC-016A canonical manifest payload using Ed25519 and an update-signing public key supplied by the caller from an independent trust channel. It rejects unknown key IDs without fallback, invalid key lengths, bad signatures, expired/not-yet-valid manifest windows, and equal/older bundle versions.

After signature verification, each root entry is parsed as X.509 DER and must round-trip as DER, contain BasicConstraints with ca=true, and contain KeyUsage with key_cert_sign=true. This is deliberately fail-closed.

## Key provenance and dependency

- The manifest cannot nominate or introduce its own update-signing key.
- The caller supplies a mapping from key ID to raw 32-byte Ed25519 public key.
- Key pinning, provisioning, rotation and recovery are outside this module. No production public key is embedded.
- CI installs the exact cryptography 50.0.2 test/runtime primitive version from requirements-security-ci.txt; this pin must be updated only through reviewed dependency maintenance.

## Anti-rollback boundary

The verifier requires bundle_version > current_version, but current_version is a caller-provided snapshot. This function does not persist or atomically advance rollback state. A later storage task must reserve/advance the version transactionally only after successful signature verification and policy acceptance; crashes and concurrent updates must fail closed.

## Explicit non-goals

This implementation does not perform PKIX path building or validation, verify a root's self-signature, process intermediate certificates, enforce name constraints/policies, check CRLs/OCSP, validate Android KeyDescription, challenge freshness, device identity, verified-boot state, owner consent, or authorize commands. CA-shape validation is not proof that a certificate is an official Android attestation root. Synthetic certificates and ephemeral test keys are never production trust material.

## Regression coverage

Synthetic signed vectors cover valid signatures, tampering, wrong and unknown keys, key length, replay/rollback, time-window rejection, malformed DER, non-CA certificates, missing KeyUsage and missing keyCertSign. No official Android trust roots are included.

## Acceptance gates

1. Python CI passes with the pinned cryptography dependency.
2. Independent security review confirms the canonical payload is exactly the parser's signed representation and the pinned-key map cannot be sourced from the manifest.
3. A separate PKIX implementation task adds chain validation and Android attestation extension policy.
4. A separate durable-state task adds atomic anti-rollback persistence and concurrency/restart/corruption tests.
5. No production consumer is enabled until independent approval and authoritative key/root provenance exist.
