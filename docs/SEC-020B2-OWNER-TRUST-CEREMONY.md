# SEC-020B2 — owner-visible offline authority trust ceremony

**Status:** implementation submitted on the authorized feature branch; exact-head CI and independent review pending.

## Scope

SEC-020B2 adds a non-exported Android Activity for an owner-visible, offline authority trust transition. It consumes the existing SEC-020A policy and SEC-020B1 storage adapter. It does not create an authority key, provision a production secret, enroll a remote device, grant Android permissions, connect a network listener, or enable command execution.

The UI accepts:
- A bounded authority key identifier.
- A positive decimal generation with no leading zeros.
- Canonical Base64 Ed25519 SPKI DER.
- An optional canonical Base64 64-byte rotation signature (required by the SEC-020A rotation policy when an active authority exists).
- A separately obtained SHA-256 fingerprint.
- An explicit checkbox attesting that the owner compared the fingerprint through a separate trusted out-of-band channel.

The candidate fingerprint is calculated locally from the canonical SPKI DER. The screen instructs the owner to obtain the same fingerprint through a separate trusted channel. The typed fingerprint must match exactly before the transition can be reviewed.

## Credential-bound transaction

1. The Activity requires a foreground, unlocked, interactive device with a secure system lock.
2. It inspects the current trust-store state and prepares a non-committing SEC-020A preview with owner confirmation false.
3. It binds the mode, trust-store snapshot and digest of every imported field to a one-shot 30-second monotonic confirmation state.
4. It opens the Android system device-credential confirmation UI.
5. After return, it requires RESULT_OK, a fresh safe-device-state check, the unchanged out-of-band confirmation checkbox and a matching one-shot binding.
6. It reparses the fields, reinspects the store, compares the complete binding and only then asks SEC-020A to produce a Ready proposal.
7. SEC-020B1 commits the proposal and verifies the persisted record by reopening it.
8. Cancellation, timeout, changed fields, changed store state, unavailable Keystore, malformed input or any blocked transition refuses without reporting success.

The one-shot state is process-memory only. Activity destruction revokes it. No pending confirmation is restored after process death or configuration recreation.

## Input and accessibility controls

- Base64 input must be canonical, padded standard Base64, single-line and bounded.
- SPKI DER is validated by the existing Ed25519 canonical-key policy.
- Fingerprints must use the exact SHA256: plus 64 uppercase hexadecimal format.
- Rotation signatures must decode to exactly 64 bytes.
- Generation parsing rejects signs, whitespace, zero, leading zeros and overflow.
- Sensitive screen uses FLAG_SECURE, obscured-touch filtering, accessible labels, live status regions, large touch targets and ordinary system font scaling.
- The Activity is explicitly non-exported and adds no Android permission.

## Explicit limitations

The checkbox is an owner attestation; Android cannot prove that the separate fingerprint source was independently authenticated. The UI does not implement QR/file import, certificate transparency, authority discovery, remote attestation or production key management. Rotation and recovery policy remain subject to independent review. The storage adapter still requires physical StrongBox validation and crash/recovery testing on the Pixel 9 Pro.

The new JVM tests exercise strict parsing and the one-shot state machine with synthetic keys and a fake monotonic clock. Python source tests verify the manifest and code boundaries. Neither proves Android system-credential behavior, real StrongBox security level, AtomicFile crash semantics, spoken TalkBack navigation or physical-device compatibility.

The Activity currently performs its small bounded trust-store inspection/commit synchronously. Before production integration, evaluate moving storage operations to a lifecycle-safe serialized worker without allowing a canceled or backgrounded UI to commit after consent has been withdrawn.

## Safety boundary

The executor remains disconnected. No remote enrollment, permission grant, accessibility service, screen capture, telephony action, shell, root, firmware flash, OTA, production signing or deployment was added. Release provenance remains not-for-release. Independent security review remains pending.
