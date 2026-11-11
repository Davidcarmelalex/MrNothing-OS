# QA-STACK-019 — exact HOME-consent prompt package integrity

## Motivation and bounded change

At candidate `5b878b1571f04f2cfa154ddb793f99baae6d00dd`, all three exact-head hosted workflows completed successfully, including QA-005. A separate source review found that `qa007_role_consent.py` accepted any package whose name *contained* `permissioncontroller`, and could classify a mixed-package hierarchy as a valid system role prompt if an unrelated node supplied the product label. This is a **test-evidence integrity weakness**, not evidence that Android granted a role without consent.

The QA-007 disposable-emulator parser now requires a single exact platform permission-controller package throughout the prompt hierarchy: `com.google.android.permissioncontroller` or `com.android.permissioncontroller`. Unexpected overlays, mixed package hierarchies and package-name suffix spoofs fail closed. The launcher retry remains bounded to one unchanged-state retry, and the separate explicit-consent QA-008 path is untouched. This change does not grant permissions, alter an Android app, or interact with a physical device.

## Acceptance

- Six negative/positive regressions cover the AOSP package, suffix spoof, unknown overlay, target label from another package, mixed trusted packages, and direct prompt-verifier overlay rejection.
- Run focused QA-007 unit tests, full Python preflight, manifest/accessibility gates, Python compilation, shell syntax, workflow YAML parsing, and Git whitespace checks.
- Exact-head hosted Phase 1, QA-005 emulator and CI-003 reproducibility must pass before this commit is accepted.
- Independently inspect actual JUnit and APK provenance artifacts when GitHub artifact download is available. A green workflow alone is not artifact-level independent verification.

## Outstanding

Independent human security and accessibility approval, spoken TalkBack, physical Pixel 9 Pro/StrongBox, signed release and OTA recovery remain unverified. No M1–M8 milestone is accepted. The local `PROJECT-ADAPTER.md` is not an installed upstream `SKILL.md` package.
