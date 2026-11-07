# Engineering Factory Run — AGENT-004P: exact SystemUI Keyguard PIN input

Date: 2026-11-07
Repository: Davidcarmelalex/MrNothing-OS
Branch: feat/phase1-agentic-phone
Audit head: 0b27ec5c8b0e527ab653cedbc5ad60182ba1d789

## Audit and evidence

- Full recursive tree at the baseline: 328 entries, not truncated.
- Latest 20 commits inspected. The branch was 268 commits ahead of main and zero behind at the baseline.
- Six open PRs (#1 and #3–#7) inspected; PR #1 remains open/draft and matches the branch. Other PRs untouched.
- PROJECT-ADAPTER.md and roadmap present; repository SKILL.md absent. Library title search and shared-with-me listing found no authorized upstream package. It remains unverified/not installed.
- Phase 1 push/PR and CI-003 push/PR passed on 0b27ec5. Phase 1 Python policy: 681 tests passed; Android debug unit/build/dependency gates passed. CI-003 verifier: unsigned release APKs byte-identical, 7,862,996 bytes, SHA-256 1283cc77cb9756f336c931d7db6cb97d6724ac0717995f94757eb101fb31c05b; normalized contents and runtime SBOM identical; release_ready=false.
- QA-005 run 42369272181 failed before instrumentation. Artifact 13572737599 was downloaded and inspected.

## Root cause

The forced sleep/wake correction worked: power evidence recorded mWakefulness=Asleep, and the post-wake Keyguard policy recorded both showing fields true. The screenshot after the synthetic input attempt showed Android SystemUI Enter PIN with an empty field and visible keypad. Both Keyguard state fields remained true. No instrumentation test started, no ANR occurred and no application crash was established. The remaining defect was the use of adb input text against the lockscreen numeric keypad; it did not populate the PIN field.

## Implementation

- Add scripts/qa005_unlock_keyguard.py to parse a UIAutomator hierarchy and require the exact SystemUI keyguard_pin_view with nested pin_container.
- Require unique enabled/clickable SystemUI key0–key9 and key_enter nodes, positive bounds fully inside the actual emulator display.
- Require emulator serial and ordinary shell UID 2000. Read the synthetic PIN from TEST_PIN environment, accept only 4–8 decimal digits, and never log it.
- Tap only coordinates derived from the exact node bounds. No guessed coordinates or text injection.
- Capture the hierarchy in the QA evidence artifact before input.
- Add unit tests for valid and adversarial hierarchies and update the workflow source gates.
- Keep the post-input Keyguard hidden-state verification and cleanup trap.

## Safety and acceptance

This changes only the disposable emulator QA harness, static gates, unit tests and documentation. No production app code, manifest, AccessibilityService, MediaProjection, permission, CommandRouter or executor change. No adb root, physical Pixel 9 Pro, flashing, OTA, signing key or deployment. Exact-head Phase 1, CI-003 and QA-005 must pass; inspect JUnit and runtime artifacts before acceptance.

## Specialist gates

Android: platform lifecycle and system UI integration. AI/agents: action schemas and supervised plans. Security: consent, replay and revocation. UX/accessibility: disclosure, keyboard and TalkBack. CI/QA: exact-head instrumentation and supply-chain evidence. Hardware/release: Pixel 9 Pro, StrongBox, signing and OTA. Independent supervisor: review exact diff and runtime evidence; human security/accessibility approval remains pending.

## Milestones

M1 Foundation — IN PROGRESS.
M2 OS interface — IN PROGRESS.
M3 Agentic intelligence — PARTIAL.
M4 Permission-controlled integrations — NOT STARTED.
M5 Pixel 9 Pro compatibility — NOT ACCEPTED.
M6 Security/privacy — IN PROGRESS.
M7 Physical hardware validation — BLOCKED.
M8 Production readiness — BLOCKED.

No milestone is complete.

Next task: verify exact-head QA-005 after the exact-node PIN entry correction; then complete independent security/accessibility review before any AccessibilityService declaration. MediaProjection remains separate and CommandRouter fail-closed.
