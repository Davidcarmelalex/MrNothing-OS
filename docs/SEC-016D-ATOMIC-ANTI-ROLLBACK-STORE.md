# SEC-016D — Atomic anti-rollback persistence

**Status:** Implemented as a bounded SQLite library on the SEC-016A/B draft branch. CI and independent security review are required. No production consumer is connected.

## Purpose

SEC-016B verifies a signed trust manifest against a caller-supplied pinned Ed25519 key, but its previous version input was only a caller-supplied snapshot. SEC-016D adds a persistent version ledger and stores the signed manifest bytes and version in one SQLite transaction.

## Transaction contract

\`\`\`text
BEGIN IMMEDIATE
  validate database integrity and schema
  read current committed version
  verify signature, key id, time window and strictly increasing version
  write manifest bytes, SHA-256 digest, version and timestamp
  compare-and-swap against the version read under the write lock
COMMIT
\`\`\`

A failed signature, stale/equal version, schema/integrity error, lock timeout or failed commit returns no authenticated result and leaves the previous row unchanged. The SQLite write lock is acquired before reading the version, preventing two processes from both committing the same version. The manifest bytes and version are stored atomically so a crash cannot advance the version while losing the corresponding signed bundle.

## Storage controls

- SQLite synchronous=FULL and bounded busy timeout.
- One-row schema with PRAGMA user_version=1, strict schema/row validation and quick_check.
- File must be regular, non-symlink and owner-only (0600 on POSIX).
- Existing/missing/corrupt databases are never silently reset or recreated during normal reads/updates.
- mode=rw prevents a deletion race from opening a new version-zero database.
- Database file size is capped at 1 MiB; manifest bytes are bounded by the SEC-016A 256 KiB parser limit.
- load_committed() re-verifies the stored signature and validity window and checks the stored digest/version before returning the bundle.

## Guarantees and limits

This is a local crash/restart/concurrency replay control. It is **not** a hardware-backed monotonic counter and cannot detect restoration of an older copy of the entire database, filesystem rollback by a privileged actor, or malicious modification by the app's own filesystem owner. The database must live in the Android app-private directory; a future hardware/remote monotonic-state design and backup/restore policy remain required before production use.

This module does not perform PKIX path validation, Android KeyDescription parsing, challenge/key/device identity binding, verified-boot evaluation, CRL/OCSP revocation, owner-consent checks or command authorization. CommittedTrustBundle is not a device-attestation verdict. No production trust roots or update-signing keys are included.

## Regression coverage

17 focused tests cover initialization/idempotence, owner-only permissions, success, persistence/re-authentication after restart, equal-version replay, older-version rollback, bad signatures, digest tampering, expired stored manifests, missing/corrupt/wrong-schema databases, non-overwrite behavior, symlink refusal, lock timeout, same-version concurrent writers and concurrent increasing versions.

Local harness: Python 3.13.5 with cryptography 46.0.4; 17/17 focused tests and compileall passed. Exact repository integration and pinned cryptography==50.0.2 are delegated to GitHub Actions on this commit.

## Acceptance gates

1. Exact-head repository Python CI passes with pinned cryptography==50.0.2.
2. Independent reviewer inspects transaction ordering, DB path/permission assumptions, SQLite durability and whole-file rollback limitation.
3. Android app-private path and backup/restore policy are specified before production integration.
4. A hardware-backed or trusted remote anti-rollback anchor is designed before claiming resistance to privileged filesystem rollback.
5. No production consumer is enabled until independent approval and authoritative key/root provenance exist.
