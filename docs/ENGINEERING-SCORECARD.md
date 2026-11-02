# Engineering scorecard — evidence-based

**Audit date:** 2026-11-02. **Branch:** `feat/phase1-agentic-phone`. **Source of truth:** [engineering roadmap](ENGINEERING-FACTORY-ROADMAP.md) and current GitHub Actions results.

| Area | Verified evidence | Remaining gate |
| --- | --- | --- |
| Android launcher | Kotlin HOME activity, app catalog and device diagnostics; UX-003 source adds SP typography, accessibility headings, descriptive buttons, 56dp touch targets and explicit Android Home settings recovery; 5 new source-gate tests passed on VPS | Emulator/device installation, real TalkBack and 200% font-scale checks, stock-launcher recovery E2E and independent review |
| Android build integrity (CI-002) | Gradle 8.9 ZIP verified against official pinned SHA-256; source manifest policy gate; two byte-identical debug APK builds in one GitHub runner; debug APK digest/provenance uploaded; [push CI passed](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/41358053978) and [PR CI passed](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/41358058925) at `ecfbf9f5d35ed266cd54a5b621041afc0302da4d` | Independent reviewer approval; pinned action SHAs, dependency verification, cross-run reproducibility, release signing and SBOM |
| Security policy | Python policy tests; HMAC/freshness/replay prototypes | Device-bound enrollment, key revocation, audit and independent review |
| Command admission | Durable SQLite replay ledger, strict validation and negative tests | Network authentication, device key storage and production integration |
| HERMES orchestration | Constrained adapter and local validation tests | Actual agent planner, executor, cancellation and task verification |
| Voice and SIM telephony | Design only | Real Pixel hardware and consent validation |
| Pixel AOSP firmware | Design only | Build, compatible drivers, secure boot, OTA and rollback |
| Release | CI debug APK artifact exists, marked **not for release** | Signed reproducible release, SBOM, OTA and recovery drill |

**Local verification for CI-002:** VPS `maverix-vps` ran **51 Python tests, all passed**, source-manifest gate passed, Python compile checks passed, `git diff --check e3c570a HEAD` passed, and a targeted new-script dangerous-call scan returned no matches. GitHub CI completed both jobs successfully for push and PR at `ecfbf9f`. No emulator or physical Pixel was used.

**UX-003 local verification (2026-11-02):** VPS ran **56 Python tests (all passed)**, the launcher source accessibility/recovery gate passed, the Android manifest gate passed, Python compileall passed and Git whitespace checks passed. Android compilation for UX-003 is tracked in GitHub Actions; do not claim an APK passed until those runs complete. Source checks are not TalkBack or emulator evidence. Independent review remains pending.\n\n**Gate status:** M1 IN PROGRESS; M2 IN PROGRESS; M3 NOT STARTED; M4 NOT STARTED; M5 NOT STARTED; M6 IN PROGRESS; M7 BLOCKED ON HARDWARE; M8 BLOCKED. **No milestone complete or independently approved.** CI-002 implementation is verified by automated checks, but supervisor signoff is `PENDING_INDEPENDENT_REVIEW`.

Previous overall completion percentages were subjective planning estimates, not objective evidence. Do not use them as a release metric.

## Verified update — 2026-11-02, QA-011 and QA-012

GitHub Actions [QA-011 run 41437333057](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/41437333057) completed successfully at 3ff50a3. Its retained TalkBack preflight reports that the TalkBack package is installed but the accessibility service is disabled; spoken navigation is not accepted. Earlier emulator QA-005 through QA-010 steps were green at this head. These results supersede the historical source-only baseline above but do not confer independent milestone signoff.

QA-012 adds a bounded read-only emulator UI hierarchy audit for section order, labelled consent/recovery/settings actions and minimum system-action touch targets. Its 14 synthetic regression tests and the full 150-test Python suite passed on the VPS. The QA-012 parser also passed against the retained QA-011 emulator hierarchy with representative density 2.75, but that is replayed evidence, not a new emulator run. New QA-012 emulator CI must pass before claiming its runtime acceptance. It does not enable TalkBack and explicitly records spoken_navigation_verified=false and acceptance_passed=false.

M1/M2/M6 remain IN PROGRESS; M3/M4/M5 have unmet gates; M7 is BLOCKED on physical Pixel 9 Pro; M8 is BLOCKED. All independent supervisor approvals remain PENDING. Upstream SKILL.md remains unverified; PROJECT-ADAPTER.md is local only.

## Verified update — 2026-11-02, AGENT-013 offline plan simulator

QA-012 Android 15 emulator [run 41446504887](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/41446504887) completed successfully at `2caa1b6`, including the read-only semantics step. It does **not** prove spoken TalkBack navigation; TalkBack remains disabled in the recorded QA-011 preflight.

AGENT-013 adds a pure Python, no-device, no-network deterministic plan simulator for M3. On VPS: 34 targeted sandbox tests and 184 total Python tests passed; Python compileall, Android manifest security gate, launcher source accessibility gate and Git whitespace checks passed. No emulator or physical-device test was run for AGENT-013 locally. New GitHub CI for AGENT-013 must be inspected after push.

This is only a partial M3 engineering slice: no real tool execution, no device enrollment, no verified remote authentication, no owner consent flow and no independent supervisor approval. **All M1–M8 completion gates remain unmet.**


## SEC-014A — screen/UI default-deny policy boundary (2026-11-02)

Python and Kotlin low-risk policies now exclude `read_screen`, `navigate`,
and `scroll`. These return approval-required for authenticated requests
and deny unauthenticated requests; contact approvals cannot be reused.
No screen/UI execution is enabled. See [SEC-014 consent boundary](SEC-014-CONSENT-BOUNDARY.md).
This is a partial remediation only: trusted per-session consent, Android
permission enforcement, revocation, expiry, restricted-screen checks and
independent security review remain **OPEN**. All M1–M8 gates remain open.


## SEC-014C — owner credential safety preview (2026-11-02)

A non-exported Android Activity now provides an explicit local system-credential
verification **preview** for read_screen, navigate and scroll. It does not
issue consent, grant Android permissions or enable execution. Ten Kotlin
state-machine tests are added, pending Android CI execution. The full local
Python suite and source security gates are to be recorded in the corresponding
engineering report. Keystore binding, permission checks, revocation of real
sessions, real-device tests and independent security review remain OPEN.
No milestone is independently approved. Upstream shared SKILL.md is unverified.

## SEC-014D — device-lock preflight for credential preview (2026-11-02)

The owner-facing **preview only** now checks actual Android lock/user/interactive
state before the credential prompt and after its result. Pure Kotlin and source
tests reject unsafe states; no consent issuance or device execution is enabled.
See [SEC-014D](SEC-014D-DEVICE-LOCK-PREFLIGHT.md). GitHub CI and independent
security review remain separate acceptance gates. SEC-014 and all milestones
remain open. Upstream SKILL.md remains unverified.

## SEC-014E — credential preview overlay hardening (2026-11-02)

Added `FLAG_SECURE`, obscured-touch filtering, preview revocation on suspicious
touches, and pure Kotlin/Python regression tests. See
[SEC-014E](SEC-014E-PREVIEW-OVERLAY-HARDENING.md). Android CI and independent
review must be checked separately. No permission or executor is enabled; no
M1–M8 gate is complete. Upstream shared `SKILL.md` remains unverified.
