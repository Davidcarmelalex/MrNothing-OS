# SEC-014F — fail-closed screen integration prerequisite preflight

**Scope:** feat/phase1-agentic-phone; no live screen executor, consent issuer,
permission request, AccessibilityService, MediaProjection session or manifest
permission added.

The new Kotlin ScreenActionPreflight is a **non-integrated readiness policy**,
not a consent grant. It rejects missing trusted owner session, unsafe device
state, absent visible indicator, restricted surfaces, emergency stop, revoked
sessions and absent app-owned AccessibilityService. For read_screen it
additionally requires a separately authorized active projection session.
Unknown actions fail closed. A read-only Android platform probe inspects the
enabled accessibility services and requires an exact match to the app's
future service class and package. That service is intentionally **not
declared**: current runtime readiness is therefore false.

PRECONDITIONS_PRESENT is **not** permission to execute. Any future executor
must independently verify Android runtime grants, trusted user intent, an
owner/device/session-bound one-use signed capability, scope, expiry, replay,
revocation and restricted-screen rules at execution time. Never source policy
signals from an LLM or remote request. No banking/biometric/CAPTCHA bypass.

Verification: 10 pure Kotlin JUnit cases, four Python source-boundary cases
and the existing full preflight. Kotlin compilation and Android emulator
behavior require separate CI evidence. No TalkBack speech, actual screen
capture, real Pixel or production security claim is made.

**Still blocked:** Keystore-backed owner enrollment and key lifecycle;
trusted owner intent and consent issuance; Android permission grant flow;
MediaProjection foreground service and user-visible stop indicator;
restricted-screen detection; immediate revocation; integration tests;
independent security review. SEC-014 remains open.
