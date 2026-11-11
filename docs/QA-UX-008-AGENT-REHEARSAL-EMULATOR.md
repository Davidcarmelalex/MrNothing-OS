# QA-UX-008 — Offline agent rehearsal emulator acceptance

Scope: draft candidate based on PR #46, targeting only feat/phase1-agentic-phone. Owner-visible entry into the non-exported preview Activity; no executor, consent grant, permission or physical device.

The Android instrumentation class AgentPlanPreviewActivityTest uses the real launcher button to open the Activity. It asserts simulation acknowledgement is required, pre-ack progression refuses, each of three fixed sample steps advances only the display, the supervisor denies all steps, completion is terminal, cancellation clears the state, and leaving the Activity triggers onStop clearing. No authenticated admission or device execution is implemented.

The QA-UX-008 shell smoke is restricted to emulator-* plus ro.kernel.qemu=1. It tests owner-visible navigation, 200% font scale with restoration on EXIT, initial/review/cancel hierarchy, labeled keyboard focus and return to launcher. It preserves UIAutomator XML and a screenshot. **FLAG_SECURE deliberately redacts the Activity screenshot; the PNG must not be represented as a visual proof of the protected screen.** UI hierarchy and instrumentation assertions are the primary evidence. It does not claim spoken TalkBack, RTL, physical Pixel 9 Pro, hardware StrongBox, signed OTA or production readiness.

Acceptance requires exact-head Phase 1 Android/Python and QA-005 green with uploaded instrumentation and hierarchy evidence, then independent human security/UX review. Static tests are not emulator evidence. CI-003 release reproducibility was already passed at predecessor PR #46; this candidate's own release gate is not assumed to have run.

Upstream shared SKILL.md remains unverified; the repository-specific PROJECT-ADAPTER.md is not an installed upstream package. No milestone is accepted by this document.
