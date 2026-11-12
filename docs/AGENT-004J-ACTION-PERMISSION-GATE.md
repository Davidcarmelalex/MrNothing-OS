# AGENT-004J — action-specific Android platform prerequisite gate

**Status:** implemented as a non-integrated, fail-closed preflight. `CommandRouter` remains unchanged and rejects every request because a verifier-created Android session capability is not integrated.

## Why this extends rather than duplicates SEC-014F

`ScreenActionPreflight` remains the existing coarse screen-safety policy. It consumes safety/consent signals and has a read-only enabled-accessibility-service observation. AGENT-004J adds a separate action-specific platform probe over the already-closed `OwnerActionArguments` model. It does not replace `ScreenActionPreflight`, mint consent, or authorize execution.

## Action-specific observations

- `navigate(target_package)`: use `PackageManager.getLaunchIntentForPackage` for the exact canonical package, require an explicit component in that package, and re-read its `ActivityInfo` to require an exported/enabled activity and enabled application. If the target activity declares a permission, verify that this app already holds it. Package-not-found, visibility denial, security exceptions and platform failures return blocked. The manifest's existing launcher-intent `<queries>` declaration is retained; no `QUERY_ALL_PACKAGES` permission is added. No activity is started.
- `scroll(direction, distance_dp)`: require the exact app-owned AccessibilityService to be enabled through the existing `ScreenActionPreflight` probe **and** an app-owned connection probe to report that service connected. The connection probe defaults to false. No service is declared or enabled by this change.
- `read_screen`: require an app-owned probe to report a currently active, user-approved MediaProjection session. The probe defaults to false. No projection prompt, foreground service, capture or session is created.

The pure-JVM `ActionPermissionGate` validates the existing typed argument model before querying only the relevant probe. It performs fresh reads on every evaluation, does not cache a positive result, and converts `SecurityException`/runtime platform failures into `PLATFORM_STATE_UNAVAILABLE`.

## Security boundary

`PlatformPrerequisitesPresent` means only that action-specific Android platform prerequisites were observed at that instant. It is not authentication, owner consent, a signed capability, a dispatch reservation, or permission to execute. The result is not persisted. It must never be sourced from an LLM, a remote payload or a caller-supplied Boolean.

A future coordinator must still revalidate the verifier-owned live transport/session and consent binding, reserve the one-use capability, recheck Android state immediately before dispatch, and atomically claim the durable reservation. Revocation, missing services, unavailable package visibility, absent projection state and platform errors remain fail-closed. `CommandRouter` is deliberately not connected.

## Verification

- Seven pure-JVM JUnit tests cover exact package visibility/launchability, invalid arguments, enabled and connected accessibility requirements, active projection requirement, fresh-state rechecks, exception denial and unknown/malformed actions.
- Six Python source-boundary tests assert exact-package lookups, default-deny service/session probes, no permission prompt or device-side effect, no broad package visibility permission, and continued CommandRouter rejection.
- Local Kotlin compiler checks used a pure-JVM harness and minimal Android API stubs; these are not an Android SDK build. Android framework adapter compilation is delegated to the repository's pinned Gradle CI.

No manifest permission, accessibility service, MediaProjection service, listener, executor, runtime grant, screen capture, navigation, scroll, shell bridge, physical-device operation or production deployment is added. Independent human security review remains pending.
