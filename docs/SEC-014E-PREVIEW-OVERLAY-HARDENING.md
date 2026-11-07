# SEC-014E — consent-preview screenshot and overlay hardening

**Scope:** `feat/phase1-agentic-phone`; owner credential PREVIEW only.

The non-exported owner preview now sets Android `FLAG_SECURE` to discourage
screenshots/screen recording of the credential-adjacent UI. Every preview button
uses `filterTouchesWhenObscured`, and an additional local touch gate refuses
both fully and partially obscured motion events. On a rejected touch, the
pending preview is revoked and the action label is cleared. Keyboard and
accessibility-service activation are not disabled by this touch-only filter.

## Verification and limits

Kotlin unit tests cover both obscuration flags and their combination; Python
source tests require screenshot protection, touch filtering, revocation and
continued absence of any screen/UI executor. GitHub Android build/JUnit CI
and actual Android overlay-injection behavior are separate gates. The overlay
filter is a defense in depth, not a proof against all tapjacking or malicious
accessibility services. This change does not enroll an owner, issue a token,
read a screen, control the UI, grant Android permissions or sign a capability.

SEC-014 remains open: Keystore-backed owner identity, permission enforcement,
visible consent, revocation, restricted-screen denial, real-device negative
tests and independent security review are not yet complete.
