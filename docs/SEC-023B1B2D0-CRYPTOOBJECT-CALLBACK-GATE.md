# SEC-023B1B2D0 — Dormant Android CryptoObject callback identity gate

**Status:** engineering proposal only; not authenticated cryptographic proof or authorization.
**Parent:** PR #21 composite, scoped to `feat/phase1-agentic-phone`.

## Bounded change

- A one-shot, monotonic 30-second state machine records the exact CryptoObject and Cipher object identities plus the canonical consent digest.
- The Android adapter obtains the returned object and authentication type from the actual `BiometricPrompt.AuthenticationResult`, requires `DEVICE_CREDENTIAL`, and rejects absent/non-GCM/incorrect-IV prompt objects.
- Mismatched digest, object identity, callback type, timeout, clock rollback/exception, cancellation, replay, re-arm and concurrent completion fail closed.
- Even the positive state is named `AWAITING_AUTHENTICATED_CIPHER_OPERATION`. It is not a grant, and cannot start the disabled service, store memory or call the agent executor.

## Remaining mandatory security acceptance

This is **not** evidence of a hardware-backed key or genuine per-use authentication. Object identity can also match a software Cipher. Before connecting any UI or persistence, the security engineer must independently review a controlled StrongBox key-provisioning path, verify the exact AndroidKeyStore key metadata, confirm framework `BiometricPrompt.CryptoObject` compatibility with per-use `AUTH_DEVICE_CREDENTIAL`, bind the consent digest as AES-GCM AAD, and demonstrate a successful post-authentication Cipher operation. Include negative tests for cancellation, revocation, lockscreen credential removal, key invalidation, process death, same-UID/cross-UID attempts and backgrounding. Test on a physical Pixel 9 Pro with owner consent. No fallback to software, biometric-only, or time-window authentication is authorized.

The framework adapter is intentionally **not wired** into an Activity or service. Android CI compiling it does not establish callback execution. JVM tests use synthetic object identities and cannot establish framework or hardware behavior. No new Android permissions, root privileges, key generation, installation, flashing or deployment are involved.

**Milestones:** M1/M2/M6 in progress; M3 partial; M4 not started; M5 not accepted; M7/M8 blocked. No independently complete milestone. Upstream shared `SKILL.md` remains absent/unverified; local `PROJECT-ADAPTER.md` is project-specific.
