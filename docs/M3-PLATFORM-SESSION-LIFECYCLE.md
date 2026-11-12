# M3 — App-owned platform session lifecycle contract

**Status:** lifecycle registry primitive implemented; Android service providers are not implemented or declared.

## Purpose

The action-specific permission gate needs a fresh answer to two questions that Android does not expose as a durable Boolean permission:

- Is Mr Nothing OS's own AccessibilityService currently connected?
- Is an actual user-approved MediaProjection session currently active?

An enabled service in Settings is not proof that the service is connected. A historical MediaProjection approval is not proof that a live projection remains active.

## Implemented primitive

`ActionPermissionSessionRegistry` is a pure-Kotlin, process-local lifecycle registry. It maintains independent ACCESSIBILITY and PROJECTION leases.

- A lease is opened only by a future app-owned platform provider after its successful lifecycle callback.
- Each replacement receives a monotonically increasing process-local generation.
- Only the exact current lease object may end a session.
- A late disconnect/stop callback from an older lease cannot revoke a newer replacement.
- Exact application-package matching is required for begin, end and observation.
- The existing permission-probe interfaces can be backed by registry snapshots.
- The registry is synchronized; every observation reads current state.
- A new process/registry begins empty. No lease is serialized, persisted or restored.

The lease is an in-process lifecycle handle, **not** authentication, owner consent, a permission grant, a cryptographic credential or an execution capability. Internal Kotlin visibility is not a security boundary against code in the same application.

## Required future provider wiring

### Accessibility

A future service implementation may open a lease from `AccessibilityService.onServiceConnected()` only after Android has actually bound the service. It must retain that exact lease and end it on unbind/destruction. A new connection replaces the old lease. A stale callback must not close the replacement.

Before implementation, require:
- A separate owner-facing explanation of the accessibility capability and its scope.
- Explicit user navigation to Android Settings; never enable the service programmatically.
- A visible, revocable in-app control and clear active-state indicator.
- A reviewed, narrowly scoped service XML configuration.
- Restricted-surface and emergency-stop policy.
- TalkBack coexistence and spoken-navigation tests.

No AccessibilityService is declared in the current manifest.

### MediaProjection

A future projection owner may open a lease only after the system consent result is successful, `getMediaProjection` returns a live session, and the stop callback has been registered. It must end the exact lease from `MediaProjection.Callback.onStop()`, on explicit owner stop, and on service teardown.

Before implementation, require:
- A fresh Android system consent flow for every new projection session as required by platform policy.
- A visible foreground-service notification and owner stop control where required.
- Explicit foreground-service lifecycle and process-death handling.
- No background or silent recapture.
- No persistence or restoration of a projection lease.

No MediaProjection service or permission is declared in the current manifest.

## Failure and lifecycle rules

| Event | Required behavior |
|---|---|
| Provider has not connected | Probe returns false |
| Callback package mismatch | Lease creation/revocation denied |
| Service/projection stops | Exact current lease removed |
| Old callback arrives after replacement | Ignore stale lease; retain current session |
| Process dies or registry is recreated | All observations return false until a new real callback |
| Provider callback throws or is unavailable | Probe adapter returns/retains denial; caller fails closed |
| Emergency stop | Future coordinator must revoke the exact active leases and deny new ones |

The registry does not itself implement Android callbacks, a foreground service, owner UI, or emergency-stop UI. It must not be wired to agent/request data.

## Acceptance evidence

- 11 pure-JVM lifecycle tests: package binding, default denial, current lease revocation, stale callback protection, independent session kinds, wrong-kind/package rejection, probe adapters, monotonic generations and process recreation.
- 5 Python source-boundary tests: no Android framework dependency, no device-side-effect APIs, no persistence, no service/permission declaration and no dispatcher wiring.
- No manifest change.
- No request dispatcher or executor integration.

## Next gate

Implement the real Android provider lifecycle only after the owner-facing disclosure/revocation UX and service configuration receive independent security and accessibility review. Then test service bind/unbind, process death, projection stop, notification visibility, revocation races and TalkBack. Keep the command router fail-closed throughout.
