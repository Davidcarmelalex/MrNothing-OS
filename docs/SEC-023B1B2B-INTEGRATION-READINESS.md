# SEC-023B1B2B — MemoryVault integration readiness, source-only gate

**Base:** feat/phase1-agentic-phone (f42af837bcb8eed478cadbc472b7571441449a7a at audit). **Scope:** separate draft PR, no production code or service activation. Upstream shared SKILL.md remains absent/unverified; PROJECT-ADAPTER.md is project-specific, not an installed upstream package.

## Why this exists

MemoryVault proposals #13–#19 are independent draft PRs, not one integrated implementation. They overlap on docs/ENGINEERING-FACTORY-ROADMAP.md; #16 and #18 also touch Android Gradle and QA-005 workflow files. Successful CI on an individual PR does **not** prove that all seven components compile or remain secure when combined. Integration must reject silent alias drift and accidental enabling/exporting of the dormant service.

## Proposed component dependency map

| PR | Component | Integration requirement |
| --- | --- | --- |
| #13 | Design/threat model | Review against actual Android/PaperClip behavior |
| #14 | Canonical Python envelope preflight | Preserve AAD, bounded TTL and no persistence |
| #15 | JVM owner admission | Caller assertions are not cryptographic identity proof |
| #16 | Disabled private Android service | enabled=false, exported=false, no intent filters, no Binder |
| #17 | Read-only Keystore preflight | StrongBox key metadata is not proof of authentication |
| #18 | Owner provisioning specification | Same AES-GCM key alias, no fallback; no key generation |
| #19 | One-shot consent-intent binding | Same alias, no authorization without real CryptoObject proof |

## Source-only preflight

Run: python3 scripts/memory_vault_integration_audit.py --root .

The script emits deterministic JSON and **never returns exit code 0**. Exit 2 means BLOCKED by missing/conflicting source. Exit 3 means REVIEW_REQUIRED: structural source checks found no listed mismatch, but this is **not** a security or release pass. It checks component presence, exactly one disabled/non-exported MemoryVault service without implicit intents, dormant service source contract, identical key alias across #17/#18/#19, and consent awaiting proof without selected side-effect APIs. It does not analyze merged manifests, dynamic registration, actual cryptography, same-UID callers, device signals or firmware.

On the authorized base, this audit is expected to report BLOCKED because #13–#19 have not been integrated. Do not force the base to pass by copying code from draft branches without review. tests/test_memory_vault_integration_audit.py covers synthetic positive-structure and negative-mutation cases, not Android or Pixel hardware.

## Independent acceptance sequence

1. **CI/QA and supervisor:** freeze candidate SHAs for #13–#19, inspect changed files, reconcile roadmap/Gradle/workflow overlaps, and compare the combined diff against the original branch. No concurrent writes to other PR heads.
2. **Android/security:** run source audit, compile combined Kotlin, execute exact-head JVM tests, Android instrumentation and merged-manifest checks. Keep service disabled/non-exported; review any new permission explicitly.
3. **Security/AI:** verify shared alias and canonical digest, caller identity including same-UID threats, per-use Keystore CryptoObject operation, cancellation/revocation/invalidation/process-death paths, and no PaperClip persistence or agent execution.
4. **UX/accessibility:** independently test trusted owner UI with spoken TalkBack, focus, large text, cancellation and explicit retention disclosure. No combined-feature UI evidence currently exists.
5. **Hardware/release:** physical Pixel 9 Pro (caiman) StrongBox/credential compatibility, rollback and signed reproducible release/OTA evidence are mandatory before enabling storage. No flashing authorized here.
6. **Independent verifier:** review actual evidence, report residual risks, approve/reject explicitly. Until then PENDING_INDEPENDENT_REVIEW, MemoryVault disabled, PaperClip RAM-only, M1–M8 not accepted.

## Boundaries

This PR adds only a Python source audit, synthetic Python regressions and this plan. No Android app code, permissions, production data, keys, services, devices, root access, release or main branch are changed. Source checks are not a substitute for Gradle, emulator, physical Pixel or independent security review.
