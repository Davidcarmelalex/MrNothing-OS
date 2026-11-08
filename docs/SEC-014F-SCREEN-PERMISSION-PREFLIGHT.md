# SEC-014F — fail-closed, least-privilege screen/action preflight

**Scope:** `feat/phase1-agentic-phone`; no live screen executor, consent issuer,
permission request, AccessibilityService, MediaProjection session or manifest
permission is added by this policy.

`ScreenActionPreflight` is a **non-integrated readiness policy**, not a
consent grant or authorization decision. Every supported action requires a
trusted owner session, safe/unlocked device, visible consent indicator, no
restricted surface, no emergency stop and no revoked session. Missing or
unsafe common state blocks every action.

Sensitive Android prerequisites are action-specific:

| Action | Required preflight | Not required |
| --- | --- | --- |
| `navigate` | Exact target package and exported/enabled launch activity, checked by `ActionPermissionGate` | AccessibilityService and MediaProjection |
| `read_screen` | Active, user-approved app-owned MediaProjection session | AccessibilityService |
| `scroll` | Exact app-owned AccessibilityService enabled and connected | MediaProjection |

This is a least-privilege correction: app launch must not pressure the owner
to enable a highly privileged AccessibilityService, and MediaProjection-based
screen capture must not depend on an unrelated accessibility grant. Scroll
remains blocked unless the app-owned AccessibilityService is both enabled and
connected. The current repository intentionally declares no such service and
the Android session probes default to deny.

The read-only Android probe checks the exact future service class and package.
It never enables a service, requests a permission, starts an Activity, captures
screen content or performs a gesture.

**Security boundary:** a positive preflight result is not owner consent, a
signed capability, verified transport, durable dispatch admission or permission
to execute. A future executor must independently revalidate owner/device/session
binding, action and canonical arguments, one-use capability, expiry, replay,
revocation, Android runtime state and restricted-screen rules at the actual
side-effect boundary. Never source safety signals from an LLM or remote request.
No banking/biometric/CAPTCHA bypass is allowed.

**Verification:** pure Kotlin/JVM policy tests and Python source-boundary tests
cover action-specific requirements, common safety denials and the no-executor
boundary. Android framework compilation and disposable-emulator behavior are
separate CI gates. No spoken TalkBack, real screen capture, physical Pixel or
production security claim is made.

**Still blocked:** production owner/session provider; trusted owner intent and
consent issuance; Android permission-grant UX; MediaProjection foreground
service and visible stop indicator; AccessibilityService implementation and
disclosure; restricted-surface detection; immediate revocation at the eventual
executor boundary; independent security review.
