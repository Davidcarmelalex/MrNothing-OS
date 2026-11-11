# UX-AGENT-006 — Invalidate hidden rehearsal on preview-mode switch

Scope: draft stack on QA-UX-008 / PR #48, targeting only `feat/phase1-agentic-phone`. No permission, network, device executor, Android root, owner-consent grant or production behavior is added.

## Finding

Before this change, an owner could start and acknowledge a sample rehearsal, then inspect a single sample action or fixed-plan preview. Those two display modes replaced the status text without invalidating the earlier rehearsal cursor. Selecting “Preview next sample step” subsequently resumed the previously acknowledged, now-hidden sample. Although the no-op supervisor always denied execution, the UI did not make the active rehearsal boundary clear.

## Remediation

`AgentPlanPreviewActivity.preview` and `previewPlan` now cancel any existing rehearsal before changing display modes. A subsequent “next step” remains terminal with zero retained steps; beginning again requires a deliberate new start and simulation acknowledgement. Existing onStop/cancel behavior is unchanged.

## Acceptance evidence

- Android instrumentation regression `testSwitchingPreviewModesInvalidatesAcknowledgedRehearsal` covers both mode switches and asserts terminal denial, zero cursor, and renewed review requirement.
- Python structural gate checks that both entry paths invalidate the rehearsal and the instrumentation regression remains registered.
- Locally executed on an isolated clean checkout at parent `3bb69d0eb3659974b8d381a63be2aaf86abc9bc5`: 995 Python preflight tests passed; Android manifest source gate, launcher accessibility source gate, Python compilation, Bash syntax and `git diff --check` passed.
- **Not executed locally:** Android/JVM compilation, Android instrumentation, exact-head GitHub CI, spoken TalkBack, physical Pixel 9 Pro, signed release and OTA recovery. Hosted exact-head results must be inspected after publication.

The upstream `SKILL.md` package remains unverified. The local `PROJECT-ADAPTER.md` is project-specific, not proof of upstream installation. All M1–M8 completion gates remain unaccepted; independent human security/UX approval is pending.
