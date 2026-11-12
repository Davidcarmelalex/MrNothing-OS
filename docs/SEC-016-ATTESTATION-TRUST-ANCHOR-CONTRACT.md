# SEC-016 — Android attestation trust-anchor provenance and fail-closed acceptance contract

Status: **DESIGN ONLY — NOT IMPLEMENTED, NOT APPROVED**. Scope: Pixel 9 Pro (`caiman`), M6 security/privacy. Base: `feat/phase1-agentic-phone` at `bd5389693d0d5c31e271766a4bfbaec6b6f9cd90`. This document must not be interpreted as a provisioned production root, validated device, or authorization to execute commands.

## Security boundary

Android key attestation is evidence about a generated key and device state, not proof of user consent or a substitute for authenticated transport. The server must bind an unpredictable single-use enrollment challenge to an authenticated owner session, enrollment transaction, device record and expected public key. A verified certificate chain alone MUST NOT authorize an agent action. Enrollment requires an explicit owner confirmation, auditable key registration and a separate revocable device authorization. Sensitive operations require per-action consent and Android's platform permission checks.

## Trust-anchor supply chain (fail closed)

1. Obtain Google Android hardware attestation root certificates and any official rotation guidance **only** from the current authoritative Android/Google documentation or authenticated distribution channel. Record exact source URL, retrieval UTC timestamp, source document revision, DER SHA-256 fingerprints, certificate subject, serial, SPKI fingerprint, validity and verifier identity in a reviewed manifest. Never copy fingerprints from this design or infer them from test fixtures.
2. Provision a **signed, versioned trust-bundle manifest** through the application's authenticated release/update channel. The bundle contains explicitly approved DER certificates, immutable fingerprints, monotonically increasing policy version, validity window and a revocation/retirement policy. Bundle signature verification uses an independently pinned update-signing key. Do not let a remote model, enrollment request or untrusted network response nominate roots.
3. Treat an absent, corrupt, expired, unsigned, downgraded or unknown bundle as `TRUST_BUNDLE_UNAVAILABLE`; do not fall back to system-wide WebPKI roots, trust-on-first-use, debug fixtures or an arbitrary self-signed leaf. Record failure without leaking certificates or identifiers into analytics.
4. Support controlled overlap for verified root rotation; refuse rollback to older bundle versions, and test recovery after interrupted updates. Revocation and compromise handling must be defined and independently approved before production.
5. Keep test-only synthetic roots under test resources. Add a CI check that no synthetic fixture fingerprint appears in production bundle inputs.

## Verification contract

- Parse strict DER/PEM with explicit maximum bytes, chain length, depth and certificate count; reject duplicate, ambiguous and malformed chains.
- Build and validate a PKIX path to **one of the pinned attestation trust anchors** with certificate signature verification, CA constraints, path length, key usage and validity-time checks. A root appended by a client does not itself confer trust.
- Validate attestation extension against the expected enrollment challenge (constant-time comparison where practical), leaf public key, attestation security level and expected key origin/purpose; reject software-only claims where hardware-backed enrollment is required.
- Check Android verified-boot state, deviceLocked, OS/patch security metadata and the attested application identity against explicit product policy. Do not equate a marketing model string with hardware identity; document what hardware identifiers can and cannot be established from attestation.
- Define freshness, nonce reuse prevention, clock tolerance and explicit fail-closed handling of unavailable revocation signals. No silent acceptance of unknown revocation status under a policy requiring positive status.
- Separate results: `CHAIN_INVALID`, `UNKNOWN_ANCHOR`, `CHALLENGE_MISMATCH`, `KEY_MISMATCH`, `BOOT_POLICY_DENIED`, `ATTESTATION_POLICY_DENIED`, `TRUST_BUNDLE_UNAVAILABLE`. Expose only privacy-safe error codes to callers.
- Preserve an independent owner-authorization, action-policy and consent gate after successful attestation. Never grant root, accessibility, screen capture, dialer or microphone access through attestation alone.

## Objective acceptance tests (synthetic/offline)

| Case | Expected |
| --- | --- |
| Approved pinned root + valid chain + correct challenge and key + compliant boot fields | eligible for *separate* owner consent gate |
| Valid chain to unpinned root | reject |
| Attacker-supplied self-signed root appended to chain | reject |
| Root rotated under signed newer manifest | accept only after manifest signature and policy validation |
| Unsigned, downgraded, corrupted or missing manifest | reject |
| Synthetic test root in production manifest | CI fail |
| Wrong challenge, reused challenge, wrong leaf key | reject |
| Invalid CA/basic constraints, expired intermediate, invalid signature, excessive chain length | reject |
| Unlocked bootloader, unverified boot or disallowed patch level | reject |
| Unsupported/absent extension, unexpected attestation security level | reject |
| Attestation passes but owner consent revoked | no action admitted |
| Update interrupted / rollback attempted | retain last verified policy or fail closed; never silently downgrade |

## Implementation decomposition

- **SEC-016A (security):** independently source and review official root metadata and create signed-manifest schema, threat model and fixture-only verifier tests. No live roots or signing keys committed.
- **SEC-016B (Android):** add offline manifest verifier, pinned root lookup and negative-path Kotlin/JVM tests; ensure production code cannot load synthetic test roots.
- **SEC-016C (AI/agents):** bind verified enrollment identity to command admission and revocation state without changing the owner-consent boundary.
- **SEC-016D (CI/QA):** run Android JVM tests, Python policy tests, malformed-input fuzz corpus, reproducibility checks and fixture-contamination checks on exact commit SHA.
- **SEC-016E (independent verifier):** inspect provenance, trust model, challenge/key/boot binding, rollback, test evidence and threat-model gaps. Record `PENDING_INDEPENDENT_REVIEW` until another reviewer signs off.
- **Hardware/release:** validate with a consented Pixel 9 Pro only in a separately authorized hardware session; no flashing, bootloader changes, production rollout or release signing from this task.

## Release blockers

No verified upstream engineering `SKILL.md` installation; no authenticated production trust-anchor bundle; no independent PKIX/attestation security approval; no physical Pixel 9 Pro attestation evidence; no proof of signed reproducible release, OTA or recovery. M6 and M8 remain open.
