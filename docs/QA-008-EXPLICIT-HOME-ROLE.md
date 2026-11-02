# QA-008: explicit HOME acceptance and recovery route

Run only on the disposable Android API 35 emulator. This scenario deliberately taps an Android permission-controller approval control after verifying its package, label, bounds and uniqueness. It does **not** use privileged role overrides. Verify the HOME holder changes exclusively to Mr. Nothing, pressing HOME launches the app, and its recovery button opens Android Settings. Keep role snapshots, prompt and launcher UI hierarchy, and screenshot as CI artifacts.

This is not a physical-device test, stock-launcher re-selection test, TalkBack test or firmware validation. Unexpected system dialog variants fail closed and require inspection of actual emulator evidence. Independent signoff remains pending.


## 2026-11-02 failure and remediation

GitHub Actions [run 41401079630](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/41401079630) built and booted the API 35 emulator. QA-005, QA-006 and QA-007 passed. QA-008 stopped at the Python helper import, before any consent approval tap: direct invocation `python3 scripts/qa008_role_accept.py` could not import `scripts.qa007_role_consent` because the repository root was not on `sys.path`. The helper now supports both direct script execution and package imports, with subprocess regression tests for each. **This change is source/test verified only until the next QA-008 emulator workflow passes.** No HOME grant or recovery success is inferred from the failed run.


### Consent UI evidence inspection

The retained emulator `qa008/prompt.xml` from run 41401079630 shows two Android permission-controller radio choices: **Mr. Nothing OS** and **Pixel Launcher**. Neither was selected and the `Set as default` button was disabled. The QA-008 test now explicitly selects the uniquely identified Mr. Nothing system-radio row, captures a second `selected.xml` hierarchy, and only then permits tapping the enabled system approval button. If the option or approval control cannot be uniquely verified, the test fails closed. The change does not bypass consent or grant roles through shell privileges.


### 2026-11-02: consent succeeded; pre-role assumption corrected

[Emulator run 41407548448](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/41407548448) passed QA-005, QA-006 and QA-007, then reached QA-008. The captured Android permission-controller hierarchy shows **Mr. Nothing OS selected** (radio checked) and the **Set as default** control enabled. After the explicit system approval tap, retained role snapshots contain a blank pre-grant HOME holder and the exclusive post-grant HOME holder tech.mrnothing.os. The QA-008 helper incorrectly required a nonempty *before* role holder, so the CI job failed despite the successful role assignment.

The helper now accepts a legitimately empty prior holder list while still rejecting an already-held role, a missing grant, and any nonexclusive post-grant role list. Regression tests cover the exact observed snapshots and direct CLI invocation. **The full QA-008 runtime acceptance gate remains open** until a subsequent CI run passes the HOME launch and recovery-settings steps; those steps were not reached in this failed run.
