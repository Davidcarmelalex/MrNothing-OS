# SEC-023B1B2D1 — Dormant AndroidKeyStore AES-GCM authentication probe

Status: PROPOSED, not independently security-approved. Scoped to PR #21 follow-up; base feat/phase1-agentic-phone.

A one-shot component reads an existing StrongBox-required AES key by the fixed AndroidKeyStore alias, reuses the read-only strict KeyInfo preflight, initializes an AndroidKeyStore AES-GCM Cipher and returns its CryptoObject for a future trusted owner UI. It neither launches a prompt nor generates/imports/replaces/deletes keys. There is no software fallback.

After a matching framework callback and second key-metadata preflight, the component binds the canonical 32-byte consent digest as GCM AAD and invokes doFinal on zero-length synthetic plaintext. It discards and zeroes the resulting tag and AAD. The strongest possible outcome is CRYPTO_OPERATION_EXECUTED_NOT_AUTHORIZED, not consent, key provenance certification, or permission to store memory.

Limitations: no owner UI; no actual credential prompt; no physical Pixel 9 Pro proof; no evidence of credential-only CryptoObject interoperability with per-use StrongBox keys; key alias replacement race, process death, same-UID/cross-UID isolation, background cancellation, revocation, key invalidation and spoken TalkBack remain open. The provider-name check is not independent hardware attestation. Never downgrade to software or time-window authentication to make a test pass.

Seven pure JVM policy regressions and six Python source-security regressions are provided; they do not demonstrate actual authenticated Keystore execution. Independent security review is pending. MemoryVault remains disabled, PaperClip memory RAM-only, and Android agent execution disconnected. Upstream shared SKILL.md is absent/unverified; PROJECT-ADAPTER.md is local and project-specific. M1/M2/M6 in progress; M3 partial; M4 not started; M5 not accepted; M7/M8 blocked; no milestone independently complete.
