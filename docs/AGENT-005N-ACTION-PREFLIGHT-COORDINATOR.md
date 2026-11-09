# AGENT-005N — composed Android action preflight

**Status:** Implemented as a non-integrated, no-side-effect policy coordinator. It is not authorization and does not enable dispatch.

## Why this task

The branch already contained two distinct gates:

- `ScreenActionPreflight` evaluates trusted owner/session, device safety, visible consent indicator, restricted-surface, emergency-stop, revocation and app-owned accessibility-service signals.
- `ActionPermissionGate` performs fresh action-specific Android platform observations for exact launch targets, connected app-owned AccessibilityService, and active user-approved MediaProjection.

They were independently tested but had no single composition point. AGENT-005N adds that composition without duplicating either policy or changing the deliberately fail-closed CommandRouter.

## Implementation

`ActionPreflightCoordinator`:

1. Rejects invalid/mismatched typed action arguments before reading any state.
2. Reads one current snapshot from an app-owned `ScreenSafetySignalProvider`.
3. Denies missing, null, or throwing safety state.
4. Applies `ScreenActionPreflight`; a safety denial short-circuits Android platform probes.
5. Applies `ActionPermissionGate`, which re-reads only the action-specific OS prerequisites.
6. Returns `ReadyForIndependentAuthorization` only when both policies pass. The name and KDoc deliberately state that transport identity, owner consent, durable dispatch admission and execution are still separate.

The default provider is `DenyAllScreenSafetySignalProvider`. No production signal provider exists or is connected. The interface must be implemented only from app-owned runtime state; model output, remote request fields and caller-provided booleans are not evidence.

## Regression coverage

Eleven pure-JVM tests cover:
- Both policies must pass.
- Safety denial short-circuits platform reads.
- Platform denial blocks after safety passes.
- Null/throwing/default-deny safety providers fail closed.
- Invalid and unsupported actions are rejected before reads.
- Navigation requires safety plus exact launch-target readiness.
- Scroll requires the app-owned service to be enabled and connected.
- Readiness is re-evaluated on each call.
- Platform probe exceptions remain denied.

Seven Python source-boundary tests verify composition order, default-deny behavior, argument validation order, exception handling, provider provenance, result semantics and absence of dispatch/platform side effects.

## Explicit non-goals and limitations

- No Activity, service, manifest permission, AccessibilityService, MediaProjection provider, prompt, listener or executor is added.
- No caller of this coordinator is wired into `CommandRouter`; that router continues to reject every request with `VERIFIED_TRANSPORT_SESSION_REQUIRED`.
- The default provider denies all requests. Test fakes are not production evidence.
- `ReadyForIndependentAuthorization` is not a capability and must never be persisted or passed as permission to execute.
- A future executor must re-read all state at the actual side-effect boundary and compose it with the verifier-retained live capability, owner enrollment/revocation, exact action/argument digest, durable idempotency, cancellation and audit.

## Acceptance

The implementation is accepted only when exact-head Phase 1 Python and Android jobs pass, strict dependency verification and tampered-artifact negative control pass, CI-003 independent-runner reproducibility passes, and QA-005 emulator workflow passes. This does not constitute independent security review, spoken TalkBack acceptance, physical Pixel 9 Pro validation or production readiness.
