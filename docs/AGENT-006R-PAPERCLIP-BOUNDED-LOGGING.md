# AGENT-006R — bounded, nonblocking PaperClip event logs

## Threat and change

The prior content-free logger protected log permissions and paths, but
unlimited append operations could exhaust local storage if events repeated
indefinitely. This change introduces MAX_LOG_BYTES = 1_048_576 and refuses
additional writes once the next entire event would exceed the bound.
It never truncates, rotates, deletes, or migrates an existing log.

A Linux advisory flock(LOCK_EX | LOCK_NB) serializes cooperating PaperClip
writers before checking current file size and appending. If another writer
holds the lock, the event is dropped rather than waiting. This is a
best-effort, noncritical telemetry path: inference continues even if logging
returns False. Existing directory owner/mode, symlink, hardlink, file type,
0600 and content allowlist checks remain.

## Acceptance evidence

Four new offline tests cover an exact-size cap, a cap smaller than one event,
preservation of an already-oversized log, and contention/recovery with a
separate open file descriptor. Run full Python suite and source/security gates,
then inspect exact-head hosted CI before acceptance.

## Residual risks and release gates

Advisory locks do not constrain malicious or noncooperating same-UID writers;
a hostile privileged process or filesystem can still bypass the cap.
Existing oversized logs remain unchanged and require owner-controlled
retention/deletion decisions. The logger does not promise crash-atomic
multi-write events or durability of a log entry after power loss.
This change does not enable an Android executor, permissions, persistent
conversation memory, physical device operations, or a production release.
Independent security review remains required.
