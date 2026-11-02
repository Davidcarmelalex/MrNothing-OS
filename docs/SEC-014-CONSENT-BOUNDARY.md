# SEC-014A — screen/UI policy fail-closed boundary

**Status:** partial remediation, NOT SEC-014 closure or device integration.
**Scope:** `feat/phase1-agentic-phone`, no Android permission changes.

## Verified policy contract

- `get_battery` and `open_app` remain the only low-risk actions.
- `read_screen`, `navigate`, and `scroll` return `approval_required`
  for authenticated requests and `deny` for unauthenticated requests.
- A contact approval flag does **not** authorize screen reading or UI control.
- The current HERMES gateway and Android CommandRouter do **not** execute
  screen-reading, navigation, or scrolling. No accessibility or screen-capture
  permission is enabled by this change.
- Python and Kotlin policy tests enforce the same decisions.

## Remaining consent acceptance gates — not implemented

A trusted **owner-facing Android UI**, not an LLM command or transport
payload, must issue a short-lived consent capability bound to device, owner,
session, exact action scope and monotonic expiry. It must verify Android
runtime/Accessibility/MediaProjection permissions as applicable, show a
persistent indicator, provide immediate revoke/kill-switch, and reject
restricted screens, banking/biometric/CAPTCHA bypass and locked devices.
Do not persist screen contents by default. Revocation, timeout, replay,
cross-session, spoofed-approval and process-restart behavior need tests on
both Python and Kotlin boundaries. No executor integration until an
independent security verifier signs off on these gates.

This change is deliberately fail-closed: returning `approval_required`
is **not** a consent grant and cannot itself enable execution.

## SEC-014B — offline one-use consent verifier (2026-11-02)

`core/owner_consent_verifier.py` is an **isolated, non-integrated** verifier
for future trusted owner-UI signed capabilities. It checks device/owner/session
identity, exact screen-action scope, HMAC authenticity, a maximum 30-second
monotonic validity interval, one-time nonce consumption, explicit session
revocation, capacity fail-closed, and process-epoch invalidation after restart.
The verifier never issues tokens, grants Android permissions, reads screens,
controls UI, or executes device actions. Tests mint synthetic HMAC fixtures.

**Critical unresolved trust boundaries:** the future Android owner-facing UI
must authenticate the local owner, obtain actual Android permission, protect
the signing key in Keystore, ensure the verifier's epoch is bound to the trusted
UI session, and pass trusted context rather than model-supplied values.
Current Python prototype shares a symmetric verification key in memory;
this is NOT a secure Android Keystore integration. Cross-process persistence,
restricted-screen detection, persistent user-visible indicator, kill switch,
actual permission revocation, Kotlin parity, and independent security review
remain open. No production consent or SEC-014 closure is claimed.
