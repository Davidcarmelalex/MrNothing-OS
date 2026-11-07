# M3 — Supervised Agent Execution Contract

**Status:** Design baseline only. No executor, listener, device bridge, permission grant, or production transport is implemented by this document.  
**Scope:** `Davidcarmelalex/MrNothing-OS`, `feat/phase1-agentic-phone`.  
**Target:** Native Android HOME launcher and the separately developed HERMES orchestration layer.

## 1. Purpose and security boundary

Define the contract that must exist before an AI-generated plan can cause an Android-side effect. The model may propose an action; it must never manufacture transport identity, owner consent, Android permission state, or an execution result.

The native Android app and the existing Termux/Python runtime are separate products at this stage. No direct bridge between them is authorized by this design.

## 2. Current implementation facts

| Component | Verified current behavior | Limitation |
| --- | --- | --- |
| `core/hermes_gateway.py` | Allowlist contains `get_battery` and `open_app`; validates bounded envelopes and a supplied authenticated flag | Returns admission readiness only; it does not execute a command |
| `core/agent_sandbox.py` | Validates bounded plans, deadlines and cancellation; returns simulated outcomes | Explicitly offline; `device_actions_executed=false` |
| `core/command_admission.py` | Verifies signed commands, freshness, policy and a durable single-host SQLite replay reservation | Caller-supplied `transport_authenticated` is a prototype input, not proof of identity; no executor |
| `core/owner_consent_transport.py` | Binds consent to an exact live mTLS socket; v1 remains read_screen/empty-arguments only; v2 mints one-use capabilities bound to signed canonical argument digests | No listener, Android permission check, production caller, or device executor |
| `core/action_reservation.py` | Persists a consent/transport/action-bound reservation and one-use lifecycle state; no raw arguments or results | Storage primitive only; not integrated with the trusted adapter, Android permissions, or an executor |
| `core/owner_action_arguments.py` | Defines strict v2 canonical JSON and domain-separated argument digests for read_screen, navigate and scroll | Pure protocol primitive; no action execution |
| Android `OwnerConsentSigner.kt` | Signs v1/v2 canonical challenges using the existing owner-authenticated Keystore path; v2 system prompt includes the exact canonical argument JSON | No production caller or executor; StrongBox behavior remains hardware-unverified |
| `core/owner_consent_verifier.py` | Verifies and consumes bounded one-use screen-action capabilities | In-memory prototype; not the Android Keystore authorization boundary |
| Android `CommandRouter.kt` | Accepts only UntrustedCommandRequest and rejects every request with VERIFIED_TRANSPORT_SESSION_REQUIRED | No verifier-created Android session capability is integrated; all agent dispatch remains disabled |
| Android owner-consent / trust UI | Local credential-confirmed preview and trust-store prototypes exist | Not connected to a live transport or device executor |

**Non-negotiable:** neither a Boolean named `authenticated` nor a JSON field, model output, UI label, package name, or caller-selected device ID is sufficient evidence of an authenticated owner session.

## 3. Legacy Termux runtime separation

The repository also contains a Python/Termux runtime:

- `agents/hermes/agent.py` supports a legacy `shell` task using `subprocess.run(..., shell=True)`.
- `agents/openclaw/agent.py` uses `subprocess.run(..., shell=True)` for its Termux command helpers.
- `core/main.py` starts agent scripts using `subprocess.Popen`.

These are not acceptable Android execution primitives. They remain outside the native Android app and outside any future supervised HERMES device executor. Do not import, package, invoke, or expose these scripts through an Android component. Any future migration must replace them with reviewed typed APIs; it must not wrap arbitrary shell strings in a new RPC.

### Boundary audit — 2026-11-07

The current build graph was inspected at branch head `dc175f388e780b041bcc398b96047ae1719099d6`:

- `android/settings.gradle.kts` includes only `:app`.
- The root Gradle build declares only the Android application and Kotlin Android plugins.
- `android/app/build.gradle.kts` has no Python plugin, interpreter/runtime dependency, external source-set directory, or root-repository source inclusion. Its application dependencies are BouncyCastle; JUnit is test-only; Android platform test APIs are compile-only.
- All 32 Kotlin files under `android/app/src/main` and `android/app/src/debug` were inspected for `ProcessBuilder`, `Runtime.exec`, `subprocess`, `shell=True`, Termux references, `agents/hermes`, and `agent.py`. No execution/bridge matches were found. The only Python mention was a comment describing cross-language canonical JSON compatibility.
- The main manifest contains no agent service or shell bridge. The debug manifest contains only the existing DUMP-protected credential probe and a non-exported test host.

**Decision:** the current Gradle module/source graph and Android source audit already demonstrate separation. No duplicate packaging-exclusion gate was added. Re-open this decision if a Python runtime/plugin, external source set, agent asset, Android IPC bridge, process-launch API, or new manifest component is introduced.

## 4. Required request model

The future transport-neutral request envelope should be versioned and bounded. The following fields are logical requirements, not an implemented wire schema:

| Field | Meaning | Source of truth |
| --- | --- | --- |
| `schema_version` | Protocol version | Compiled protocol |
| `request_id` | Unique request identifier | Trusted host / caller, validated |
| `device_id` | Intended enrolled device | Must match authenticated transport enrollment |
| `owner_id` | Intended owner | Must match trusted enrollment record |
| `session_id` | Short-lived owner session | Created by transport adapter; never model-supplied |
| `action_id` | Exact allowlisted action | Versioned action registry |
| `arguments` | Strict JSON-native bounded values | Validated against action schema |
| `arguments_digest` | Canonical digest of action arguments | Recomputed by verifier |
| `issued_at`, `expires_at` | Bounded validity window | Trusted clock policy |
| `idempotency_key` | Side-effect deduplication key | Validated and durably reserved |
| `policy_version` | Policy used for admission | Compiled policy registry |
| `correlation_id` | Redacted trace correlation | Trusted host |

Transport authentication is out-of-band. Do not add an `authenticated=true` payload property.

## 5. Authentication, consent and Android permission are separate gates

1. **Transport identity:** derive owner/device/session from an accepted, live, mutually authenticated channel and the trusted enrollment registry. Revalidate expiry, certificate/key generation and revocation at use time.
2. **Owner action consent:** for actions requiring approval, verify a separate one-use capability bound to device, owner, session, exact action, canonical argument digest, nonce and short expiry. A consent token for one action or argument set cannot authorize another.
3. **Android permission/role:** query the operating system immediately before dispatch. The model and request envelope cannot assert that a permission, role, accessibility service or screen-capture grant is enabled.
4. **Policy:** evaluate action risk, context, target and current policy. Unknown actions and unknown fields are denied.
5. **Foreground confirmation:** sensitive or irreversible operations require an owner-visible confirmation in the appropriate Android UI. Transport authentication alone is not consent.

A permission revoked after planning but before dispatch must stop the action.

## 6. Action registry contract

Each action definition must declare:

- stable action ID and schema version;
- strict argument schema, size/depth limits and canonicalization;
- risk tier and whether owner confirmation is mandatory;
- required Android permission/role and the OS query used to verify it;
- foreground/visibility requirement and user-facing explanation;
- maximum execution deadline and cancellation behavior;
- idempotency class and reconciliation method;
- reversibility and whether a second confirmation is required;
- audit fields and redaction policy.

The initial registry may contain read-only `get_battery` and visible `open_app` only after a real authenticated session boundary is implemented. This document does not authorize either action to execute today. Screen access, communications, purchases, transfers, deletion, security changes, and arbitrary intents remain unavailable until separate threat review and consent design.

## 7. Execution state machine

```text
RECEIVED
  -> AUTHENTICATED
  -> VALIDATED
  -> POLICY_ADMITTED
  -> CONSENT_PENDING (only when required)
  -> APPROVED
  -> IDEMPOTENCY_RESERVED
  -> EXECUTING
  -> SUCCEEDED | FAILED | CANCELLED | TIMED_OUT | UNKNOWN_OUTCOME

Any pre-dispatch failure -> REJECTED
```

- Validate the entire plan before dispatch; an invalid later step must not allow earlier partial execution.
- Reserve the idempotency key durably before a side effect.
- Same key + same canonical request returns the recorded outcome; same key + different digest is rejected.
- A crash or transport loss after a side effect but before its result is committed becomes `UNKNOWN_OUTCOME`. Reconcile; never blindly replay.
- Cancellation before dispatch prevents execution. During execution it signals cooperative cancellation. It cannot promise to undo an external side effect already committed.
- Use monotonic deadlines for in-process timeout enforcement. Wall-clock timestamps are for protocol freshness, not elapsed-time measurement.
- A full, unavailable or corrupt replay/audit store fails closed.

## 8. Execution interface constraints

A future Android executor must:

- accept a verifier-created typed session/capability object, not a Boolean or caller-populated identity structure;
- expose only registered typed actions, never arbitrary shell, `ProcessBuilder`, `Runtime.exec`, Python subprocess, reflection-based method dispatch, or model-generated intents;
- recheck OS permissions and owner consent immediately before dispatch;
- run bounded work with cancellation and an explicit emergency stop;
- keep sensitive actions foreground-visible and revocable;
- produce a typed result; the model cannot claim success without a verified result;
- keep the legacy Termux scripts unreachable from the Android app.

The Kotlin `CommandRouter` Boolean parameter is a known prototype limitation. It must be replaced or made unreachable from any production-facing call path before transport integration. A future type is only meaningful if its construction is confined to the verifier boundary; a public factory that accepts caller-provided identity is not an improvement.

## 9. Privacy-preserving audit event

Record, at minimum: request/correlation IDs, action ID and version, authenticated owner/device reference, policy version, consent-capability reference, permission decision, state transition, monotonic elapsed time, result code and an argument digest.

Do not record raw credentials, PINs, private keys, full screen contents, message bodies, contact details or unrestricted command strings. Diagnostic artifacts must redact identifiers and sensitive payloads. Audit write failure before a side effect is a denial; audit failure after a side effect must produce an explicit uncertain/failure state and reconciliation path.

## 10. Required adversarial acceptance matrix

| ID | Scenario | Required outcome |
| --- | --- | --- |
| M3-01 | Caller supplies `authenticated=true` without a verified session | Reject |
| M3-02 | Session certificate/key is revoked or generation changed | Reject |
| M3-03 | Device, owner or session differs from enrolled context | Reject |
| M3-04 | Consent action or argument digest differs | Reject |
| M3-05 | Expired, future-dated or replayed request/capability | Reject |
| M3-06 | Same idempotency key and same request | Return original outcome; no second side effect |
| M3-07 | Same idempotency key with different arguments | Reject |
| M3-08 | Android permission/role is revoked between plan and dispatch | Reject before dispatch |
| M3-09 | Cancellation races with reservation/commit | Exactly one defined terminal/uncertain outcome |
| M3-10 | Timeout or process death after side effect | `UNKNOWN_OUTCOME`; reconcile, never blind replay |
| M3-11 | Replay ledger or audit store unavailable/full/corrupt | Fail closed |
| M3-12 | Unknown action, extra argument, oversized/deep JSON | Reject |
| M3-13 | Legacy Termux shell script or arbitrary process launch requested | Not present in Android action registry; reject |
| M3-14 | Model claims success without executor result | Report unverified; never mark succeeded |

## 11. Milestone gates and non-goals

M3 remains **PARTIAL** until a fake/no-op executor demonstrates the full verified-session → policy → owner-consent → permission-check → idempotency → cancellation → audit lifecycle under adversarial tests. The first integration must be a deterministic local test adapter, not a physical device action.

M4 remains separate: actual Android permissions and device APIs require their own consent, runtime and hardware gates. M5/M7 require a supervised physical Pixel 9 Pro session. M6 requires independent security review. M8 requires signed reproducible artifacts, provenance, OTA/recovery and release approval.

This design does **not** create a listener, network endpoint, production CA, key provisioning, Android permission grant, accessibility service, screen capture, call/message function, shell bridge, device executor, firmware image, OTA package or signed release. No milestone is completed by this document.


## Implementation update — 2026-11-07: Boolean-only Android dispatch removed

The Android command path has been made explicitly fail-closed:

- `AgentPolicy` is now a risk classifier only. It accepts an action name and returns `LOW_RISK`, `OWNER_APPROVAL_REQUIRED`, or `DENY`; it has no caller-supplied authentication or contact-approval Boolean.
- `CommandRouter` accepts only `UntrustedCommandRequest`. It rejects every request with `VERIFIED_TRANSPORT_SESSION_REQUIRED` (and rejects malformed action names before that check). The previous `authenticatedByTransport: Boolean` parameter and direct `get_battery` / `open_app` dispatch code are removed.
- A source gate scans all Android main Kotlin sources and fails if a call site is added before the typed verifier boundary exists. JVM tests prove that even low-risk actions are refused by the router.

This is an intentional disabled state, not an executor or a completed M3 integration. The user-facing launcher still exposes ordinary owner-initiated app opening separately. The Python `core/command_admission.py` Boolean remains an offline, no-execution prototype and must not be wired into a production call path.

M3 remains **PARTIAL**. The next implementation must introduce a verifier-originated, non-caller-constructible capability bound to owner, device, live session, exact action and canonical argument digest; then add Android permission revalidation, idempotency, cancellation, redacted audit and a fake/no-op executor. No listener, permission grant, shell bridge or device action is enabled by this update.


## Implementation update — 2026-11-07: opaque capability and no-op simulation

The mTLS adapter now has a deliberately narrow capability path:

- verify_and_issue_capability first verifies and consumes the owner-signed challenge through the exact live server-side TLS socket and trusted enrollment registry.
- Protocol v1 is accepted only for read_screen with an exactly empty argument object. The capability stores a domain-separated SHA-256 digest of that fixed action/argument schema. Non-empty arguments and navigate/scroll are refused until a new signed protocol version can bind and visibly preview their arguments.
- The returned VerifiedOwnerActionCapability is an opaque object handle. The issuing adapter retains the exact object identity and its owner/device/session, transport certificate, credential generation, consent-key digest, nonce, action, argument digest and monotonic expiry in peer-local state. Constructing another handle does not create authority.
- consume_action_capability rechecks the exact live socket, certificate enrollment, session, consent enrollment, key digest and monotonic expiry. It removes the handle before returning successful one-use admission. Transport or owner-key revocation invalidates it.
- core/noop_action_executor.py consumes this handle and returns SIMULATED_ONLY; device_actions_executed is always false. It has no Android, shell, process, network or device API.
- Synthetic mTLS tests cover successful one-use consumption, caller-constructed handles, action/argument mismatch, socket transfer, transport revocation, consent-key rotation, enrollment revocation, expiry and registry outage/retry.

This is a trusted-process capability pattern, not isolation against arbitrary malicious code already executing inside the same Python interpreter. It is not connected to an Android executor, and it does not query Android permissions. The existing Android router remains fail-closed. core/command_admission.py and the offline plan simulator remain prototypes and are not promoted to production paths.

M3 remains PARTIAL. The next step is a versioned consent protocol that signs a canonical digest of non-empty action arguments and presents those exact arguments in owner-visible Android UI before signing. Only after that should the verifier-created capability be mirrored in the JVM layer and Android permission state be revalidated. No listener, shell bridge, screen capture, permission grant or device action is enabled by this update.

### Independent review correction — verified key provenance and transport remapping

A second review found two capability-binding gaps and closed them before acceptance:

1. The verifier result now carries the SHA-256 digest of the exact enrolled consent public key whose signature was verified and whose nonce was atomically consumed. Capability minting compares that digest with the current enrollment record and refuses a key change between verification and minting.
2. Capability consumption now compares the current transport registry owner and device mapping, as well as the certificate fingerprint and credential generation, with the values captured at issuance. The retained challenge owner/device identity is also checked.

New adversarial tests cover a consent-key rotation immediately after nonce consumption, transport owner/device remapping, and transport credential-generation changes. A failure consumes no device action; the key-rotation race consumes the consent nonce but deliberately returns no capability, requiring a fresh challenge.

This closes the identified in-process admission gaps for the no-op harness only. It does not make registry lookup and a future real side effect atomic. Any real executor still requires a durable authorization/idempotency reservation transaction that binds the current enrollment generation at the final side-effect boundary.



## Protocol v2 — exact action-argument binding

AGENT-004G adds a version-2 signed arguments_sha256 field. Python host issuance and verification use strict, closed action schemas; Kotlin recomputes the same domain-separated digest from typed arguments; and the Android per-use signer places the exact canonical JSON in the owner-visible system authentication prompt. Shared v1/v2 fixtures preserve cross-platform byte equality.

The live mTLS adapter can mint opaque one-use capabilities for v1 and v2. V1 remains limited to read_screen with empty arguments. V2 recomputes and binds the strict canonical argument digest before issuance and consumption. The only consumer remains the no-op simulator; no device action, permission grant, screen capture, listener or production caller is connected. See AGENT-004G-ARGUMENT-BOUND-CONSENT-V2.md.


## Implementation update — AGENT-004H durable final-action reservation

AGENT-004H adds a dedicated SQLite action-reservation state machine. It binds owner/device/session, capability nonce and protocol, action and canonical argument digest, signed validity window, transport certificate, credential generation and consent-key digest. The deterministic idempotency key is domain-separated; same-binding retries are read-only replays, and changed bindings on the same owner/device nonce conflict. BEGIN IMMEDIATE serializes reservation and state transitions. Capacity and storage failures deny; records are not automatically evicted.

The state machine supports RESERVED, DISPATCH_STARTED, COMPLETED, FAILED_NO_EFFECT, CANCELLED and UNKNOWN_OUTCOME. A dispatch claim is one-use. DISPATCH_STARTED is sticky across restart and cannot be reclaimed; uncertain outcomes are never blindly retried. Only redacted outcome codes/digests are stored. This is distinct from the older DurableReplayLedger, which stores a generic command replay marker.

The new module is storage only. Its public request dataclass is not authentication. It is not yet called by the live mTLS adapter, does not query Android permissions and does not execute an action. A future trusted adapter must construct requests from retained verifier-created capability records, then a Kotlin/Android PermissionGate must re-query the current OS permission/role/service immediately before each platform call. No permission grant, listener, shell bridge, Android executor or device action is connected. Independent human security review remains pending.
