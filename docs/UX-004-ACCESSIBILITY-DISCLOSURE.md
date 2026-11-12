# UX-004 — Owner-visible Accessibility disclosure and revocation handoff

**Status:** Disclosure/status screen implemented. No AccessibilityService is declared or enabled by this change.

## Owner-facing behavior

The launcher exposes a non-exported Accessibility access and revocation screen. It explains that Android Accessibility access is powerful and that a registered service could observe interface content and perform UI actions within its declared scope.

The screen makes the current build's boundary explicit:
- No OwnerScreenControlAccessibilityService is declared in the app manifest.
- This build cannot read the screen or control other apps through Accessibility.
- The owner may open Android Accessibility Settings only by pressing the explicit review button.
- Opening Settings does not grant access. Android remains the sole authority for enabling or disabling an AccessibilityService.
- The screen re-reads service declaration/enabled state on every resume.
- An enabled-in-settings observation is not represented as a live service connection or action authorization.
- Any platform inspection failure is displayed as unavailable, never as enabled.

If a future reviewed build registers the service, the owner can disable it in Android Settings under Accessibility. This screen is a Settings handoff, not a programmatic enable/disable API.

## Status model

| Status | Meaning |
|---|---|
| NOT_REGISTERED | Exact app-owned service component is absent from the package manifest |
| REGISTERED_DISABLED | Component is declared but not listed as enabled by Android |
| ENABLED_IN_SETTINGS | Android lists the exact component as enabled; connection is not implied |
| UNAVAILABLE | Package/AccessibilityManager state could not be safely verified |

The component name is centralized in AccessibilityServiceContract and shared with ScreenActionPreflight to prevent identity drift.

## Security boundary

This change adds only a non-exported Activity and read-only package/AccessibilityManager observations. It does not add an AccessibilityService class or manifest service declaration, BIND_ACCESSIBILITY_SERVICE or other new Android permissions, a permission prompt, automatic Settings launch, programmatic service toggle, MediaProjection, a foreground service, screen capture, gesture execution, session lease, consent capability, action reservation or command-router call.

The existing ActionPermissionSessionRegistry remains process-local and disconnected from any Android provider. CommandRouter remains fail-closed.

## Accessibility and recovery

- Scalable SP typography and scrollable content.
- Explicit section headings and live status announcement.
- 56dp minimum action targets and descriptive content descriptions.
- Obscured-touch rejection on Settings/return controls.
- Android Settings fallback if the Accessibility Settings intent is unavailable.
- No automatic navigation to Settings.

## Acceptance evidence

- Pure-JVM tests cover not-registered, disabled, enabled, fresh reads and fail-closed platform errors.
- Instrumentation tests verify current-build disclosure and that the Settings intent is requested only after an explicit button tap.
- Python source-boundary tests verify non-exported Activity registration, no service/permission declaration, exact component identity and no command-router connection.
- Exact-head GitHub Actions and QA-005 emulator validation are required after commit.
- This is not spoken TalkBack acceptance. QA-011/QA-012 remain preflight/structural checks only.

## Gate before a real service

Do not declare or enable an AccessibilityService until an independent security and accessibility review approves a narrowly scoped accessibility-service XML configuration, event types, window-content access, gesture/global-action surface, owner-visible active indicator, immediate stop/revocation path, TalkBack coexistence and process-death behavior. Keep the command router fail-closed.
