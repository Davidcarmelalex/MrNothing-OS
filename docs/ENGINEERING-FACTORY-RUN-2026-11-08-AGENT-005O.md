# Engineering Factory Run — AGENT-005O

**Date:** 2026-11-08  
**Repository:** `Davidcarmelalex/MrNothing-OS`  
**Authorized branch:** `feat/phase1-agentic-phone`  
**Starting head:** `75f6f2384181b8a7107850bf5f40cf890db8527a`  
**Task:** remove an unnecessary AccessibilityService prerequisite from actions that do not use accessibility.

## Audit

- Complete recursive tree: 360 entries; not truncated.
- Latest 10 commits inspected.
- Open PRs: #1 and #3–#7. PR #1 is the only open PR using this branch; it targets main and remains draft.
- PR #1 has no submitted reviews or inline review threads.
- `PROJECT-ADAPTER.md` and `docs/ENGINEERING-FACTORY-ROADMAP.md` exist; repository `SKILL.md` is absent. Upstream shared package remains unverified.
- Exact starting-head Phase 1 push/PR, CI-003 push/PR and QA-005 emulator PR passed.

## Finding

The AGENT-005N coordinator composed the common `ScreenActionPreflight` before the action-specific `ActionPermissionGate`. The common preflight required the app-owned AccessibilityService to be enabled for every action. This contradicted AGENT-004J's action-specific contract and imposed an unnecessary high-privilege Android setting on simple app launch and MediaProjection screen capture.

## Implementation

- Common owner-session, device-safety, visible-consent, restricted-surface, emergency-stop and revocation checks remain mandatory for all actions.
- `navigate` relies on the exact package/activity launchability check; no AccessibilityService or projection is required.
- `read_screen` requires the active user-approved MediaProjection session; no AccessibilityService is required.
- `scroll` still requires the app-owned AccessibilityService enabled in the coarse policy and connected in the action-specific gate.
- Unknown actions remain blocked.

Added two Kotlin policy tests, one coordinator composition test and a Python source-boundary regression test. Updated SEC-014F to make the least-privilege contract explicit.

## Safety

No Android service or permission was added, no permission prompt was shown, no owner state was granted, and no executor or CommandRouter wiring was added. The CommandRouter remains fail-closed. No local test execution is claimed; exact-head GitHub Actions are required.

## Review

The author re-read the diff and assertions against AGENT-004J and SEC-014F. This is not independent human security approval; the independent supervisor gate remains pending.

## Milestones

M1 foundation, M2 OS interface and M6 security/privacy remain in progress. M3 remains partial. M4 is not started. M5 is not accepted. M7 and M8 remain blocked. No milestone is complete.
