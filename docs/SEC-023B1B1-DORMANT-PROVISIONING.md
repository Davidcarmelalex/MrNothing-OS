# SEC-023B1B1 — Dormant StrongBox MemoryVault provisioning specification

**Status:** design + source/JVM policy only. **Not an implementation of key
provisioning, cryptographic owner authentication, encrypted memory or IPC.**
Related SEC-023 through SEC-023B1B0 draft PRs are unmerged; do not imply their
code is integrated into this branch.

## Boundaries

- MemoryVaultProvisioningPolicy rejects API below 31, secondary users, untrusted
  caller signals, background UI, locked devices, absent secure credentials,
  absent explicit memory opt-in, missing StrongBox and existing aliases.
- The positive result means REQUIRES_OWNER_CEREMONY, not authenticated,
  approved, provisioned or ready to persist.
- MemoryVaultKeySpecDraft.forSecurityReview constructs only an uninstalled
  Android KeyGenParameterSpec. It does not access Keystore or generate a key.
  The alias is distinct from the existing owner-consent P-256 signing key.
- Specification requires AES-256/GCM/NoPadding, randomized IV, unlocked-device
  restriction, zero-second (per-use) device-credential authentication, and
  StrongBox with **no TEE/software fallback**. Actual device support and
  BiometricPrompt CryptoObject interoperability are **unverified**.
- Inputs are caller-supplied planning signals, not trustworthy authorization
  evidence. Never expose this policy as a Binder admission gate without
  independently trusted UID/profile/signature/foreground/consent provenance.
- No existing alias may be overwritten, replaced, rotated or deleted as a
  side effect. Key invalidation, StrongBox absence and prompt cancellation
  must fail closed in the future implementation.

## Mandatory future acceptance gates

1. Independent security review of the exact key-generation policy and Android
   API behavior, including device-credential-only per-use CryptoObject
   compatibility on **physical Pixel 9 Pro**. Reject unsupported combinations;
   never silently weaken the requirement.
2. Owner-visible, accessible consent UX with fresh system authentication,
   cancellation and revocation; trusted snapshot provenance and no implicit
   background enrollment.
3. Keystore operation in a disabled-by-default native component with
   atomic check-if-absent and race protection, no overwrite, strict failure
   handling and post-provisioning KeyInfo inspection. No remote caller.
4. Cryptographic prompt binding, AEAD tag verification, crash-safe replay/
   nonce ledger, authenticated IPC and negative cross-UID/same-UID tests.
5. Real hardware tests for locked state, reboot, credential changes, key
   invalidation, StrongBox unavailable, process death and rollback.
6. Independent verifier signs off before any persistent memory is enabled.

## Verification semantics

Python tests are **source assertions**, Kotlin/JUnit tests are **pure policy
unit tests**, hosted Android build confirms compilation only. Neither proves
actual key creation, owner consent, encryption or physical-device behavior.
All M1–M8 gates remain unaccepted.
