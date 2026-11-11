# QA-STACK-018 — bounded HOME-consent UI retry (emulator only)

## Evidence and scope

At PR #51 head 2defac371cc03f6c1c2d8caa5440eda3ddc2bce0, GitHub
Actions QA-005 run 43078716635 failed at QA-007, after the 39
instrumentation tests and split JUnit evidence validator had passed.
The failure was "Android permission controller is not foreground".
Artifact 13884715033 contains qa007/before.xml and qa007/prompt.xml;
both show the Mr Nothing launcher, with the same enabled and clickable
"Choose Mr. Nothing as Home" button. The HOME holder before the tap was
the stock Nexus Launcher. This establishes a missed/ineffective synthetic
tap in that run, **not** the precise cause of the missing role dialog.
Phase 1 and CI-003 passed at the previous SHA; the QA-005 workflow failed
and skipped QA-008 and later steps.

## Bounded change

The QA-007 disposable-emulator harness now classifies the UI after the
first tap. A valid system PermissionController prompt is accepted as
before. An unchanged launcher with the exact clickable chooser control
is eligible for **one** additional synthetic tap, but only after
reconfirming the HOME role holder is unchanged. Any unexpected window,
mixed package hierarchy, malformed role prompt, role mutation, or second
missed tap fails closed. The existing negative-consent path still uses
BACK and verifies that HOME ownership did not change.

This is a **test harness** resilience change, not an Android app or
permission policy change. It does not automatically approve a role,
alter a real device, or claim to fix the underlying input delivery
problem. The QA-008 explicit-consent test remains separate.

## Verification

- Focused QA-007 parser tests: 13 passed (five new classifier cases).
- Full scripts/phase1-preflight.sh: 1,164 Python tests passed locally.
- bash -n, python -m py_compile, Python compileall and Git whitespace
  checks: passed.
- Actual QA-005 emulator rerun at the new SHA: **pending**.
- Independent human security/accessibility review: **pending**.
- Physical Pixel 9 Pro, StrongBox, spoken TalkBack, signed OTA and
  recovery: **not tested**.

No M1–M8 milestone is independently accepted. Upstream shared SKILL.md
is unverified; PROJECT-ADAPTER.md is local and project-specific.
