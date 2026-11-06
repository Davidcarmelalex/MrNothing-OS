# SEC-014C — owner credential safety preview (NOT consent issuance)

The launcher now opens a non-exported owner-facing Activity for local preview
of read_screen, navigate and scroll. Only a secure Android device credential
prompt can show a temporary preview success message. The state machine rejects
cancel, expiry after 30 seconds, monotonic clock rollback, overlapping attempts,
revocation and process recreation.

This does NOT issue or sign a consent capability, enroll an owner, check or
grant Android Accessibility/MediaProjection permissions, enable screen/UI
actions, call the agent executor or persist consent. AgentPolicy and
CommandRouter remain fail-closed for screen actions. The current Android user
credential is not proof of separately enrolled owner identity.

Kotlin pure JUnit tests and Python source/manifest tests are included. Android
compile/emulator runtime requires separate CI evidence; no physical Pixel used.
Independent security approval remains pending.

Next: design and test Keystore-backed, device/owner/session-bound consent
issuance, explicit owner intent, permission checks, visible indicator,
restricted-screen denial and immediate revocation before any executor integration.
