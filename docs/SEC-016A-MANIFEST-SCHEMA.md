# SEC-016A — Trust-manifest structural schema and parser

**Status:** Implemented on a scoped feature branch; independent security review and cryptographic verifier remain pending. **No production roots, update-signing keys, or device identity material are included.**

## Purpose

Provide a deterministic, bounded parser for the signed Android attestation trust-bundle envelope described by SEC-016. The parser is an input-validation boundary only. A successful parse returns an explicitly **unverified** data structure; it does not establish trust or authorize enrollment, commands, or device actions.

## Version 1 envelope

The top-level JSON object has exactly these fields:

| Field | Rule |
| --- | --- |
| schema | mrnothing.android-attestation-trust-bundle |
| schema_version | integer 1 (booleans rejected) |
| bundle_version | positive signed-64-bit integer; caller must compare with persisted anti-rollback state |
| issued_at, not_before, not_after | UTC timestamps in exact YYYY-MM-DDTHH:MM:SSZ form; issued_at <= not_before < not_after |
| signing_key_id | lowercase identifier, 1–64 characters |
| roots | 1–8 unique root entries |
| signature | exactly algorithm and value; Ed25519 and canonical Base64 of 64 bytes |

Each root entry has exactly id, certificate_der and sha256. Certificate bytes are canonical Base64, 1–16 KiB each, 64 KiB aggregate DER maximum. The SHA-256 digest is recomputed over the decoded DER bytes. Root identifiers and fingerprints must be unique.

## Signature input

The detached signature covers the complete manifest object with the signature property removed. Canonical payload bytes are UTF-8 JSON with recursively sorted object keys, no insignificant whitespace, no ASCII escaping of valid Unicode, and no floating-point values. The signing_key_id remains inside the signed payload.

The update-signing key must be selected from an independently pinned key set, not nominated by this manifest. This parser only returns the canonical bytes and signature; it does **not** perform Ed25519 verification. No caller may treat ParsedTrustManifest as verified.

## Resource and ambiguity limits

- Manifest input: 256 KiB maximum.
- JSON nesting: 12 levels; JSON values: 1,024 nodes; aggregate text: 131,072 characters.
- Duplicate JSON keys, unknown/missing fields, non-finite numbers, floating-point values, non-canonical Base64, malformed UTF-8/Unicode, oversized integers, and unsupported schema/signature versions are rejected.
- Timestamps are parsed for format and ordering only. Current-time validity, revocation, root rotation, and rollback persistence are separate gates.

## Explicit non-goals

This implementation does not parse or validate X.509 DER, compare SPKI fingerprints, verify the Ed25519 signature, pin or rotate update-signing keys, perform PKIX path validation, evaluate Android KeyDescription, challenge freshness, verified boot, revocation, owner identity, or consent. The synthetic test bytes are not valid certificates and must never be used as trust anchors.

## Tests

tests/test_attestation_trust_manifest.py covers canonicalization, duplicate keys, strict types, timestamps, root fingerprint consistency, Base64 and size limits, duplicate roots, signature shape, and version monotonicity. All certificate and signature values are synthetic placeholders; no cryptographic acceptance is claimed.

## Next gate

Implement the cryptographic verifier using an independently provisioned update-signing public key and a real X.509 parser, then add signed synthetic test vectors. Obtain independent security review before any root bundle is consumed by production code.
