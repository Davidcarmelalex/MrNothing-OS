# SEC-014D — fail-closed local device-lock preflight (preview only)

**Scope:** `feat/phase1-agentic-phone`. The owner credential **preview** now
reads real Android `KeyguardManager`, `UserManager`, and `PowerManager`
state immediately before opening the system credential prompt and again after
the result. It refuses to display a successful preview unless the device has
a secure credential, the device and keyguard are unlocked, the Android user is
unlocked, and the display is interactive. Missing services and runtime failures
fail closed. The state evaluator has seven pure Kotlin JUnit tests and three
Python static boundary tests.

**Trust boundary:** This does not enroll or identify an owner, sign or issue a
consent capability, prove Android accessibility/MediaProjection permission,
detect restricted app screens, enable device execution, or authorize any action.
The Python HMAC verifier is an isolated synthetic prototype, not connected to
the Android UI. Do not pass model- or network-provided booleans to the evaluator.

**Evidence limits:** Kotlin tests and Android compilation require exact-head
GitHub CI. A real Android emulator credential-prompt interaction and physical
Pixel validation have **not** been demonstrated for this change. The earlier
emulator launcher smoke suite is not a test of credential preview lock-state
transitions. Independent security review remains pending. SEC-014 stays open.

**Next gate:** trusted owner enrollment, Keystore-protected signing, explicit
per-action consent, platform permission enforcement, visible indicator,
restricted-screen denial, revocation and end-to-end negative testing. Do not
wire any screen/UI executor until independent approval.
