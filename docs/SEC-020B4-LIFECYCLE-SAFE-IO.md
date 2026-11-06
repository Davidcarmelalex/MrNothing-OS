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

The QA-005 workflow sets a fixed synthetic PIN through ordinary ADB shell immediately before the instrumentation task and clears it in an EXIT/INT/TERM cleanup trap. Both test cases reuse that disposable credential to exercise the actual Android DEVICE_CREDENTIAL prompt. No real user credential, authority, Android Keystore alias, StrongBox key, AtomicFile, permission grant, enrollment, executor or physical device is used. The fake backend is process-memory-only.

**Acceptance boundary:** this validates Activity/gate ordering around a fake backend on API 35. It does not prove StrongBox/AtomicFile hardware atomicity, crash recovery, physical Pixel 9 Pro behavior, or independent security approval. Exact-head Phase 1, CI-003 and QA-005 evidence is required.


## SEC-020B4D exact-head QA failure analysis and diagnostic correction — 2026-11-06

At branch head 2299b723621f654bb3782f8fa0371a13f8b37122, Phase 1 push [42168597642](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168597642) and PR [42168602224](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168602224) passed; each Python suite ran 506 tests, and Android debug unit/build/dependency checks passed. CI-003 push [42168597742](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168597742) and PR [42168602103](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168602103) passed independent builders and cross-runner verification. QA-005 [42168602258](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42168602258) booted the disposable API 35 emulator, compiled instrumentation, and began the after-commit-claim test; that test failed, and later QA steps were skipped. The uploaded diagnostics did not include the AndroidJUnitRunner XML/HTML result bundle, and the 300-line logcat tail did not expose the assertion cause. SEC-020B4D remains unaccepted.

The next correction broadens credential UI detection to inspect accessible Android windows and recognize the known auth_credential_input and lockPassword fields only when hosted by com.android.systemui or com.android.settings. The test now waits for the Activity's explicit final-revalidation status after submitting the synthetic emulator PIN, then reports the Activity status and both boundary latch states if the fake backend is not reached. This narrows the failure signal between system credential UI detection, credential callback acceptance and the trust I/O boundary; it does not relax credential-only authentication or the device safety gate.

The QA-005 always-run evidence step now preserves Android connected-test XML/HTML reports from both Gradle report/output locations and captures a larger 2,000-line all-buffer logcat tail. These diagnostics are needed to distinguish a test assertion from an instrumentation-process crash. No production credential, trust mutation, Android permission, agent execution, privileged shell, physical device or production release is involved. Exact-head Phase 1, CI-003 and QA-005 reruns remain required; upstream shared SKILL.md remains unverified and is not claimed as installed.


### SEC-020B4D — Android 15 Keyguard PIN selector correction (2026-11-06)

Exact-head evidence at `23993daed4e213b95cda115ca8700b4b92211174`:
- Phase 1 push [42174955256](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42174955256) and PR [42174961713](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42174961713) passed; both Python-policy jobs reported 507 tests passed, and both Android unit/build/dependency paths passed.
- CI-003 push [42174955299](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42174955299) and PR [42174961699](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42174961699) passed.
- QA-005 PR [42174961897](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42174961897) failed in both SEC-020B4D instrumentation cases before the trust commit boundary. The exact assertion reported `secure=true, deviceLocked=true, keyguardLocked=true, userUnlocked=true, interactive=true, deviceCredentialCanAuthenticate=0, visibleSystemCredentialInput=false`. The disposable emulator PIN had been configured and the device was awake, but the preflight could not recognize the visible lockscreen PIN control. Later QA steps were skipped.

Root cause was confirmed against the Android 15 AOSP SystemUI source, not inferred from the assertion alone: `packages/SystemUI/res-keyguard/layout/keyguard_pin_view.xml` declares `@+id/pinEntry` as `com.android.keyguard.PasswordTextView`, while `keyguard_password_view.xml` declares `@+id/passwordEntry` as an `android.widget.EditText`. The previous detector accepted only `auth_credential_input` and `lockPassword`, and required every candidate to be an EditText. It therefore rejected the real Android 15 PIN field.

Correction: the debug-only instrumentation detector now recognizes four explicit SystemUI ID/class pairs: `auth_credential_input/EditText`, `lockPassword/EditText`, `pinEntry/PasswordTextView`, and `passwordEntry/EditText`. It still requires the root window package to be `com.android.systemui` or `com.android.settings`, the node to be visible, and the exact expected class to match. No generic EditText fallback, app-owned input, Keyguard dismissal API, credential bypass or production code change is introduced. The disposable synthetic PIN is entered only after one of these known system-owned credential fields is observed.

A Python source regression test now pins the Android 15 PIN/password ID-to-class mapping and package boundary. AOSP references: [Android 15 Keyguard PIN layout](https://github.com/aosp-mirror/platform_frameworks_base/blob/android15-release/packages/SystemUI/res-keyguard/layout/keyguard_pin_view.xml) and [password layout](https://github.com/aosp-mirror/platform_frameworks_base/blob/android15-release/packages/SystemUI/res-keyguard/layout/keyguard_password_view.xml).

This is a test-harness correction only. SEC-020B4D remains NOT ACCEPTED until the new exact-head QA-005 run passes both commit-boundary cases and the full remaining QA sequence. No real trust-store mutation, production credential, StrongBox, AtomicFile, physical Pixel 9 Pro, permission grant, agent execution, signed release or deployment is claimed. Independent human security review remains pending.


## SEC-020B4D — exact-head QA-005 failure and lockscreen gesture correction (2026-11-06)

At head `e8d255c24db2670adec78d5dc3d505acedc9c29c`, Phase 1 push [42181487968](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181487968) and PR [42181494281](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181494281) passed; each Python policy job ran 508 tests, and both Android jobs passed. CI-003 push [42181488047](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181488047) and PR [42181494488](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181494488) passed both independent builders and the independent verifier.

QA-005 PR [42181494325](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181494325) booted API 35, built both APKs, passed the dependency-verification negative control and started all three Android instrumentation tests. The queued-inspection lifecycle test passed. Both SEC-020B4D commit-boundary tests failed before the Activity prompt or fake-store boundary in `prepareInteractiveUnlockedEmulator()`: `secure=true`, `deviceLocked=true`, `keyguardLocked=true`, `userUnlocked=true`, `interactive=true`, `deviceCredentialCanAuthenticate=0`, but no visible SystemUI credential field was exposed. The XML report confirms both failures occurred at the lockscreen preflight; no commit-boundary assertion ran. The workflow cleanup logged `Lock credential cleared`. Artifact: [13485568001](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42181494325/artifacts/13485568001).

The Android 15 SystemUI selector correction in the preceding commit was present, but the preflight only sent `KEYCODE_WAKEUP` and immediately searched for the PIN field. The failure is consistent with the lockscreen still showing its ambient/clock surface and requiring a normal swipe-up to reveal the PIN pad; this is a bounded test-harness hypothesis, not a confirmed production defect.

The next correction injects a display-metrics-relative swipe-up using `UiAutomation.injectInputEvent`, only when Keyguard reports locked and the exact SystemUI credential field is not already visible. The test then requires the known SystemUI package, resource ID, visibility and exact Android view class before typing the synthetic PIN. A failed/incomplete gesture sends ACTION_CANCEL in `finally`. This is an ordinary lockscreen reveal gesture, not Keyguard dismissal or authentication. No `requestDismissKeyguard`, shell dismissal, root, app-owned input, production behavior, permission or trust-store path is introduced.

SEC-020B4D remains NOT ACCEPTED until both commit-boundary instrumentation cases and the complete QA-005 sequence pass at the new exact head. The synthetic PIN must be cleared. Independent human security review and physical Pixel 9 Pro validation remain separate gates.


## SEC-020B4D — UIAutomation swipe did not reveal Android 15 PIN pad; unprivileged input correction (2026-11-06)

At head `34b34e1da3158c5c0497142de92391295f8b31a7`, Phase 1 push [42183555613](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183555613) and PR [42183562415](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183562415) passed; each Python policy job ran 509 tests, and both Android jobs passed. CI-003 push [42183555609](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183555609) and PR [42183562507](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183562507) passed both independent builders and independent verification. The unsigned release APKs were byte-identical across runners: 7,829,060 bytes, 21 ZIP entries, SHA-256 `3c09c4b4c7956cb7e2a90fdc96c9ab909f53f4526c8439ed25b0aae78c49f1ea`; normalized-entry SHA-256 `9e6c4b9489af0f8b07f1d5fdae1d2ac6746041686d84fded9c0cecd4ddbc97d1`. The scoped build-environment inventory contains 1,260 components; provenance still reports `release_ready=false`.

QA-005 PR [42183562453](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183562453) booted the API 35 emulator, compiled the instrumentation tests and ran all three cases. The queued-activity destruction test passed. Both commit-boundary tests again failed in `prepareInteractiveUnlockedEmulator()` before the credential prompt or fake-store boundary. The previous display-relative `UiAutomation.injectInputEvent` swipe returned accepted, but the exact SystemUI PIN field remained unavailable; the safety snapshot remained secure=true, deviceLocked=true, keyguardLocked=true, interactive=true and deviceCredentialCanAuthenticate=0. JUnit artifact [13486851509](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42183562453/artifacts/13486851509) confirms the failures at the preflight line. The workflow cleanup logged `Lock credential cleared`. Later launcher/accessibility steps were skipped.

The next bounded correction replaces injected MotionEvent objects with Android's `input swipe` utility, executed only after verifying the instrumentation shell identity is exactly `uid=2000(shell)`. The gesture uses display-metrics-derived coordinates and is issued only when Keyguard reports locked and no exact SystemUI credential field is already visible. The test still waits for the exact visible SystemUI package/resource-ID/class pair before entering the synthetic PIN. This is an ordinary touch gesture from the unprivileged shell; no root, Keyguard dismissal API, credential bypass, app-owned input or production behavior is introduced.

SEC-020B4D remains NOT ACCEPTED until both commit-boundary tests and the full QA-005 sequence pass at a new exact head. Synthetic PIN cleanup, independent human security review and physical Pixel 9 Pro validation remain separate acceptance gates.


## SEC-020B4D — credential surface still absent after unprivileged swipe; bounded UI diagnostics added (2026-11-06)

At head `e5a313ac6c942b982739294e097daa90c6eadcf4`, Phase 1 push [42184476741](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184476741) and PR [42184482244](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482244) passed; each Python policy job ran 509 tests and both Android jobs passed. CI-003 push [42184476880](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184476880) and PR [42184482249](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482249) passed both independent builders and verifiers.

QA-005 [42184482208](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482208) booted the API 35 emulator, compiled instrumentation and ran three tests. The queued-activity destruction test passed; both SEC-020B4D commit-boundary tests failed before credential prompt display. The Android `input swipe` command returned without a reported shell error, but no exact visible SystemUI PIN field appeared. The workflow cleanup logged `Lock credential cleared`; subsequent QA steps were skipped. Artifact [13487605359](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42184482208/artifacts/13487605359) contains JUnit and logcat evidence.

The repeated failure shows that neither accepted UiAutomation MotionEvent injection nor the unprivileged `input swipe` utility has yet demonstrated that the credential entry surface is being revealed. The actual window hierarchy/focus was not captured in either artifact, so the reason remains unconfirmed. This is not evidence of a production trust Activity or trust-store defect.

This commit adds a bounded read-only diagnostic snapshot on failure: up to 80 accessibility nodes, at most 9 KB, root/window package/class/view identifiers, plus a filtered `dumpsys window windows` focus summary. Every acquired AccessibilityNodeInfo is recycled. The swipe diagnostics also record shell identity, display dimensions, coordinates, and command output. No gesture behavior or production path is changed. The next exact-head QA run should identify whether the lockscreen root is exposed, whether the gesture changed focus, and which SystemUI nodes actually exist.

SEC-020B4D remains NOT ACCEPTED. Do not add further gesture or credential automation changes until this evidence identifies the failing layer. The synthetic PIN cleanup, independent human security review and physical Pixel 9 Pro validation remain separate gates.
