# SEC-014G — read-only AndroidKeyStore owner-key readiness

**Scope:** feat/phase1-agentic-phone. Bounded M6 security slice, not owner enrollment or SEC-014 closure.

OwnerKeystorePreflight.inspectExisting() reads only a fixed alias from AndroidKeyStore.
It fails closed when absent, invalid, not P-256 EC, not hardware-backed,
not requiring owner authentication, or not configured for per-use authentication.
Exceptions also deny readiness. It never generates, exports, signs with,
deletes, or rotates a key.

The positive EXISTING_KEY_REQUIRES_OWNER_AUTH state is intentionally
**not** a consent grant, owner identity verification, key attestation, or
permission to control a screen. No production component calls this
preflight, no enrollment flow creates the alias, and no device executor
is enabled. An alias name alone is not a secure enrollment protocol.

## Acceptance evidence and limitations

- Eight pure Kotlin policy tests cover the positive readiness state and
  each missing requirement; these require Android CI to execute.
- Four Python source-boundary tests ensure inspection stays read-only and
  is not wired to agent execution or the credential-preview Activity.
- The existing launcher manifest must remain without accessibility
  services, MediaProjection grants, or elevated device permissions.
- No AndroidKeyStore runtime, hardware-backed key, biometric prompt,
  physical Pixel 9 Pro, emulator key enrollment, or attestation is proven
  by these source/policy tests.

## Next security gates

Implement trusted local owner-initiated enrollment, Android credential
confirmation, protected P-256 key creation and attestation policy,
explicit per-action consent signing after fresh authentication, persistent
revocation, and negative/replay/lock-state tests. Validate KeyInfo behavior
on Android 15 emulator and actual Pixel 9 Pro hardware. Never fall back
to software-only keys silently. Independent security review is mandatory
before integrating any device command executor.
