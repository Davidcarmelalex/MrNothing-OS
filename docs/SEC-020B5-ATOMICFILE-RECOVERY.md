# SEC-020B5 — Android AtomicFile interruption and recovery tests

**Status at initial submission:** instrumentation tests added; exact-head Android/QA CI pending.

## Scope

This is a test-only extension of the existing SEC-020B1 Android persistence adapter. It does not change the production trust-store implementation, Keystore aliases, credential ceremony, manifest, permissions or agent connectivity.

The new `AndroidAtomicAuthorityRecordPersistenceTest` runs inside the existing API 35 disposable-emulator instrumentation step and supplies an isolated `ContextWrapper` whose `noBackupFilesDir` points to a temporary directory under the test app's cache directory.

## Runtime cases

1. Atomic write/read round-trip and replacement of a committed record.
2. Interrupted replacement: write a baseline record, call the real `AtomicFile.startWrite()`, write and sync partial replacement bytes, close without `finishWrite()` or `failWrite()`, then read through a fresh adapter. The test requires Android `AtomicFile.openRead()` to restore the previous committed backup.
3. Interrupted first write: Android AtomicFile discards its uncommitted staging file when no previous base exists, so the adapter correctly reports Missing. The test then supplies a synthetic generation high-water marker and verifies that OwnerAuthorityTrustStore.inspect() returns RecoveryRequired(ACTIVE_RECORD_MISSING), never Empty. This exercises the marker-first fail-closed contract at the layer that can distinguish an interrupted first commit from a fresh install.
4. Oversized stored data is reported as `AuthorityRecordRead.Failed`.
5. Empty and oversized writes are refused without changing the previous committed bytes.

The tests use no credentials, no root, no production authority material and no Android Keystore calls. Temporary test files are removed in `finally`.

## Evidence boundary

Closing an unfinished `AtomicFile` output stream is a deterministic simulation of the interrupted-write window. It is **not** a process-kill, kernel crash, sudden power-loss, filesystem-corruption or physical-device durability test. The emulator does not establish StrongBox behavior. Pixel 9 Pro validation remains an M7 hardware gate.

Exact-head Phase 1, CI-003 and QA-005 results must be recorded before this slice is accepted. Independent security review remains pending.


## Exact-head correction — interrupted first write

The first SEC-020B5 emulator run, [QA-005 #42203152698](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42203152698), compiled and executed all eight instrumentation tests but failed the first-write case because the test incorrectly expected AuthorityRecordRead.Present after an unfinished first AtomicFile.startWrite().

That expectation was wrong for Android's atomic staging protocol: with no prior committed base or backup, openRead() discards the uncommitted staging file and reports no committed record. The trust-store layer—not the persistence adapter—must distinguish this from a fresh install by checking the marker-first StrongBox generation high-water mark.

The corrected instrumentation test now asserts:
- the interrupted first write is AuthorityRecordRead.Missing;
- a synthetic high-water marker at generation 1 causes OwnerAuthorityTrustStore.inspect() to return RecoveryRequired(ACTIVE_RECORD_MISSING), never Empty.

This is a test-contract correction, not a production storage change. Exact-head rerun and independent review remain pending. The test still does not simulate process death, kernel crash or power loss.


## Exact-head acceptance — 2026-11-06

**Acceptance head:** `c80634ec871516e829fb18025de8af732fee422f` on `feat/phase1-agentic-phone`.

- Phase 1 push [42210823960](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210823960) and PR [42210832289](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210832289) both passed. Each Python-policy job reported **518 tests**; Android `:app:testDebugUnitTest`, `:app:assembleDebug`, same-run repeat debug-APK byte comparison, strict Gradle dependency verification, modified-dependency negative control and the source-manifest security gate passed.
- CI-003 push [42210824198](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210824198) and PR [42210832148](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210832148) passed both independent builders and the independent verifier. The unsigned release APKs were byte-identical at 7,829,060 bytes, SHA-256 `3c09c4b4c7956cb7e2a90fdc96c9ab909f53f4526c8439ed25b0aae78c49f1ea`; normalized-entry SHA-256 `9e6c4b9489af0f8b07f1d5fdae1d2ac6746041686d84fded9c0cecd4ddbc97d1`. Runtime inventory and SPDX runtime SBOM matched. The scoped CI-006 build-environment inventory matched at 1,260 components; it is not a complete hosted-runner image SBOM. The verifier reported `reproducible=true` and `release_ready=false`.
- QA-005 [42210832208](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210832208) passed all 21 workflow steps on a disposable API 35 x86_64 emulator. Gradle reported **8 instrumentation tests started and 8 finished**, followed by `BUILD SUCCESSFUL`. The run includes the three SEC-020B4D lifecycle tests and five SEC-020B5 AtomicFile tests. QA-006 through QA-013 and QA-020B2/B3 also completed; synthetic emulator PIN cleanup reported `Lock credential cleared`. Evidence artifact [13498728651](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42210832208/artifacts/13498728651).
- QA-011 remains a read-only TalkBack availability preflight and is not spoken-navigation acceptance. QA-012 is structural semantics only.

**Gate decision:** SEC-020B5 is accepted for the tested API 35 x86_64 disposable-emulator AtomicFile path only. The interrupted-write tests use deterministic unfinished-stream simulation; they do not prove process-kill, kernel-crash, sudden-power-loss, filesystem-corruption or physical-device durability. The emulator does not establish StrongBox behavior. Independent human security review and Pixel 9 Pro validation remain pending. Release provenance remains unsigned and `release_ready=false`.
