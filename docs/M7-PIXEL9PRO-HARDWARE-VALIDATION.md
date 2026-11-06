# M7 — Pixel 9 Pro supervised hardware validation protocol

**Status:** PREPARED — NOT EXECUTED. No physical device was accessed during preparation.
**Exact target:** Google Pixel 9 Pro, codename `caiman`. A Pixel 9 Pro XL, carrier-specific variant or other Pixel model is not an interchangeable substitute.
**Scope:** M7 physical compatibility and recovery evidence for the Android application/launcher and isolated hardware-backed trust tests. This protocol does not authorize bootloader unlocking, rooting, firmware flashing, custom AOSP installation, factory reset or production deployment.

## 1. Entry criteria and operator consent

Do not start until all of the following are true:

- The device owner is present and gives explicit, informed approval for each disruptive stage (installation, HOME-role selection, app-process termination, reboot, credential prompt, connectivity tests and any data-affecting action). Consent to one stage does not authorize the next.
- The device is positively identified as **Pixel 9 Pro / `caiman`**, not XL or another model. Record only the model, codename, Android release/API and a privacy-reviewed build-fingerprint representation; never publish the serial number, IMEI, phone number, SIM identifiers, account names, Wi-Fi SSID/BSSID or personal notifications.
- The owner has a current backup and confirms that the device contains no irreplaceable test data. Prefer a dedicated test device with no production owner-authority state.
- Battery is at least 60%, the device is not hot, the USB connection is stable and the operator has a safe stop/recovery path.
- The stock bootloader remains locked and Android Verified Boot reports a green/verified state. Any unexpected unlocked, orange, yellow, red or unknown state is a STOP condition; do not attempt to repair it by unlocking, flashing or wiping.
- The exact test APK is reviewed and its SHA-256, package/application ID, version and signer certificate are recorded. Use a debug/test-signed artifact explicitly labelled **NOT FOR RELEASE**. CI-003 unsigned release APKs are not installable release candidates and must not be represented as signed production builds.
- A second reviewer is assigned to inspect the protocol, evidence handling and stop conditions. If no independent reviewer is available, record `PENDING_INDEPENDENT_REVIEW`; the operator must not self-approve M7.

## 2. Read-only device identity preflight

Use ADB only after the owner approves connecting the device. These commands are diagnostic reads; redact serials and personal identifiers before saving output:

    adb get-state
    adb shell getprop ro.product.manufacturer
    adb shell getprop ro.product.model
    adb shell getprop ro.product.device
    adb shell getprop ro.build.version.release
    adb shell getprop ro.build.version.sdk
    adb shell getprop ro.kernel.qemu
    adb shell getprop ro.boot.flash.locked
    adb shell getprop ro.boot.verifiedbootstate
    adb shell getprop ro.boot.vbmeta.device_state
    adb shell pm list features

Expected identity is Pixel 9 Pro and `caiman`. Expected secure baseline is locked bootloader, verified/green boot and a known stock build. If any property is absent or contradictory, stop and obtain a human device assessment; do not infer safety from one property alone. On AOSP, `ro.kernel.qemu=1` is an emulator marker; physical Android builds may omit the property. The offline validator therefore accepts only an absent/blank marker or exact `0`, and rejects `1` and every other non-empty/unrecognized value. Absence is not proof of physical hardware and never completes M7. This interpretation follows the [AOSP init kernel-property import path](https://chromium.googlesource.com/aosp/platform/system/core/+/7daa66aa07ce0ffa119a2cfde31ec133f03f3ec2/init/init.cpp).

Record whether `android.hardware.strongbox_keystore` is advertised by PackageManager. Feature presence is only a capability preflight, not proof that a generated key is StrongBox-backed.

## 3. Test artifact and installation gate

1. Verify the test APK checksum against the exact-head CI artifact and inspect the signer certificate with Android SDK build tools (`apksigner verify --print-certs`).
2. Confirm the application ID is `tech.mrnothing.os`, the build is the intended debug/test variant and the source commit is recorded in provenance.
3. Do not install the unsigned CI-003 release APK. Do not replace an existing installation with a different signer. If an existing package or owner trust state is present, stop and design a non-destructive test plan rather than uninstalling, clearing app data or overwriting aliases.
4. Install only after a separate explicit owner approval. Do not grant permissions with `pm grant`, hidden APIs or shell shortcuts. Use Android Settings/system prompts for user-visible choices.

## 4. StrongBox identity and key-operation gate

Run a dedicated instrumentation case that creates only UUID-scoped disposable aliases. It must request StrongBox explicitly with `setIsStrongBoxBacked(true)` for each test key and inspect the returned Android `KeyInfo.securityLevel` (API 31+) for the exact value `KeyProperties.SECURITY_LEVEL_STRONGBOX`.

Required checks:

- Verify the StrongBox feature preflight and record the API/device build.
- Generate a disposable HMAC marker key and a disposable AES-GCM record key with StrongBox required. Record algorithm, size, purposes, digest/block mode and security level, but never key bytes or secret material.
- Perform a known-message HMAC sign/verify operation and AES-GCM encrypt/decrypt round trip with associated data; verify that a modified tag or associated-data mismatch is rejected.
- Confirm both keys report `SECURITY_LEVEL_STRONGBOX`. `isInsideSecureHardware` alone is insufficient because it does not distinguish StrongBox from TEE.
- If StrongBox is absent, unavailable, unsupported or returns a non-StrongBox level, record a failed/not-supported gate. **Never retry with TEE, software keys or a different provider.**
- Clean up only the exact UUID-scoped test aliases created by the test, in a `finally` path. Never enumerate and delete production aliases or the live owner-authority namespace.

## 5. Process-death and reboot persistence

Use only the disposable aliases from section 4:

1. Complete and verify HMAC and AES-GCM operations; record a redacted alias token and result.
2. With owner approval, terminate only the test application process (not SystemUI, Keyguard, Keystore or other processes). Relaunch and repeat the key operations.
3. With a separate explicit owner approval, perform one normal Android reboot. Do not simulate power removal, bootloader operations or battery disconnects.
4. The owner unlocks the device manually through the real system credential UI after boot. Do not inject credentials through ADB, automate a hidden PIN field or bypass Keyguard.
5. Relaunch the test harness, reload AndroidKeyStore, verify the same disposable aliases remain present, verify exact StrongBox metadata again, and repeat HMAC/AES-GCM operations.
6. If aliases disappear, become unreadable, change security level or operations fail, record the failure and stop. Do not regenerate under the same alias, reset the device or silently classify the state as a fresh install.

A normal reboot test does not prove kernel-crash, sudden power-loss, storage-corruption, factory-reset or Keystore-daemon recovery. Those are separate experiments requiring a separately reviewed safety plan.

## 6. Marker-first recovery and fail-closed behavior

Use a test-only namespace and isolated persistence fixture. Exercise: missing active record with an existing generation marker; unreadable AES key; missing AES alias; malformed envelope; and interrupted record replacement. Expected outcomes are `RecoveryRequired` or `Unavailable` as defined by the trust-store policy, never `Empty`/fresh installation when a generation marker exists.

Do not corrupt, delete, rotate or overwrite the real owner-authority marker, AES alias, encrypted record, credential generation or enrollment state on the owner's device. A test that requires damaging live trust state is prohibited. Preserve evidence that no fallback key, TEE key or new generation marker was created after an injected failure.

## 7. Credential prompt, HOME role and stock-launcher recovery

- Verify the owner-credential prompt is the genuine Android system prompt and that the app cannot substitute its own PIN/password field.
- Test both explicit cancellation and owner-approved success. Cancellation must leave trust state unchanged and must not create a consent capability.
- Ask the owner to select MrNothing OS as HOME through Android's own role/chooser UI. Verify cancellation leaves the existing launcher selected; explicit acceptance changes the role only after the system UI confirms it.
- Restore the stock launcher through Android Settings/system UI and verify the device remains usable. Do not force a HOME role through shell commands or suppress the system chooser.
- Keep production owner credentials out of screenshots, logs, test fixtures and transcripts.

## 8. Accessibility and TalkBack acceptance

Current CI evidence is limited: QA-011 is a read-only preflight and the latest run reports the TalkBack package present but the service disabled; QA-012 verifies structural semantics only. Neither establishes spoken navigation.

For acceptance, use a device or disposable emulator with the official TalkBack package installed. The owner/operator must enable TalkBack through Android Settings and explicitly approve the system accessibility prompt. Never enable it by writing `enabled_accessibility_services` or `accessibility_enabled` through ADB or another shell override.

With TalkBack active, independently verify spoken labels and roles for the app catalog, consent preview, cancel/confirm controls, errors and recovery actions; predictable focus order; double-tap activation; Back/Home navigation; large text; keyboard focus; stock-launcher recovery; and the ability to revoke/disable the service through Settings. Do not record personal speech or notifications. Capture only redacted test observations and obtain separate verifier signoff.

## 9. Device compatibility matrix

| Area | Test | Acceptance evidence |
| --- | --- | --- |
| Model/boot | Exact `caiman`, locked bootloader, verified boot | Redacted property snapshot |
| StrongBox | Feature, generated-key `securityLevel`, HMAC/AES-GCM | Instrumentation report and key metadata without secrets |
| Persistence | Process death and owner-approved reboot | Before/after operation results and build identity |
| SIM/VoLTE | Owner-approved ordinary test call on a test number | Manual two-way audio result; no call recording |
| Wi-Fi | Connect/disconnect and ordinary network reachability | Redacted pass/fail; no SSID/BSSID |
| Bluetooth | Pair/connect/disconnect a test accessory | Redacted device category and pass/fail |
| Microphone/speaker | Local test tone/voice loop approved by owner | Manual result; no recording unless separately consented |
| Battery/thermal | Capture baseline, run bounded 15-minute app workload, compare afterward | Battery delta and thermal status; stop on overheating or severe thermal warning |
| Accessibility | TalkBack spoken navigation, large text, keyboard and recovery | Operator checklist and independent observation |
| Launcher recovery | Accept/cancel HOME role and restore stock launcher | System UI evidence and final HOME-role state |

Ordinary SIM voice/VoLTE acceptance is not AI-call integration. Two-way AI audio remains a separate dependent gate requiring M3/M4 authenticated, consented execution and its own privacy/safety review. Do not claim it from a normal phone call.

App/launcher recovery is an M7 check. Signed OTA installation, rollback partitions, verified-boot image signing and firmware recovery remain M8 release gates and are not authorized by this protocol.

## 10. Evidence record template

Create one evidence bundle per supervised run with:

- Run ID, date/time, operator and independent reviewer.
- Explicit consent record for each disruptive stage (store the approval outcome, not a credential or unnecessary personal details).
- Model/codename, Android release/API, redacted build fingerprint, locked/verified boot result and battery/thermal baseline.
- Test APK SHA-256, package ID, version, signer certificate fingerprint and source commit.
- StrongBox feature result; HMAC/AES key algorithms/purposes/security levels; operation results; redacted disposable alias tokens.
- Process-death and reboot before/after results, manual first-unlock confirmation and any recovery classification.
- Credential prompt cancellation/success, HOME-role cancellation/acceptance, stock-launcher restoration and accessibility/TalkBack checklist.
- SIM/VoLTE, Wi-Fi, Bluetooth, audio, battery and thermal observations with personal identifiers removed.
- Test-alias cleanup result, stop conditions encountered, deviations, unresolved defects and reviewer decision.

Never include serial/IMEI, phone number, SIM identifiers, private keys, raw credentials, personal notifications, SSIDs/BSSIDs, call content or unredacted screen recordings in a public artifact.

## 11. Stop conditions and pass/fail rules

Stop immediately on wrong model, unknown firmware, unlocked/unverified boot, artifact/signature mismatch, unexpected production trust state, missing owner consent, StrongBox fallback, key/alias mutation outside the disposable namespace, credential prompt ambiguity, unexplained data loss, severe thermal condition or any request to root/unlock/flash/wipe.

M7 can be marked **COMPLETE** only when every applicable hardware row has device-backed evidence, recovery to stock launcher is demonstrated, no high-severity unresolved safety/security finding remains, and an independent reviewer signs the evidence. If the exact device is unavailable, M7 remains **BLOCKED**; this prepared protocol is not hardware validation.

## 12. Explicitly prohibited during this protocol

- No `fastboot`, bootloader unlock, root acquisition, custom recovery, firmware/AOSP flash, factory reset or production deployment.
- No ADB secure-setting override to enable TalkBack or bypass user consent.
- No hidden credential entry, biometric/Keyguard bypass, unrestricted AccessibilityService execution or background permission grants.
- No production owner-key deletion, alias enumeration/cleanup, authority rotation or trust-store corruption.
- No call recording, covert microphone capture, personal notification collection or publication of device identifiers.
- No claim of OTA rollback, signed production readiness or AI telephony from the tests in this document.

**Current disposition:** protocol prepared; physical Pixel 9 Pro access and explicit operator approval are still required. The upstream shared engineering-factory package remains unverified; this document is project-specific work.

## 2.1 Offline snapshot preflight validator

After separate, explicit owner approval to connect the device, an operator may collect only the read-only values listed above and place them in a local JSON file. Do not retain the output of `adb devices -l`; it contains the device serial. Do not include serial, IMEI, phone number, SIM identifiers, account names, Wi-Fi SSID/BSSID, personal notifications or the full build fingerprint.

The project validator is deliberately offline: it does not invoke ADB or any shell command. Run it against the redacted snapshot:

    python3 scripts/m7_pixel9pro_preflight.py --snapshot /path/to/redacted-snapshot.json --output /path/to/preflight-result.json

The input schema is `mrnothing-m7-pixel9pro-preflight-v1` and contains only `adb_state`, the allowlisted `properties` below, and the PackageManager `features` lines:

    {
      "schema": "mrnothing-m7-pixel9pro-preflight-v1",
      "adb_state": "device",
      "properties": {
        "ro.product.manufacturer": "Google",
        "ro.product.model": "Pixel 9 Pro",
        "ro.product.device": "caiman",
        "ro.build.version.release": "16",
        "ro.build.version.sdk": "36",
        "ro.kernel.qemu": "0",
        "ro.boot.flash.locked": "1",
        "ro.boot.verifiedbootstate": "green",
        "ro.boot.vbmeta.device_state": "locked"
      },
      "features": ["feature:android.hardware.strongbox_keystore"]
    }

The example is synthetic, not a device observation. The validator blocks wrong model/codename, unauthorized/disconnected ADB, unlocked/unknown boot state, emulator indication, unsupported API baseline or missing StrongBox feature. It emits only allowlisted model/build fields and named pass/fail checks; unknown input fields are not copied into the report.

A passing report is `ready_for_supervised_hardware_session` only. It always sets `acceptance_passed=false` and `strongbox_key_security_level_verified=false`. PackageManager feature advertisement does not prove a generated key is StrongBox-backed; only the separately approved instrumentation check of `KeyInfo.securityLevel == SECURITY_LEVEL_STRONGBOX` can establish that key-level property. This offline preflight cannot install, grant permissions, reboot, alter settings or complete M7.
