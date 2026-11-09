# SEC-023B1A — Dormant native MemoryVault component

**Scope:** isolated scoped branch off the authorized `feat/phase1-agentic-phone` base `f42af837`; **status: proposed, not accepted**. This does not incorporate unmerged SEC-023/023A/023B0 PRs (#13–#15).

## Delivered

- A native Android `Service` component named `.MemoryVaultService`, declared `android:exported="false"` **and** `android:enabled="false"` with no intent filters, special process, permission, foreground service type or direct-boot access.
- `onBind()` returns `null`; defensive `onStartCommand()` stops the service and returns `START_NOT_STICKY` if a future manifest regression makes it startable.
- Source-manifest security gate rejects accidental enabling, intent filters, process/permission/foreground-service attributes or direct-boot exposure. Offline negative mutation tests cover the boundary.

## Explicit limitations and mandatory gates

**This is a disabled component reservation, not an operational vault.** No IPC, Binder API, Android Keystore, owner prompt, encryption, persistence, agent bridge or memory import/export/delete is implemented. No owner-authentication Boolean is trusted. PaperClip remains RAM-only. This work does not verify the Gradle-merged manifest or runtime Android behavior; hosted Gradle build and future instrumentation are required.

Before enabling this component: independent security review of SEC-023A/B0 schema and trust provenance; implement per-use Keystore CryptoObject proof bound to owner consent, authenticated encryption and nonce/rollback durability; implement negative same-UID/cross-UID Binder tests; verify revocation, key invalidation and process death; obtain real Pixel 9 Pro and spoken TalkBack acceptance. No main merge or production release is authorized.

The repository's `PROJECT-ADAPTER.md` is project-specific. The shared upstream `SKILL.md` is absent and remains unverified. No M1–M8 milestone is independently complete.

## Local verification record (2026-11-09)

- Targeted source/manifest tests: 30 passed after updating the pre-existing accessibility disclosure contract to recognize only this explicitly disabled, private Service.
- Full Python suite: first run failed **one existing SQLite crash-marker race** (`test_process_death_before_signed_revocation_commit_rolls_back_atomically` observed an empty marker); the dedicated fix remains separately proposed in draft PR #11 and is not copied here. Targeted rerun passed; subsequent complete run **946/946 passed**. Do not represent the initial failure as a vault regression or hide it.
- Python compileall, launcher accessibility/recovery source gate, source AndroidManifest security gate and Git whitespace validation passed.
- Gradle/JUnit and merged-manifest checks require exact-head hosted CI; no Android emulator or physical device was used locally. Independent reviewer approval remains pending.

## SEC-023B1A-QA — installed-manifest boundary follow-up (2026-11-09)

Two **instrumentation tests** inspect the installed/merged manifest through Android PackageManager: the service must remain disabled, non-exported, direct-boot-inaccessible, permission-free, same-process, and without a runtime component-state override; an implicit vault probe must not resolve. The explicit instrumentation runner class inventory is updated from five to six classes, and the Phase 1 hosted Android job now compiles the instrumentation APK (`:app:assembleDebugAndroidTest`). The existing QA-005 emulator workflow is scoped to PRs against `main`, so this scoped feature-branch PR does **not** establish that these new tests have run on an emulator. Instrumentation execution and Pixel 9 Pro hardware verification remain pending. No production service behavior, permissions, memory persistence, signing or trust state changed.


## QA-023B1A-C — JUnit aggregate-counter integrity (2026-11-09)

The XML evidence gate now rejects contradictory or malformed JUnit aggregate
`tests`, `failures`, `errors` and `skipped` attributes, and suite-level
failure/error/skip nodes outside individual testcases. This closes an evidence
integrity gap in which a report could declare an aggregate failure without a
child failure element and still satisfy the two required method names.

This change is confined to offline CI evidence parsing and synthetic regression
tests. It does not modify Android app behavior, unlock the disabled vault, or
constitute an independent security approval. Exact-head hosted Android/emulator
results must be rechecked for the new commit.
