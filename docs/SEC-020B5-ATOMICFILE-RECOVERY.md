# SEC-020B5 — Android AtomicFile interruption and recovery tests

**Status:** instrumentation tests added; exact-head Android/QA CI pending.

## Scope

This is a test-only extension of the existing SEC-020B1 Android persistence adapter. It does not change the production trust-store implementation, Keystore aliases, credential ceremony, manifest, permissions or agent connectivity.

The new `AndroidAtomicAuthorityRecordPersistenceTest` runs inside the existing API 35 disposable-emulator instrumentation step and supplies an isolated `ContextWrapper` whose `noBackupFilesDir` points to a temporary directory under the test app's cache directory.

## Runtime cases

1. Atomic write/read round-trip and replacement of a committed record.
2. Interrupted replacement: write a baseline record, call the real `AtomicFile.startWrite()`, write and sync partial replacement bytes, close without `finishWrite()` or `failWrite()`, then read through a fresh adapter. The test requires Android `AtomicFile.openRead()` to restore the previous committed backup.
3. Interrupted first write: a non-empty partial base is reported as present bytes, never as a missing/fresh-install record. The higher-level codec and generation-marker logic must reject the incomplete record; the existing JVM store tests cover unreadable-record recovery semantics.
4. Oversized stored data is reported as `AuthorityRecordRead.Failed`.
5. Empty and oversized writes are refused without changing the previous committed bytes.

The tests use no credentials, no root, no production authority material and no Android Keystore calls. Temporary test files are removed in `finally`.

## Evidence boundary

Closing an unfinished `AtomicFile` output stream is a deterministic simulation of the interrupted-write window. It is **not** a process-kill, kernel crash, sudden power-loss, filesystem-corruption or physical-device durability test. The emulator does not establish StrongBox behavior. Pixel 9 Pro validation remains an M7 hardware gate.

Exact-head Phase 1, CI-003 and QA-005 results must be recorded before this slice is accepted. Independent security review remains pending.
