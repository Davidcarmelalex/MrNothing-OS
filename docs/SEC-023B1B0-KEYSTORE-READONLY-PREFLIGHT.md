# SEC-023B1B0 — dormant MemoryVault Keystore inspection contract

**Status: proposal; not independently approved.** Scoped to `feat/phase1-agentic-phone`; no memory persistence, owner authentication or IPC is enabled.

## Why this bounded gate exists

The SEC-023 design and SEC-023B1A dormant service are separate, **unmerged** draft PRs (#13 and #16). The SEC-023B0 owner-admission policy (#15) and SEC-023A canonical envelope (#14) are also unmerged. This change does not silently integrate any of them. It introduces only a read-only native inspection of a *future*, distinct AES-GCM Android Keystore alias, plus a pure JVM metadata policy.

A positive `EXISTING_KEY_REQUIRES_OWNER_AUTH` result **does not** mean that an owner authenticated or that any data can be encrypted/decrypted. The service remains absent on this scoped branch and disabled in the separate PR #16. No keys are generated or mutated. An absent, unsupported, malformed, imported, TEE/software, non-per-use, non-StrongBox or non-credential-only key fails closed.

## Required properties

Android API 31+ (StrongBox security-level inspection), AES-256, GCM-only, NoPadding-only, exactly encrypt/decrypt purposes, Keystore-generated origin, StrongBox security level, device-credential-only user authentication with per-operation validity (KeyInfo reports -1; the modern key-generation parameter uses timeout 0). Key metadata is local self-report, **not remote attestation or proof of owner consent**.

## Follow-on acceptance gates — not implemented here

1. SEC-023B1B1: explicit owner-initiated key provisioning with no silent overwrite or TEE fallback; read-back metadata validation and explicit failure UX.
2. SEC-023B1B2: one-operation Android `BiometricPrompt.CryptoObject` bound to the exact cipher and owner-visible operation, with cancellation, lifecycle, UID/profile/signature and revocation checks. Never accept an unbound callback or a prior credential window.
3. SEC-023B1C: independently reviewed non-exported IPC, AAD-bound AES-GCM record encryption/decryption, nonce/replay/rollback controls, consent and delete/export semantics. Persistence must stay disabled until approved.
4. Physical Pixel 9 Pro StrongBox, Keyguard and key-invalidation tests, including lock-state changes, credential rotation, process death and rollback; emulator success cannot substitute.

**Threat note:** KeyInfo flags are not a cryptographic authentication event. Even an authenticated CryptoObject must not alone authorize agent actions; a fresh owner gesture, trusted caller identity, one-use operation binding, foreground lifecycle and revocation remain mandatory. No release claim is justified by this patch.

**Engineering roles:** Android owns KeyInfo adapter; security owns policy; CI/QA owns JVM and source gates; UX/accessibility owns later consent UI; hardware/release owns Pixel evidence; AI/agents may not connect to this component; independent verifier must approve all cross-boundary behavior. Upstream shared SKILL.md remains absent and unverified; PROJECT-ADAPTER.md is the local contract.

**Platform reference:** [Android KeyInfo](https://developer.android.com/reference/android/security/keystore/KeyInfo#getUserAuthenticationValidityDurationSeconds()) documents -1 for every-use authorization. Do not confuse this readback value with the 0 timeout passed to `KeyGenParameterSpec.Builder.setUserAuthenticationParameters`. The StrongBox/credential-only combination and prompt interoperability still require physical hardware evidence.

**CI correction:** The initial hosted Kotlin compilation revealed that `SecretKeyFactory.getKeySpec` returns the general `KeySpec` type; the adapter now explicitly performs a nullable `KeyInfo` cast and refuses an unexpected type. The initial failed run is retained as evidence, not counted as a pass.

**CI correction 2:** Android SDK's `KeyInfo` does **not** expose `isUnlockedDeviceRequired` or `isRandomizedEncryptionRequired` (those belong to `KeyGenParameterSpec` / `KeyProtection`). The read-only preflight cannot prove those two controls. The policy therefore checks only actual KeyInfo metadata; explicit owner-consented key-generation spec, cryptographic operation and physical runtime verification must establish unlocked-device and randomized-IV behavior. The second failed hosted compilation is preserved as evidence.
