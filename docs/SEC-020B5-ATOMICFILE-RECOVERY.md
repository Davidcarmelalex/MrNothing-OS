# SEC-020B5 — Android AtomicFile interruption and recovery tests

**Status:** instrumentation tests added; exact-head Android/QA CI pending.

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
