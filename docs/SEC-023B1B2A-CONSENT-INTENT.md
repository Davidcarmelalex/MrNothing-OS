# SEC-023B1B2A — dormant MemoryVault consent-intent binding

Scope: scoped branch derived from feat/phase1-agentic-phone; separate draft PR.
This is a pure-JVM, no-side-effect owner-visible preview and one-shot intent
binding, not a production consent UI, Android credential ceremony, key
provisioning, CryptoObject authentication, or authorization.

## Security contract

- Explicit opt-in is required, with owner user 0, unlocked device, foreground
  owner UI, secure credential, StrongBox availability, absent alias, strict
  lowercase app-signing SHA-256 and a 256-bit nonce represented as lowercase
  hex. Retention must be 1–90 days.
- A domain-separated, length-prefixed SHA-256 digest binds the exact operation,
  future key alias, owner, signing identity, retention and request nonce.
  The eventual trusted Android UI must display and preserve these terms and
  derive security signals from Android, not from an agent or remote caller.
- A single attempt per instance uses the existing monotonic 30-second
  OwnerAuthorityConfirmationState; mismatch, expiry, rollback, cancellation,
  backgrounding and revocation consume the pending intent. A new request
  requires a new trusted ceremony instance and fresh CSPRNG nonce.
- The strongest return value is AWAITING_CRYPTOOBJECT_PROOF. It NEVER
  authorizes key generation, encryption, persistence or agent execution.
  The platformCredentialReported argument is a testable assertion, not a
  cryptographic proof. Never treat it as one.
- No IPC, new permission, Activity, service activation, KeyStore operation,
  key alias mutation, memory file, network access, Android device action or
  production behavior is introduced.

## Independent gates (all pending)

1. Review exact canonical digest, input provenance, CSPRNG nonce generation,
   same-UID caller assumptions, replay across process death and UI lifecycle.
2. Reconcile the key alias and provisioning signals with unmerged PRs #15–#18
   before integration; do not assume separate draft branches are combined.
3. Implement an accessible trusted Android owner UI with actual cancellation,
   foreground lifecycle and verified credential/CryptoObject binding. Confirm
   Android/StrongBox DEVICE_CREDENTIAL compatibility on real Pixel 9 Pro.
4. Prove Keystore key invalidation, owner revocation, negative IPC, rollback,
   crash-safe retention/export/delete and independently reviewed crypto.
5. Keep MemoryVault disabled and PaperClip RAM-only until security approval.

## Acceptance

New JVM regressions cover malformed identity/nonce, invalid retention, missing
consent/device preflights, exact snapshot mutation, cancellation, expiration,
clock rollback, replay and concurrent one-shot completion. Source-only Python
checks enforce dormant side-effect boundaries. Hosted exact-head Android
Gradle/JUnit, independent security review and hardware acceptance must be
recorded separately; source tests alone are not cryptographic assurance.

Milestones: M1/M2/M6 IN PROGRESS, M3 PARTIAL, M4 NOT STARTED, M5 NOT
ACCEPTED, M7/M8 BLOCKED. No milestone independently COMPLETE. Project-specific
PROJECT-ADAPTER.md exists; upstream shared SKILL.md remains unverified.

## QA-023B1B2A — post-preview negative-path hardening (2026-11-10)

Ten additional pure-JVM regression cases require foreground loss, device lock,
checkbox withdrawal, credential removal, StrongBox loss, alias appearance and
owner-profile change at completion to consume the pending intent. Clock
exceptions, negative monotonic time at start and replay after the
AWAITING_CRYPTOOBJECT_PROOF result are also tested. Tests only: no production
policy, Android permissions, CryptoObject or persistence changed. The snapshots
remain synthetic and the future trusted UI must derive them from platform state.
Independent security and physical Pixel validation remain pending.
