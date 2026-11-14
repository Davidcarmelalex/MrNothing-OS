# QA-STACK-037 — Restore exact-head UX instrumentation evidence

**Scope:** draft branch stacked on QA-STACK-036 / PR #84, rooted exclusively in `feat/phase1-agentic-phone`. No production, device, signing, permission or executor changes.

## Evidence-driven defect

At commit `ff1ca28f9f609666e665920f66192f006def08d1`, GitHub Actions QA-005 run [43585896491](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/43585896491) executed 37 uncredentialed Android instrumentation tests and 2 credential-protected tests, both with no failed cases. The SEC-023B1A check against the preserved first suite passed. QA-STACK-008 incorrectly read Gradle's *live* XML directory **after the second Gradle invocation replaced it**, and failed because MemoryVault/UX tests were no longer present. The failure was a test-evidence path defect, not evidence that the UX cases failed.

The fix makes QA-STACK-008 read the existing immutable-for-this-job saved uncredentialed report directory. The verifier still requires both MemoryVault methods, all three UX rehearsal methods, no failures/skips, and valid XML. QA-STACK-011 continues to require both saved uncredentialed and current credentialed suites. Scoped manual dispatch for this review branch permits exact-head hosted emulator verification without broadening automatic triggers.

## Independent acceptance gates

- Exact-head Python regression, source/security checks and hosted Phase 1 Android/JVM checks.
- Exact-head QA-005 emulator job must run both suites, report 37+2 passing cases, pass QA-STACK-008 and QA-STACK-011, and complete launcher/recovery and accessibility smoke.
- CI-003 strict independent runner provenance remains blocked by host-image/SBOM drift until pinned environment or reviewed policy; no gate weakening here.
- Independent non-author security/UX reviewer must inspect the diff and evidence. Physical Pixel 9 Pro, spoken TalkBack, signed releases and OTA remain unverified.
- Upstream shared `SKILL.md` remains absent and unverified; existing `PROJECT-ADAPTER.md` is retained.
