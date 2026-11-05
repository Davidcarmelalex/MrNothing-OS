# SEC-020B1 — Android authority trust-store transaction boundary

**Status at submission:** implementation committed; exact-head CI and independent security review pending.

## Scope

SEC-020B1 implements the storage transaction boundary beneath SEC-020A. It is intentionally not wired into the enrollment Activity, the host registry, command admission, permission grants or the agent executor.

The implementation consists of:

- `OwnerAuthorityTrustStore`: a serialized transaction coordinator that accepts only a SEC-020A `Ready` proposal, checks the current state/mode/generation transition, creates the new generation marker first, encrypts the canonical record, atomically replaces the active record and verifies the persisted bytes by reopening them.
- `AndroidAuthorityTrustCrypto`: StrongBox-required Android Keystore HMAC-SHA256 generation markers and AES-256-GCM record encryption. It refuses API levels below Android 12 because the implementation requires `KeyInfo.securityLevel` to distinguish StrongBox from TEE. It never falls back to TEE or software.
- `AndroidAtomicAuthorityRecordPersistence`: bounded `AtomicFile` persistence under `noBackupFilesDir`; no exported storage endpoint and no backup copy.
- Pure-JVM transaction tests with synthetic in-memory keys and failure injection.

## Commit ordering and recovery

1. Inspect the append-only marker aliases and active record.
2. Require the proposal to match the exact state transition: first install generation 1; rotation current+1; recovery highest-marker+1.
3. Create a new StrongBox HMAC marker alias for the next generation and compute a record-bound HMAC proof.
4. Obtain/create the StrongBox AES-GCM key and encrypt the bounded canonical record with generation-bound associated data.
5. Atomically replace the encrypted active record.
6. Reopen, decrypt, validate the canonical public-key fingerprint, and verify the matching marker HMAC before returning committed.

The marker is deliberately created before record persistence. A crash or failure after marker creation leaves the watermark ahead of the active record. The older record is not loaded; the store returns a recovery-required state. Recovery must advance to the next generation and requires a new SEC-020A proposal. Old marker aliases are never deleted during normal rotation.

A missing or unreadable record with a non-zero marker is not treated as first install. A record without any marker is corrupt. A Keystore inspection failure or storage I/O failure returns unavailable and refuses mutation.

## Security boundaries and limitations

- The store contains only a public authority key, key identifier, generation and fingerprint; AES-GCM provides authenticated encryption and binds the generation in AAD.
- HMAC marker keys and the AES key are requested with `setIsStrongBoxBacked(true)` and their `KeyInfo.securityLevel` is checked. StrongBox absence, unsupported algorithms or key inspection errors fail closed; no TEE/software fallback.
- Marker aliases are retained and enumerated as the generation watermark. This detects rollback of the app-private encrypted record while the Android Keystore marker aliases remain present. It does not survive app uninstall, factory reset, a compromised OS/root attacker deleting aliases, or loss of the device-backed Keystore. These cases require the separately documented fresh owner-controlled first-install/recovery ceremony; this implementation does not claim hardware monotonic counters.
- `AtomicFile` provides same-filesystem replace/recovery semantics. The coordinator serializes operations in one app process; the Android adapters are not exposed as a multi-process service.
- The SEC-020A `ownerConfirmation` boolean remains only a policy input. This store does not prove a foreground UI tap or fresh system-credential result.
- No authority is provisioned by this commit, no UI imports a key, no remote enrollment path is connected, and no agent action can be executed.
- JVM tests use synthetic software keys and do not exercise Android Keystore, StrongBox hardware, crash behavior on a Pixel, or physical device recovery.

## Acceptance

Required before this slice can be treated as accepted:

- Phase 1 push and PR workflows pass Kotlin/JUnit, Python policy/static checks, strict Gradle dependency verification and Android assembly.
- CI-003 push and PR workflows pass independent unsigned builds, SBOM/provenance and artifact comparison.
- QA-005 emulator workflow passes its applicable launcher checks. Emulator results do not substitute for StrongBox hardware validation.
- A separate security reviewer inspects marker lifecycle, generation alias parsing, AtomicFile failure semantics, backup/uninstall assumptions and the non-connection to execution.
- Physical Pixel 9 Pro validation is a later M7 gate; no physical-device result is claimed here.

Release state remains `release_ready=false`; artifacts remain unsigned and not for release.
