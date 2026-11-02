# SEC-014J — fail-closed owner-key alias collision preflight

Scope: `feat/phase1-agentic-phone`, development-only Android owner enrollment.

Before starting a system credential prompt, inspect the existing AndroidKeyStore
alias read-only. Four explicit states distinguish an absent alias, a verified
existing StrongBox key, an existing alias that fails StrongBox/authentication
policy, and a Keystore inspection failure. Only **absent** may proceed to the
credential prompt. Existing aliases are preserved, even if malformed or TEE-only.
Inspection errors are not treated as absence. The provisioning routine retains
its independent post-credential alias check to protect against a race.

Acceptance evidence: four pure Kotlin/JUnit policy tests, three Python source
boundary tests, full Python preflight, manifest and accessibility checks,
and exact-head Android CI. This does not exercise AndroidKeyStore or a Pixel.
No key deletion, migration, remote identity binding, consent issuance,
agent execution, root operation or flashing is added.

Limitations: this is a local policy guard, not attestation, owner identity
proof, or revocation. A trusted device-backed attestation challenge and
independent security review remain required before signing any agent command.
