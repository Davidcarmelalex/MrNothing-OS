# SEC-019A — Atomic enrollment-aware consent admission

**Status:** Implemented on `feat/phase1-agentic-phone`; exact-head CI is the acceptance source.  
**Scope:** Host-side consent admission only. No listener, device executor, Android permission grant or production enrollment ceremony.

## Problem

SEC-018 checked the active paired enrollment, reserved a nonce in a separate SQLite database, then checked enrollment again. This reduced the race but did not make credential revocation/rotation and nonce consumption one atomic operation.

## Change

The owner/device enrollment database moves to database schema version 2 and gains `owner_consent_replay`. The signed enrollment statement protocol remains version 1; the database version is independent.

`SQLiteOwnerEnrollmentRegistry.consume_consent_nonce` performs the following under one `BEGIN IMMEDIATE` transaction:

1. Read the current device row.
2. Require active state and exact owner/device identity.
3. Require exact transport certificate SHA-256 fingerprint and credential generation.
4. Compare the exact canonical P-256 SPKI bytes.
5. Enforce a 10,000-row bound and reject an existing (device, nonce).
6. Insert the nonce and commit.

Enrollment rotation/revocation already uses `BEGIN IMMEDIATE` against the same file. SQLite therefore serializes these writes: if rotation/revocation commits first, old credentials fail; if admission commits first, it is ordered before the later credential change. This is a local single-database guarantee, not a distributed or hardware-monotonic guarantee.

## Migration

New databases are initialized directly at schema v2. Existing schema-v1 databases are not silently changed. An operator must explicitly call `migrate_v1_to_v2(explicit_migration=True)`. The migration verifies the exact v1 table set and SQLite integrity, adds only the replay table/index, updates `user_version`, preserves enrollment/history rows and is idempotent. Unrecognized, corrupt or partially modified schemas fail closed.

## Tests

- one-use nonce survives a new registry instance/process-style reopen;
- revocation committed before admission rejects;
- rotation committed before admission rejects the old generation;
- concurrent duplicate nonce submissions admit exactly once;
- wall-clock advance followed by rollback does not evict a consumed nonce;
- malformed nonce fails without consuming a valid nonce;
- explicit v1 migration preserves enrollment/history and is idempotent.

The synthetic tests use ephemeral software keys and temporary databases.

## Remaining blockers

- SEC-019B: bind verifier admission to the exact live TLS connection/session; remove the caller-supplied authentication boolean from the production-facing contract.
- Provision the enrollment authority public key through a separately authenticated first-install ceremony.
- Android client certificate provisioning and hardware-backed owner key validation.
- Independent security review.
- Rate limiting, operational audit log, remote attestation and executor design.

The only positive result remains `ADMITTED_NO_EXECUTION`. No Android action is executed.

## Replay-retention decision

The initial draft used wall-clock TTL deletion. Review identified that a forward clock jump followed by rollback could remove a replay record while a capability might again appear unexpired. Automatic wall-clock eviction has therefore been removed. Consumed nonces remain until a separately reviewed compaction/anti-rollback mechanism exists. The 10,000-row limit causes fail-closed capacity rejection rather than unsafe deletion.


## SEC-019B follow-on

Implemented in the transport adapter: a session is retained against the exact live server-side SSLSocket object, and every issued challenge is retained against that connection with a monotonic expiry deadline. Verification rechecks the live peer certificate, current transport enrollment and generation, exact challenge/session binding, current owner/device consent enrollment and then performs the atomic nonce transaction. The request-facing adapter method accepts no authentication boolean or caller-supplied certificate/generation/session snapshots. See SEC-019B-LIVE-TLS-SESSION-BINDING.md.

This remains a process-local library boundary. There is no listener, executor, persistent session store, Android TLS client provisioning or production service. Independent security review is still required.
