# SEC-018 — Verifier-time paired-enrollment revalidation

**Branch:** `feat/phase1-agentic-phone`  
**Scope:** P-256 consent admission only. No action executor, permission grant, network listener or device integration.

## Problem

SEC-017 paired the mTLS certificate fingerprint and per-use P-256 consent key in one signed durable owner/device record. AGENT-004D checks the transport certificate when issuing a challenge, and AGENT-004C checks the paired generation during challenge issuance. Before SEC-018, AGENT-004A verification did not re-read that record when consuming a signature. A credential could therefore be revoked or rotated after challenge issuance while an unexpired signed capability remained admissible.

## Change

`verify_and_consume` now requires the trusted host to provide:
- the paired enrollment registry;
- the authenticated session's transport-certificate SHA-256 fingerprint;
- the credential generation captured by AGENT-004D.

After validating the P-256 signature, the verifier reads the active enrollment and checks exact owner/device identity, consent SPKI bytes, transport fingerprint, credential generation and active state. It then reserves the nonce in the existing durable replay ledger and reads the enrollment again. A change observed on the second read fails closed; the nonce remains consumed, so the same capability cannot be retried after restoring a credential.

Registry exceptions, missing/revoked records, mismatched identities, key rotation, certificate rotation and generation mismatch all deny admission.

## Tests

- Revocation after challenge issuance is rejected before nonce consumption; restoring the same active enrollment permits the still-unused challenge.
- Transport certificate/generation rotation rejects the old session snapshot.
- Consent-key rotation rejects the old enrolled public key.
- Registry outage fails closed without consuming the nonce.
- Revocation observed between the pre- and post-reservation checks fails closed and leaves the nonce consumed.

The parser mutation and synthetic end-to-end suites now supply a paired enrollment fixture to the verifier.

## Security boundary and remaining limitation

This is a verifier-time double-check around a separate SQLite replay-ledger transaction. It is **not** an atomic transaction across enrollment state and replay consumption. A revocation immediately after the final registry read can still race with a future executor. No command executor exists, and the only positive result remains `ADMITTED_NO_EXECUTION`. Before any executor is implemented, current credential generation must be revalidated atomically with action admission (preferably in the same transactional store or under a single admission lock spanning both state changes).

All keys/certificates in tests are synthetic software credentials. This does not establish StrongBox, remote attestation, production authority-key custody, Android client provisioning, physical Pixel 9 Pro behavior or production readiness. Independent security review remains pending. The upstream shared `SKILL.md` remains unverified; this document is project-specific.
