# SEC-014H — opt-in local StrongBox key enrollment (development-only)

Scope: `feat/phase1-agentic-phone`. A **non-exported** Activity can be opened
from the launcher by a deliberate local tap. It requires an unlocked, secure,
interactive Android user, a fresh system credential result within 30 seconds,
and a second platform-state check before provisioning.

The provisioning routine generates a non-exportable P-256 AndroidKeyStore key
with per-use biometric-strong/device-credential authentication and **requires
StrongBox**; it refuses software/TEE fallback. It never overwrites or deletes
an existing alias. A post-generation read-only check must confirm hardware
backing and authentication policy before reporting local enrollment. A failed
verification leaves any created alias inert and requires manual investigation;
no automatic destructive cleanup is performed.

**Critical limitations:** A local device-credential holder is not yet a
verified remote owner identity. A key alias or a locally reported KeyInfo
property is not remote attestation. This does not sign commands, issue
consent, grant screen capture/accessibility permissions, enable an executor,
create a network service, or prove secure enrollment on Pixel 9 Pro.
The 30-second credential intent is not a general authorization session.
There is no key rotation, deletion, recovery or remote revocation UI.
StrongBox and system credential APIs require Android runtime and Pixel
hardware validation; source and JVM policy tests cannot establish this.

Acceptance checks: pure Kotlin one-shot intent tests, Python source boundary
checks, Android build/JUnit CI, manifest security gate and no new permissions.
Independent security signoff remains pending; SEC-014 and M1–M8 remain open.

Next: device-backed test of StrongBox generation and Android credential
prompt; attestation-chain validation and owner identity binding; protected
per-action signing, revocation, replay controls and permission enforcement
before any agent integration. No physical flashing or root escalation.

SEC-014I follow-up: exact StrongBox security-level verification and device-credential
authentication checks require API 31+; optional enrollment is blocked on older
Android versions. See [SEC-014I](SEC-014I-STRONGBOX-IDENTITY-BOUNDARY.md).
