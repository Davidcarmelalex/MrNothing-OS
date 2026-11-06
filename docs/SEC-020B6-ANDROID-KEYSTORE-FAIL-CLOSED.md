# SEC-020B6 — Android Keystore fail-closed negative-path verification

**Status:** SEC-020B6 base, B6A, B6B and B6C are accepted for the exact API 35 x86_64 disposable-emulator failure-path coverage recorded below. The current accepted head is `893b8cdadab035439eefe62aeb4d42409b6d47ef`. This does not establish physical StrongBox behavior, Pixel 9 Pro compatibility, Keystore persistence across reboot/reset, spoken TalkBack acceptance, independent human security approval or production readiness. Those remain separate M5/M6/M7/M8 gates.

## Scope

This slice tests AndroidKeyStore behavior that can be observed without claiming StrongBox hardware. It does not enroll an owner, create a production authority, grant permissions, change trust transitions or connect the agent executor.

AndroidAuthorityTrustCrypto now accepts an internal alias namespace with the original production aliases as defaults. The production AndroidOwnerAuthorityTrustStore continues to construct it with no arguments. Instrumentation supplies a unique UUID-scoped test namespace and removes only aliases created under that namespace in a finally block.

## Instrumentation cases

1. A StrongBox-required marker request fails without creating a TEE marker when the emulator does not advertise FEATURE_STRONGBOX_KEYSTORE. If a test device advertises StrongBox, the test instead requires a marker whose KeyInfo.securityLevel is exactly STRONGBOX and verifies its proof.
2. A missing marker alias cannot verify a marker proof.
3. A malformed marker suffix makes trust-store inspection unavailable.
4. A non-canonical decimal generation suffix (for example 01) makes inspection unavailable.
5. A zero generation marker makes inspection unavailable.
6. A TEE/software-only HMAC marker cannot become the generation watermark.
7. An AES encryption alias without any generation marker is an inconsistent state, not a fresh install.
8. A non-secret key under the marker prefix is rejected.
9. An injected `GeneralSecurityException` from KeyInfo inspection makes the trust store unavailable.
10. An injected runtime provider exception from KeyInfo inspection makes the trust store unavailable.
11. Loss of the AES alias while a generation marker and stored envelope remain produces `RecoveryRequired(ACTIVE_RECORD_UNREADABLE)`, never `Empty`.

SEC-020B6A injects the KeyInfo reader only through the internal test seam. The production default remains the AndroidKeyStore-backed reader. The missing-AES recovery fixture uses an isolated TEE test marker plus a metadata-only test reader that reports the StrongBox level so the coordinator path can be reached on an emulator; this is not StrongBox evidence.

The tests use only disposable, unique AndroidKeyStore aliases and a missing-record persistence fixture. They clean their own aliases and never enumerate/delete production aliases.

## Security invariants

- Marker HMAC and AES-GCM production keys continue to request setIsStrongBoxBacked(true).
- KeyInfo.securityLevel must equal SECURITY_LEVEL_STRONGBOX; hardware-backed TEE is insufficient.
- Malformed, non-canonical, non-positive, wrong-type or non-StrongBox marker state must not become a valid generation watermark.
- An AES alias without a generation marker must not be classified as a fresh install.
- Missing marker proofs fail verification.
- Production aliases remain mrnothing_authority_marker_v1_ and mrnothing_authority_record_aes_v1.

## Evidence boundary and remaining gaps

An API 35 emulator without the StrongBox feature can verify refusal and absence of a TEE fallback; it cannot prove a real StrongBox implementation. If the emulator advertises StrongBox, the test verifies the returned key metadata, but a Pixel 9 Pro M7 hardware run remains separately required.

This slice does not inject a failing KeyInfo provider, simulate Keystore daemon death, verify loss of the AES key while a valid StrongBox marker remains, or test physical Keystore persistence across reboot/reset. Those remain separate failure-injection and hardware gates.

No production key is created or deleted by the instrumentation tests. No root, device flashing, credential bypass, permission grant, production signing or deployment is involved.

## Acceptance

- Phase 1 push/PR Python, Kotlin/JUnit, Android assembly, strict dependency verification and manifest checks pass.
- CI-003 push/PR independent unsigned build, manifest, SBOM and provenance checks pass.
- QA-005 API 35 emulator instrumentation passes all SEC-020B4D, SEC-020B5 and SEC-020B6 cases and confirms test-alias cleanup.
- Independent security review remains mandatory.
- Physical Pixel 9 Pro StrongBox and recovery validation remain M7 gates.

Release state remains release_ready=false; unsigned artifacts are not for release.


## First exact-head run and fixture correction — 2026-11-06

QA-005 run [42220218287](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42220218287) compiled the instrumentation and started all 16 tests (three SEC-020B4D, five SEC-020B5 and eight SEC-020B6). Two SEC-020B6 cases failed before reaching their crypto assertions: the synthetic record helper requested Ed25519 from the default Android provider, which resolved to the AndroidKeyStore key-pair generator and raised `IllegalStateException: Not initialized`. The other 14 tests reported no failures. The workflow stopped before QA-006 onward; emulator diagnostics were captured and the workflow's synthetic lock-credential cleanup reported `Lock credential cleared`.

The test fixture now requests an explicit local Bouncy Castle provider instance, matching the provider-isolation approach used by OwnerAuthorityTrustCeremony. This creates only an in-memory synthetic Ed25519 key pair and does not register or mutate a process-wide provider. No production trust-store, Keystore alias policy, credential flow or Android permission changed. The exact-head QA-005 rerun is required before SEC-020B6 can be accepted.


## Exact-head acceptance — SEC-020B6 base cases (2026-11-06)

At head `83a3aa2e90e89b29bae4f9c2b14cd402f084ebc7`:

- Phase 1 push [42221148919](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221148919) and PR [42221159695](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221159695) passed. The push Python-policy job ran **524 tests**. Android unit tests, debug assembly, same-run repeat APK comparison, strict dependency verification, modified-dependency negative control and manifest security gate passed on push and PR.
- CI-003 push [42221148873](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221148873) and PR [42221159954](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221159954) passed both builders and independent verification. Unsigned APKs were byte-identical (7,829,728 bytes; SHA-256 `09623ce52db112aab99a23b08196b260e9fab02456e76a41d970c14edbc69510`; normalized-entry SHA-256 `97c70391d2c258e19a7cd4080e04bc852472b4c622320bea760ef56fea6c0027`). Runtime inventory, SPDX runtime SBOM, release variant and toolchain matched. CI-003 reports `reproducible=true`, `release_ready=false`. The scoped CI-006 inventory contains 1,260 components and is not a complete hosted-runner image SBOM.
- QA-005 [42221159692](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221159692) passed all workflow steps on a disposable API 35 x86_64 emulator. The instrumentation log reports **16 tests started, 16 finished, 0 skipped, 0 failed**: three SEC-020B4D, five SEC-020B5 and eight SEC-020B6 tests. QA-006 through QA-013 and QA-020B2/B3 passed; synthetic emulator PIN cleanup reported `Lock credential cleared`. Evidence artifact [13504760131](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42221159692/artifacts/13504760131), digest `sha256:4012f7db4d37504a9080fd49bb57eff1cc9780803733e56f4a19f4346b0eb519`.
- QA-011 remains a read-only TalkBack availability preflight and reported the service disabled; QA-012 is structural semantics only, not spoken TalkBack acceptance.

SEC-020B6 base cases are accepted for the tested API 35 x86_64 emulator path only. This does not prove StrongBox hardware, Pixel 9 Pro behavior, KeyStore persistence across reboot/reset, spoken TalkBack, independent human security approval or production readiness.

## SEC-020B6A — deterministic KeyInfo/provider failure injection

The production crypto class now accepts an internal `AndroidAuthorityKeyInfoReader` seam. Its default is `PlatformAndroidAuthorityKeyInfoReader`, which performs the same AndroidKeyStore `SecretKeyFactory` / `KeyInfo.securityLevel` query as before. The production `AndroidOwnerAuthorityTrustStore` still constructs `AndroidAuthorityTrustCrypto()` with the original aliases and default reader.

Three isolated instrumentation cases were added:
- GeneralSecurityException during KeyInfo inspection returns an unavailable trust state.
- Runtime provider failure during KeyInfo inspection returns an unavailable trust state.
- Missing AES alias with a generation marker and a structurally valid stored envelope returns `RecoveryRequired(ACTIVE_RECORD_UNREADABLE)`.

The metadata test double is scoped to one instrumentation instance and does not register a global JCA provider. The missing-AES case uses an isolated test alias and synthetic StrongBox metadata only to exercise coordinator behavior; it does not claim a StrongBox key exists. Test aliases are cleaned in `finally`.

**SEC-020B6A status:** implementation committed; exact-head Phase 1, CI-003 and QA-005 acceptance pending. No production alias, key, authority, permission, trust transition or executor connection was changed.


## Exact-head acceptance — SEC-020B6A (2026-11-06)

At head `f6e4099ae991eba9b7e8a56a674b08efd479c7ed`:

- Phase 1 push [42223971396](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223971396) and PR [42223981107](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223981107) passed. The Python policy job ran **526 tests**; Android unit tests, debug APK assembly, repeat-build comparison, strict dependency verification, modified-dependency negative control and manifest gate passed.
- CI-003 push [42223971449](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223971449) and PR [42223981151](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223981151) passed both independent builders and the verifier. Unsigned APKs were byte-identical: 7,830,680 bytes, SHA-256 `60f0df5a92ebed50e1ddf1885e56e5b12ceb25c19263f8910943d832d53fb53f`; normalized-entry SHA-256 `1c08ed89586bad608133bbcc4521c440895e10bef1dc78f4cc757501e5228405`. Runtime inventory, SPDX runtime SBOM and the scoped 1,260-component CI-006 build-environment inventory matched. CI-003 reports `reproducible=true`, `release_ready=false`; the inventory is not a complete hosted-runner image SBOM.
- QA-005 PR [42223981189](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223981189) passed all workflow steps on a disposable API 35 x86_64 emulator. The downloaded JUnit XML reports **19 tests, 0 failures, 0 errors, 0 skipped**: three SEC-020B4D lifecycle tests, five SEC-020B5 AtomicFile tests and eleven SEC-020B6/B6A Keystore tests. QA-006 through QA-013 and QA-020B2/B3 passed; the synthetic emulator lock credential was cleared. Evidence artifact [13505691330](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42223981189/artifacts/13505691330), digest `sha256:35ee53f42519f688d0e65ad422b1d2e3fd1a235aa8e4511b5e2ac736e9ebc569`.
- QA-011 remains a read-only TalkBack availability preflight and reported the service disabled. QA-012 is structural semantics only, not spoken TalkBack acceptance.

SEC-020B6A is accepted only for its tested API 35 x86_64 emulator failure-path scope. The conditional StrongBox test does not establish physical StrongBox behavior, Pixel 9 Pro compatibility, Keystore persistence across reboot/reset, spoken TalkBack, independent human security approval or production readiness.

## SEC-020B6B — deterministic Keystore load and alias-enumeration failure injection

A narrow internal `AndroidAuthorityKeyStoreReader` seam now isolates AndroidKeyStore loading and marker-alias enumeration. The production default delegates directly to `KeyStore.getInstance("AndroidKeyStore")`, `load(null)` and `store.aliases()`; the production `AndroidOwnerAuthorityTrustStore` still constructs `AndroidAuthorityTrustCrypto()` with the default platform readers and original aliases.

Five new isolated instrumentation cases inject:
1. `GeneralSecurityException` during AndroidKeyStore load.
2. `IOException` during AndroidKeyStore load.
3. Runtime provider failure during AndroidKeyStore load.
4. `GeneralSecurityException` during marker-alias enumeration.
5. Runtime provider failure during marker-alias enumeration.

Each case requires the trust store to report `Unavailable`, refuses generation-marker creation, and verifies that no isolated marker or AES alias was created. Alias enumeration failures use a real disposable AndroidKeyStore instance but inject the failure at the narrow reader boundary. No process-wide JCA provider is registered, and only UUID-scoped test aliases are eligible for cleanup.

**SEC-020B6B status:** implementation committed; exact-head Phase 1, CI-003 and QA-005 validation pending. These deterministic seam tests verify fail-closed handling at the injected boundary; they do not prove that a Pixel 9 Pro's real AndroidKeyStore provider will exhibit the same failures or establish StrongBox hardware behavior.


## Exact-head acceptance — SEC-020B6B and SEC-020B6C (2026-11-06)

**Accepted source head:** `893b8cdadab035439eefe62aeb4d42409b6d47ef`.

- Phase 1 push [42244248208](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244248208) and PR [42244257688](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244257688) passed. Each Python-policy job ran **530 tests**. Android `:app:testDebugUnitTest`, `:app:assembleDebug`, same-run repeat debug-APK byte comparison, strict Gradle dependency verification, modified-dependency negative control, Android source-manifest gate and debug artifact provenance passed.
- CI-003 push [42244248205](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244248205) and PR [42244257705](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244257705) passed both independent builders and the verifier. Unsigned release APKs were byte-identical: **7,831,964 bytes**, SHA-256 `a8acfc839d7de40d21cf6452989056953060e24eb8dd12f766408f3b029e30f9`; normalized-entry SHA-256 `4cc2150f1d66384508ab181236d233b7abec5eeebcbeed855a45b43be3aab8b4`. Runtime inventory, SPDX runtime SBOM, release variant and toolchain matched. The verifier reported `reproducible=true`, `release_ready=false`.
- CI-006 independently matched a **1,260-component scoped build-environment inventory**. It covers the declared OS packages, Python packages, Android SDK packages, Gradle distribution/plugins, JDK/Python runtimes and pinned GitHub Actions. It does not claim to enumerate every transitive Gradle plugin-resolution dependency, every runner toolcache file or the complete hosted-runner image.
- QA-005 [42244257673](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244257673) passed every workflow step on a disposable **API 35 x86_64 emulator**. The downloaded JUnit XML reports **28 tests, 0 failures, 0 errors and 0 skipped**: three SEC-020B4D lifecycle tests, five SEC-020B5 AtomicFile tests and twenty SEC-020B6-family tests. The twenty include the base/B6A cases, five B6B load/alias cases and all four B6C key-retrieval cases. Evidence artifact [13516679629](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42244257673/artifacts/13516679629), digest `sha256:57dfa4349aef3a1db93a8f523f240d6b0589ded6c11cf27051405fbd0a3940b9`.
- QA-005 also completed launcher runtime/recovery, QA-006 large-font, QA-007 HOME cancellation, QA-008 explicit HOME acceptance, QA-009 stock-launcher restoration, QA-010 keyboard navigation, QA-011 read-only TalkBack preflight, QA-012 structural semantics, QA-013 insecure-enrollment denial and QA-020B2/B3 emulator checks. QA-011 reported `blocked_service_disabled`; QA-012 passed structural checks only. Neither is spoken TalkBack acceptance.

**SEC-020B6B and SEC-020B6C are accepted only for the injected failure paths exercised on this API 35 x86_64 emulator.** The four B6C tests cover marker/AES `UnrecoverableKeyException` and `ProviderException`; they verify fail-closed outcomes and no generation advancement/fallback. Test metadata doubles are not StrongBox hardware evidence.

Independent human security review remains pending. Physical Pixel 9 Pro StrongBox/key persistence/reboot/recovery, spoken TalkBack, SIM/VoLTE hardware checks, signed release, OTA rollback and production deployment remain unverified. Unsigned CI-003 artifacts are not for installation or release.
