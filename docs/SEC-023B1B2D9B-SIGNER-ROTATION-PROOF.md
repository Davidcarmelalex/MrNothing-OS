# SEC-023B1B2D9B — Dual-signature signer-rotation proof (offline only)

**Status: NOT AUTHORIZING; no trusted enrollment is implemented.**

The existing signed witness policy verifies an Ed25519 signature against a caller-provided pin. The owner-recovery policy explicitly cannot establish the pin's independent provenance or protect its generation watermark. This bounded follow-up tests one cryptographic prerequisite for future rotation: an existing signer must approve the new public-key pin, and the proposed new signer must demonstrate possession of its private key for the **same** domain-separated transaction.

The canonical payload binds previous and adjacent candidate generation, owner user ID 0, a 256-bit lowercase nonce, and SHA-256 fingerprints of both canonical Ed25519 X.509 DER public keys. Both signatures are required. Inputs are copied before verification; malformed DER, wrong signatures, altered keys/pins/nonce, non-adjacent generations and key reuse fail closed.

The only positive result is `DUAL_SIGNATURES_VALID_NOT_AUTHORIZED`. It is deliberately replayable as a pure stateless test. It **does not** prove:
- The old signer pin came from an independently authenticated source, or was ever trusted by the owner.
- The old signing key was held in StrongBox, is non-exportable, or is currently uncompromised.
- The nonce is fresh, durable or independently enforced; whole-state rollback remains undetectable.
- An Android credential prompt, owner-facing consent or protected enrollment actually occurred.
- Durable commit ordering, key invalidation, recovery or physical Pixel 9 Pro compatibility.

**Integration remains forbidden.** No Android service, launcher, owner UI, MemoryVault persistence, network agent or executor may consume this result as an authority. The existing `OwnerAuthorityTrustStore` is a separate system; its marker model does not automatically anchor MemoryVault witness provenance. A production integration requires independently authenticated initial signer pin, rollback-resistant trusted watermark, durable transaction journal, genuine credential-bound CryptoObject verification, independent security approval and physical Pixel 9 Pro StrongBox tests.

Synthetic JVM tests and exact-head CI prove only the offline cryptographic policy and its fail-closed cases. Upstream shared `SKILL.md` remains absent and unverified. M1–M8 milestone acceptance is unchanged.
