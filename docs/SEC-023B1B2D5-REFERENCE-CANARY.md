# SEC-023B1B2D5 — Offline key-generation reference canary

**Status: draft, synthetic only; not an accepted security boundary.** Stacked on SEC-023B1B2D4 PR #25, ultimately targeting feat/phase1-agentic-phone. Do not merge or enable MemoryVault without independent review.

## Threat and bounded design

A Keystore alias can be replaced with a different AES-256 StrongBox key carrying identical KeyInfo policy. Rechecking alias metadata before and after a Cipher operation does not establish continuity. This change introduces an **unwired pure-JVM reference verifier** and nine synthetic JUnit tests. It checks that an already-initialized AES-GCM decrypt Cipher can open a domain-separated reference ciphertext bound to a 32-byte generation ID and 32-byte consent digest, with a 12-byte nonce and 16-byte tag. A second same-policy software key cannot open the original reference. Tampering, wrong nonce, absent reference, and malformed tag fail closed.

**Reference match is not authorization.** A caller-supplied reference is not a trusted anchor. An adversary able to replace BOTH alias and reference can create a matching replacement pair. Therefore, no key-generation continuity claim is valid until an immutable or integrity-/rollback-protected owner-enrollment anchor has been provisioned, authenticated, retained, and recovered safely. The verifier does not authenticate a device credential, prove StrongBox, enforce cancellation, or bind to a live CryptoObject. The existing diagnostic probe is not wired to this verifier. The synthetic tests use software JCE keys only.

## Future acceptance gates

1. Specify and independently review the authenticated, rollback-protected generation anchor and key-provisioning lifecycle, including power loss, uninstall/reinstall, revocation, alias replacement, concurrent enrollment, and compromised storage.
2. Integrate only with owner-visible foreground consent and a genuine per-use hardware-backed decrypt CryptoObject. Verify generation reference against a **trusted** anchor and exact pending session; cancellation must win before final admission.
3. Run same-policy alias replacement and reference replacement adversarial tests, device-credential cancellation and invalidation, process death, and caller isolation.
4. Verify hardware provenance, supported authentication mode, and failure behavior on a consented Pixel 9 Pro; obtain independent Android/security review and accessible TalkBack signoff.
5. Keep MemoryVaultService disabled/non-exported, PaperClip RAM-only, executor disconnected, no memory persistence, no root or flashing, and no production/release claims.

Upstream shared SKILL.md remains absent and unverified. The project-specific PROJECT-ADAPTER.md is not a copy of the upstream package. No M1–M8 milestone has independent completion approval.
