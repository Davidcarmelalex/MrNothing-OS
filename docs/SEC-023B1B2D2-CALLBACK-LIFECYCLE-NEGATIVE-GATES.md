# SEC-023B1B2D2 — Negative callback lifecycle regression gate

Status: DRAFT / independent security review pending. Stacked on dormant MemoryVault composite PR #21; target is `feat/phase1-agentic-phone`. This change adds **only pure JVM regression tests and documentation**, not a runtime permission, key, service, or credential prompt.

## Scope and evidence contract

Eight new tests exercise process recreation (no restoration of in-memory prompt authority), cancellation before callback, terminal cancellation before arming, forged value-equality vs reference identity, exact 30-second boundary, one-nanosecond expiry, near-`Long.MAX_VALUE` monotonic time, and incorrect credential type followed by replay. The only positive outcome remains `AWAITING_AUTHENTICATED_CIPHER_OPERATION`, which is **not** authorization to persist memory.

The tests use synthetic `Any` objects and a controlled clock. They do **not** exercise AndroidKeyStore, BiometricPrompt, StrongBox, device credentials, physical Pixel 9 Pro, same-UID/cross-UID IPC, app backgrounding, or real process killing. Those acceptance gates remain open.

## Unresolved security questions

- Key alias replacement between prepare and complete is not closed by a second metadata inspection; a different key can occupy the same alias. Do not claim key continuity from alias or KeyInfo alone.
- A concurrent cancellation racing an already-running cryptographic operation requires a trusted lifecycle/owner-state gate at the future authorization boundary. These JVM tests prove only ordered cancellation.
- Real process-death recovery must never resurrect a pending CryptoObject; future Activity integration needs an explicit onStop/onDestroy/recreation policy.
- Device-credential-only per-use CryptoObject interoperability and hardware StrongBox provenance require an owner-consented physical Pixel 9 Pro test and independent security review.
- MemoryVaultService stays disabled and non-exported; PaperClip memory stays RAM-only; Android executor remains disconnected.

## Acceptance

Run the new `MemoryVaultCryptoCallbackNegativeGateTest` through hosted `:app:testDebugUnitTest` and verify exact-head CI. Run existing Python source/security checks and a separate clean-checkout verification. Do not count new JVM tests as executed unless a Gradle task or JUnit evidence proves it. No independent signoff, release, flash, or production enablement is authorized. Upstream shared `SKILL.md` remains unverified; local `PROJECT-ADAPTER.md` is not that package.

Milestones M1/M2/M6 remain in progress, M3 partial, M4 not started, M5 not accepted, M7/M8 blocked. None complete.
