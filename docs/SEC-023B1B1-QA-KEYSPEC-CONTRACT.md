# SEC-023B1B1-QA — Android KeyGenParameterSpec contract verification

**Scope:** four Android instrumentation tests against the **uninstalled** MemoryVault
KeyGenParameterSpec draft proposed in SEC-023B1B1. These tests are metadata-only:
they never open AndroidKeyStore, create/delete a key, authenticate a user, grant a
permission, write memory, or enable the dormant MemoryVault service.

## Objective acceptance

- The actual Android framework builder returns an AES-256/GCM/NoPadding spec with
  exactly encrypt/decrypt purposes, randomized encryption, unlocked-device
  restriction, per-operation authentication duration 0, DEVICE_CREDENTIAL-only
  authentication and StrongBox-backed flag set.
- Missing explicit owner consent, unavailable StrongBox, or an existing alias
  yields no specification.
- QA-005 instrumentation allowlist includes this class; its source inventory
  gate rejects omitted/unexpected classes.
- A disposable API 35 emulator must **execute** these tests; Gradle
  assembleDebugAndroidTest alone does not prove execution.

**Limitations:** positive test signals are synthetic, deliberately marking
StrongBox available so the draft can be inspected on a generic emulator. This
does not attest hardware availability, that AndroidKeyStore accepts the spec,
that the credential-only CryptoObject path works, or that a Pixel 9 Pro supports
this combination. Hardware testing and independent security review remain
mandatory before key generation or persistence. Related SEC-023 through
SEC-023B1B0 PRs remain unmerged, and this branch does not integrate them.

## Acceptance and release gates

Keep the proposal draft until exact-head Python/Android CI, QA-005 actual
instrumentation execution, independent security review, and upstream PR
dependency reconciliation. No M1-M8 milestone is independently accepted.
