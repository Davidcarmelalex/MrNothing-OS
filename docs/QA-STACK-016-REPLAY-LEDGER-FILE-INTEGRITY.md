# QA-STACK-016 — Private, identity-bound durable replay ledger

**Scope:** core/command_admission.py and tests/test_command_admission.py on existing PR #51. No Android device API, permission, executor, transport or deployment changes.

## Observed failure before the patch

The original DurableReplayLedger called sqlite3.connect(path) directly. With POSIX umask 022, a new SQLite database was mode 0644, exposing command IDs, device IDs and timestamps to other local users. Existing symlinks or replacement/deletion could silently bypass expected durable replay history.

## Bounded correction

- Pre-create the file atomically with O_CREAT | O_EXCL and mode 0600, plus O_NOFOLLOW when supported, before SQLite opens it.
- Reject preexisting non-regular files, symlinks, group/other-accessible files and wrong POSIX ownership; do not silently chmod or migrate an exposed file.
- Require a real filesystem path rather than :memory: or a file: URI.
- Pin device/inode and recheck ownership, permissions and identity before and after each SQLite connection. Missing, replaced or relaxed files raise sqlite3.OperationalError, translated by admission to LEDGER_UNAVAILABLE without dispatch.
- Reject boolean/non-integer ledger limits.

## Regression and operational limits

Seven new offline tests cover private creation under umask 022, world-readable files, symlinks, deletion/replacement, post-initialization permission relaxation, in-memory paths and invalid limits. Existing restart and concurrent replay tests must still pass.

**Important:** File mode and inode checks do not provide cryptographic rollback resistance, protection against a hostile same-user process, or atomic file-descriptor binding to SQLite. A directory writer can still race path lookup. This is local prototype fail-closed hardening, not an accepted production security boundary. Production needs authenticated persistent state and a reviewed anti-rollback strategy.

Existing deployments with group/world-readable files now fail closed and need operator-reviewed migration preserving replay history; no automatic migration, deletion or chmod occurs. Do not discard replay state just to make a test pass.

Independent human security review of the full UX x MemoryVault integration remains pending. No physical Pixel 9 Pro, spoken TalkBack, StrongBox, signed release or OTA/recovery acceptance is implied. M1-M8 remain unaccepted.
