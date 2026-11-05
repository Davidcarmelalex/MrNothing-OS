# MrNothing OS — Universal Engineering Factory project adapter

**Scope:** `Davidcarmelalex/MrNothing-OS`, exclusively `feat/phase1-agentic-phone`. Target device: **Google Pixel 9 Pro (`caiman`)**.

**Provenance:** At the 2026-11-02 audit, no `SKILL.md` or `PROJECT-ADAPTER.md` existed in the audited repository tree. No authorized copy of the reusable upstream Universal Autonomous Engineering Factory package was found in the supplied files. **This adapter is a local, project-specific implementation of the user's factory contract, not a claim that the upstream shared skill was installed or verified.** Do not silently overwrite it if the upstream package later arrives; review differences first.

## Mission and architecture
Build an accessible, privacy-preserving, agent-first Android experience that can replace the stock launcher with explicit user choice. Preserve compatibility with ordinary Android apps. Investigate a Pixel-specific AOSP distribution separately, only after device and firmware safety gates. Root is not a prerequisite for basic functionality and must never be silently obtained.

Components: Kotlin HOME launcher and device diagnostics; consented Android system integrations; Python HERMES policy/orchestration; authenticated, device-bound command channel; audited tool registry; voice interface; optional AOSP/device build; signed OTA/recovery. Existing Termux modules remain legacy prototypes, not proof of integrated functionality.

## Specialist ownership and path boundaries
| Role | Owns | Must verify |
| --- | --- | --- |
| Android engineer | `android/**` | compile, launcher selection/recovery, lifecycle and permissions |
| AI/agent engineer | `agents/**`, `core/hermes_gateway.py`, agent orchestration | deterministic plans, tool limits, cancellation, injection resistance |
| Security engineer | `core/*security*`, `core/*policy*`, threat model | identity binding, consent, replay prevention, fail-closed paths |
| UX/accessibility engineer | launcher UI and UX docs | TalkBack, contrast, large text, focus, reduced motion |
| CI/QA engineer | `.github/workflows/**`, `tests/**`, scripts | repeatable checks, artifact provenance, no unsupported claims |
| Hardware/release engineer | device, OTA, installer docs and future firmware | Pixel-specific hardware matrix, signed images, rollback |
| **Independent supervisor/verifier** | evidence review across all areas, no self-approval | inspect diff, rerun tests, challenge security assumptions, record gate decision |

Roles are **responsibilities**, not a claim that separate agents or humans have been launched. When separate independent reviewers are unavailable, mark the independent gate **PENDING** rather than self-certifying.

## Workflow per engineering run
1. Read latest branch SHA, open PRs, CI, tree, architecture, adapter, tests and prior evidence. Check for concurrent changes.
2. Select the highest-priority **unblocked and bounded** task with a measurable acceptance test.
3. Work only on the existing feature branch or an explicitly scoped branch; do not merge `main`.
4. Implement minimal compatible changes; never duplicate code or overwrite unrelated changes.
5. Run targeted tests, full available tests and static/security checks; state which environments were **not** tested.
6. Request independent verification, or explicitly record the absence of it. Keep PR draft until all required gates pass.
7. Record commit SHA, tests, CI, blockers and next task in the run report.

## Safety and release policy
No unauthorized root escalation, credential extraction, covert recording, unrestricted shell tools, CAPTCHA/biometric bypass, production deployment, device flashing, bootloader unlocking or irreversible changes. All sensitive actions require explicit informed user approval; emergency stop and recovery are mandatory. Android accessibility permissions and screen capture must be user-enabled, visible and revocable. Physical telephony audio must be validated on a real Pixel; root or default-dialer status does not prove audio routing. Sign release artifacts using protected keys; never commit keys or secrets. Supply SBOM and reproducible-build evidence before release.

**Milestone gates:** See [docs/ENGINEERING-FACTORY-ROADMAP.md](docs/ENGINEERING-FACTORY-ROADMAP.md). A milestone is COMPLETE only when its listed evidence exists and the independent supervisor has approved it.


## Audit update — 2026-11-05

The recursive tree of feat/phase1-agentic-phone contains this local PROJECT-ADAPTER.md and no SKILL.md. An authorized Library title-only search for SKILL.md returned no result, and no upstream shared package was supplied or verified. The upstream package remains unverified; this local adapter must not be represented as an installed copy.

SEC-019B extends the consent boundary with exact live SSLSocket-object binding, adapter-retained issued challenges, monotonic session/challenge expiry and a three-argument verifier API. The executor remains disconnected. Independent security approval remains pending.
