# SEC-020B4 — lifecycle-safe trust-store I/O

**Scope:** move Android Keystore and AtomicFile inspection/commit work off the Activity main thread while preserving the existing owner-consent and credential boundary.

## Implementation

- OwnerAuthorityIoCoordinator provides one process-wide single-thread executor. All AndroidOwnerAuthorityTrustStore inspect() and commit() calls from the owner trust Activity are submitted through it, so Keystore/AtomicFile work is serialized and the UI thread does not wait for disk or hardware-backed cryptographic operations.
- OwnerAuthorityOperationGate issues one active operation token, rejects concurrent operations, and invalidates queued work on explicit cancellation or Activity destruction.
- Store inspection and final commit revalidation use immutable parsed input captured on the main thread. UI state is updated only through a main-thread Handler.
- The 30-second one-shot confirmation is still consumed on the credential callback. The background task reinspects the store, recomputes the mode/snapshot binding, rebuilds the Ready proposal, and rechecks device safety before claiming the commit boundary.
- Cancellation or Activity destruction before claimCommit() suppresses the queued commit. After the boundary is claimed, the already-authorized atomic transaction is allowed to finish; the UI callback is suppressed if the Activity is destroyed. A started AtomicFile/Keystore transaction is not falsely described as cancelable or rolled back.
- Explicit cancel/clear refuses to claim success if the transaction has already crossed the commit boundary. The executor remains disconnected.

## Tests and acceptance

- OwnerAuthorityOperationGateTest covers single-operation admission, cancellation-before-commit, destruction-before-commit, non-cancelability after commit claim, callback suppression after destruction, and concurrent begin attempts.
- Python source gates require a single-thread executor, off-main store calls, cancellation invalidation, commit-claim ordering, and the application-context device-safety recheck.
- Exact-head Phase 1 push/PR, CI-003 push/PR, and QA-005 emulator PR workflows must pass before accepting this change.
- The tests do not exercise Android Keystore, StrongBox, physical crash recovery, or Pixel 9 Pro behavior. Independent security review remains required.

## Transaction boundary clarification

The commit claim is the point after fresh credential success, one-shot confirmation consumption, trust-store snapshot revalidation, proposal reconstruction and a final device-safety check. Before that point, cancellation/destruction invalidates the operation and the worker must not commit. Once claimed, the storage transaction has started and is allowed to complete atomically; an Activity destruction after that point suppresses UI delivery but cannot safely promise rollback of an already-started AtomicFile/Keystore operation.


## SEC-020B4A — serialized-worker and commit-race regression tests

The follow-up test slice adds a direct JVM test of the process-wide coordinator. It holds the first submitted task behind a latch, queues a second task, proves the second task cannot overlap or complete early, then releases the worker and verifies both tasks used the dedicated `mrnothing-owner-authority-io` thread.

The operation-gate suite now also races `cancel(token)` against `claimCommit(token)` from two synchronized workers. Exactly one operation must win the synchronized boundary. A stale completion/cancellation token is also tested against a newer active operation so late callbacks cannot cancel or finish the newer transaction.

These tests exercise the JVM executor and pure synchronization gate only. They do not invoke Android Keystore, StrongBox, AtomicFile, Activity lifecycle callbacks or a physical device. Exact-head Phase 1 and CI-003 workflows are the acceptance gate; QA-005 remains a separate launcher/credential-probe emulator suite.


## SEC-020B4B — static capability-boundary regression gates

The source-level security boundary is now checked across the owner trust Activity, import parser, Android trust backend, trust store and serialized I/O coordinator. The regression gate rejects direct references to agent/command routing, permission grants, foreground execution, screen capture/accessibility, notification listeners, VPN/device administration, telephony, camera/microphone, arbitrary process launch and network clients/listeners.

A second regression gate parses both manifests. It requires the credential probe Activity and cancellation receiver to exist only in the debug manifest, with both components explicitly exported only behind `android.permission.DUMP`; neither probe may appear in the main/release source manifest.

These are static source/manifest checks. They do not prove absence of reflective or transitive runtime capabilities, do not inspect a Gradle-merged release manifest, and do not exercise the Android trust-store worker on-device. Existing Phase 1 manifest/build gates and exact-head QA-005 remain required. Independent security review and Pixel 9 Pro validation remain separate acceptance gates.


## SEC-020B4C — Android Activity lifecycle instrumentation

The QA-005 API 35 emulator workflow now runs `:app:connectedDebugAndroidTest` before the launcher smoke scripts. The platform `android.test.InstrumentationTestRunner` is used without adding an external Maven dependency. The API-35 SDK's `android.test.base.jar` and `android.test.runner.jar` are compile-only dependencies of the instrumentation source set; they are supplied by the emulator at runtime and are not packaged into the application or test APK.

`OwnerAuthorityTrustActivityLifecycleTest` occupies the process-wide trust I/O worker with a bounded latch, launches the real non-exported owner trust Activity, and observes the active token created by its initial trust-state refresh. It then finishes the Activity on the main thread and verifies that the actual `onDestroy()` path invalidates the queued token and makes it non-deliverable. The worker is released and a FIFO sentinel proves the queued task drains; because the task's first operation is the active-token check, it must return before constructing or inspecting the Android trust store.

The test enters no credentials, imports no authority material, commits no trust transition and adds no permission or exported component. Reflection is limited to reading the Activity's private operation gate and the gate's active token; it does not mutate either. The existing JVM tests continue to cover the synchronized cancel/commit-claim race and the post-claim destruction semantics.

**Acceptance boundary:** this proves the real Activity destruction hook invalidates queued trust I/O on the disposable API 35 x86_64 emulator. It does not exercise an in-flight StrongBox/AtomicFile transaction, actual credential cancellation, physical Pixel 9 Pro hardware, crash recovery or spoken TalkBack. Those remain separate gates.


### SEC-020B4C compile-classpath correction

The first exact-head QA-005 run reached `:app:compileDebugAndroidTestKotlin` and failed because the optional `android.test` APIs are not part of the default API-35 compile classpath. No instrumentation test executed on that attempt. The correction adds the SDK's `android.test.base.jar` and `android.test.runner.jar` as `androidTestCompileOnly` files, checks that both are present, and leaves them out of packaged artifacts. No external dependency or release manifest/library entry is introduced. Two Python workflow regression tests now require the instrumentation step to run after emulator boot and before launcher smoke, and require the platform test jars to remain compile-only.


### SEC-020B4C lifecycle-observation correction

The first corrected compile/run attempt successfully compiled the instrumentation source and launched the API-35 emulator test, but the assertion checked `Activity.isDestroyed` immediately after `finish()`. Android completes the destruction transition asynchronously, so that assertion raced the framework lifecycle. The test now registers an `Application.ActivityLifecycleCallbacks` observer before finishing the Activity and waits on a bounded latch for the actual `onActivityDestroyed` callback before asserting the destroyed state and invalidated operation token. The callback is always unregistered. No timeout was relaxed, no application lifecycle behavior was changed, and the worker release/FIFO drain remain in `finally`.


## SEC-020B4D — in-flight transaction lifecycle instrumentation

The Activity now depends on a narrow `OwnerAuthorityTrustStorePort`. Its default internal factory still constructs only `AndroidOwnerAuthorityTrustStore`; the only override is a debug-source-set test host registered in the debug manifest as a non-exported Activity. The fake backend slot and test host do not exist in the release source set or release manifest.

Two API-35 emulator instrumentation cases exercise the real Activity's credential-confirmation callback and commit worker with a synthetic Ed25519 authority and an in-memory fake store:

1. **Destroyed before commit claim:** the fake backend blocks the third inspection (the final revalidation after the credential callback). The test finishes the Activity, observes its actual `onActivityDestroyed` callback, releases inspection and verifies the operation gate prevents `commit()`; fake trust state remains empty.
2. **Destroyed after commit claim:** the fake backend blocks inside `commit()`, which proves the synchronized commit claim has already succeeded. The test destroys the Activity, verifies the claim remains non-cancelable and UI delivery is disabled, releases the fake atomic commit, and verifies exactly one in-memory commit completes while the destroyed Activity's status view is unchanged.

Each test sets and clears a fixed synthetic PIN on the disposable emulator to exercise the actual Android DEVICE_CREDENTIAL prompt. No real user credential, authority, Android Keystore alias, StrongBox key, AtomicFile, permission grant, enrollment, executor or physical device is used. The fake backend is process-memory-only.

**Acceptance boundary:** this validates Activity/gate ordering around a fake backend on API 35. It does not prove StrongBox/AtomicFile hardware atomicity, crash recovery, physical Pixel 9 Pro behavior, or independent security approval. Exact-head Phase 1, CI-003 and QA-005 evidence is required.
