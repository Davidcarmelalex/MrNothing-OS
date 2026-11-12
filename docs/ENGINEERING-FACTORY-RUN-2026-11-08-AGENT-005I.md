# AGENT-005I — QA-012 viewport-complete structural semantics

**Audit head:** 271af2d097c2b2445079b8c6c41a05336433420b  
**Authorized branch:** feat/phase1-agentic-phone  
**Selected task:** Correct the QA-012 structural semantics harness using the exact emulator artifact.  
**Scope:** Emulator-only QA scripts, parser, tests and documentation. No production Android code changed.

## Audit and repository instructions

The recursive tree contained 346 entries and was not truncated. Twenty recent commits were inspected; the branch was 298 commits ahead of main and zero behind. Six open PRs (#1 and #3–#7) were inspected. PR #1 matched the authorized branch, remained open/draft against main, and had no submitted reviews or inline review threads. PRs #3–#7 were left untouched. The branch is unprotected; the rulesets collection was empty. PROJECT-ADAPTER.md and the engineering roadmap are present. Repository SKILL.md is absent. An authorized Library search did not find the upstream shared package; it remains unverified and is not claimed installed.

## Exact-head evidence

- Phase 1 push run 42414351859 and PR run 42414355914 passed. The Python policy job ran 723 tests; Android debug unit tests, debug APK build, repeat debug APK byte comparison, strict dependency verification, modified-dependency negative control and manifest security gate passed.
- CI-003 push 42414352066 and PR 42414356039 passed independent-runner verification. The unsigned APKs were byte-identical (7,862,996 bytes; SHA-256 1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b; normalized contents SHA-256 fc4aa03eb6754f76fe9fa005495d923da85678aaa3bb5f92cd942f2375575140). The scoped environment inventory covered 1,260 components. Provenance explicitly reports release_ready=false.
- QA-005 PR run 42414355907 built both APKs, booted the disposable Android 15 emulator and ran all 30 instrumentation tests: 30 passed, zero failed. QA-005, QA-006, QA-007, QA-008, QA-009, QA-010 and QA-011 passed. QA-012 failed with Missing or ambiguous section Installed apps; QA-013, QA-020B2 and QA-020B3 were skipped downstream.

Artifact 13591805010, SHA-256 3da97e398385d46a63e89171fe129d172a6bacb3a7d5caae623b281475fecc73, was downloaded and inspected. Both the original launcher hierarchy and QA-012 hierarchy were 6,526 bytes. The XML contained MR. NOTHING, Device status and visible buttons through the lower viewport boundary, but no Installed apps node. The screenshot confirmed that the app's ScrollView extends below the display. MainActivity adds Installed apps after the preceding action controls. The failure was an incomplete single-viewport capture, not a missing production section or failed instrumentation test.

## Implementation

- QA-012 now captures the top viewport, then uses at most five display-size-derived upward swipes on the disposable emulator until Installed apps becomes visible.
- The parser accepts repeated --hierarchy inputs, merges snapshots in top-to-bottom order and removes one occurrence of nodes overlapping the immediately previous viewport using class, resource ID, text, content description and sibling index. Distinct sibling indices and duplicate controls remain visible to ambiguity checks.
- Duplicate controls within a snapshot or newly introduced in a later snapshot remain visible to ambiguity checks; overlap de-duplication must not hide duplicate actions.
- Both top and bottom hierarchy XML plus screenshots are retained.
- No TalkBack service is enabled. semantics.json continues to set spoken_navigation_verified=false and acceptance_passed=false.
- No system accessibility setting, HOME role, permission, app installation, production component, trust store or executor is changed by QA-012.

## Tests executed locally

In an isolated temporary harness containing the changed QA-012 source/test files and a workflow reference stub:
- python -m unittest -v tests.test_qa012_semantics — 21 passed.
- python -m compileall -q scripts tests — passed.
- bash -n scripts/qa012_semantics_smoke.sh — passed.
- Fake-ADB shell integration harness with synthetic top/bottom viewport XML — passed; parser reported structural_checks_passed=true, hierarchy_snapshots=2, spoken_navigation_verified=false and acceptance_passed=false.

The fake-ADB harness validates shell argument flow and parser integration only; it is not an Android emulator. The focused local harness is not a substitute for the complete repository policy suite or an emulator run. Exact-head GitHub CI and QA-005 reruns are required after this correction.

## Milestones and next gate

M1 Foundation — IN PROGRESS; M2 OS interface — IN PROGRESS; M3 Agentic intelligence — PARTIAL; M4 permission-controlled integrations — NOT STARTED; M5 Pixel 9 Pro compatibility — NOT ACCEPTED; M6 security/privacy — IN PROGRESS; M7 physical hardware validation — BLOCKED; M8 production readiness — BLOCKED. No milestone is complete.

Next: verify exact-head Phase 1 and CI-003, then rerun QA-005. Confirm all 30 instrumentation tests, QA-012 top/bottom snapshot merge, and downstream QA-013/QA-020B2/QA-020B3. TalkBack spoken acceptance and independent human security/accessibility review remain pending. No physical Pixel 9 Pro test, signed production release or production readiness is claimed.
