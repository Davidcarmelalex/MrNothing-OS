# AGENT-004E — Synthetic end-to-end owner-consent flow harness

**Scope:** test-only integration coverage on `feat/phase1-agentic-phone`.
**Status:** synthetic issuer → P-256 signature → verifier → durable replay path covered; production trust and execution remain unimplemented.

## Purpose

AGENT-004A, AGENT-004B and AGENT-004C were previously tested as separate primitives. This harness exercises their Python host-side integration contract in one deterministic test fixture:

1. A test-only `AuthenticatedOwnerSession` and in-memory registry provide the issuer's trusted inputs.
2. AGENT-004C issues a bounded challenge and returns the enrolled P-256 public key.
3. An ephemeral software P-256 key, generated only inside the test, signs the canonical challenge bytes.
4. The test serializes the exact version-1 payload/signature envelope.
5. AGENT-004A verifies transport state, exact challenge binding, public-key signature and challenge freshness.
6. The existing SQLite `DurableReplayLedger` atomically consumes the consent nonce.
7. The only success result is `ADMITTED_NO_EXECUTION`.

## Coverage

The integration tests cover successful no-execution admission, replay after reopening the SQLite ledger, concurrent duplicate submission, signature tampering, wrong signing key, unauthenticated transport, session-expiry capping, owner/device mismatch, registry failure and replay-ledger failure.

The suite intentionally uses synthetic identifiers, a fake in-memory registry, an explicitly asserted transport boolean and ephemeral software test keys. It does not connect to an Android activity, command router, accessibility service, network socket, production registry or device.

## Security boundaries

- Passing this suite does **not** prove that `AuthenticatedOwnerSession` came from an authenticated transport. That object is constructible by any Python caller; AGENT-004D must establish provenance before creating it.
- Passing this suite does **not** prove Android StrongBox signing. The test signer is software-generated and exists only in the test process. Physical key authentication requires separate Android/runtime and Pixel evidence.
- Passing this suite does **not** prove enrollment attestation, public-key provenance, rate limiting, distributed replay protection, or durable session revocation.
- `ADMITTED_NO_EXECUTION` is a verifier decision only. It must never be interpreted as permission to run an Android action. The command executor remains disconnected.
- The harness does not contact the network or request Android permissions.

## Acceptance evidence

The repository Python preflight discovers this file through unittest discovery. The exact-head GitHub Actions Python job must pass. Android/JVM tests remain a separate workflow gate; emulator QA does not exercise the physical StrongBox signer. Independent security review remains required. Keep M3 partial and M6 in progress.
