# SEC-023B1B2B-C — Disposable composite build candidate (not release acceptance)

**Base:** `feat/phase1-agentic-phone` at `f42af837bcb8eed478cadbc472b7571441449a7a`.
**Scope:** separate draft branch based exclusively on the authorized feature branch. No merge to `main` or any other PR head. All source imported from the following frozen published draft PR heads:

| PR | Frozen SHA | Contribution |
|---|---|---|
| #13 | `2a76b0c7d71b7d614775cdebabf3633633bac875` | Memory threat model |
| #14 | `074c93a6da2c669be9312393bc1df0f514982b33` | Python canonical envelope and tests |
| #15 | `a062de4e41b60fff142541bdfb5d994815cb5d92` | JVM admission and tests |
| #16 | `bcabf0fafd59d5f5c89050fccb6fb17c56dcd834` | Disabled service, manifest/CI/instrumentation gates |
| #17 | `aa16e334fac61112d1c1e9da1b3fa9c7c5760f41` | Read-only Android Keystore inspection |
| #18 | `d31275db50a9f0513d36433e79bb314c5983dd36` | Dormant provisioning policy and instrumentation |
| #19 | `4ce03b1a4bcf3ebade218b5e86ca3489fb44a5a1` | One-shot consent-intent binding |
| #20 | `1dc4f2f4f84508c4c8f890c7ce00d7cc86429e14` | Fail-closed structural integration preflight |

## Explicit conflict resolution

1. Imported each unique new source/test/spec file verbatim from its frozen PR head; did not merge unrelated branch history.
2. Applied #16's changes to AndroidManifest, phase1-checks, QA-005, manifest gate and accessibility test. Preserved its fail-closed XML instrumentation evidence validator.
3. Both #16 and #18 extend `android/app/build.gradle.kts`'s instrumentation class list. Combined the two additions, yielding **seven** exact configured classes, with both `MemoryVaultManifestBoundaryTest` and `MemoryVaultKeySpecContractTest`. Updated the corresponding class-inventory Python test from six to seven.
4. #17's branch-local test assumed PR #16's service was absent. Replaced that outdated absence assertion with an XML assertion that the combined service is **disabled, non-exported and has no intent filter**, and that no Keystore preflight call is wired to the service, launcher or owner signer.
5. Omitted all eight PR-local edits to `docs/ENGINEERING-FACTORY-ROADMAP.md` because each was based on the same initial roadmap and would overwrite other workers' entries. Appended this single reconciliation entry instead. The original PR-specific acceptance documents are preserved as separate files.

## Evidence and explicit non-evidence

The candidate is **dormant**: no key generation, CryptoObject operation, IPC, encrypted storage, PaperClip persistence, consent Activity integration, privileged operation, permission expansion or device installation was added. The source-only integration audit can at most return `REVIEW_REQUIRED` (exit 3); it **cannot approve** the composite. The composite source tests also require a disabled/non-exported service, no new permission and no launcher/PaperClip wiring.

The separate PRs' successful CI runs are **not** evidence that the composite compiles. A new exact-head Android Gradle/JUnit CI run and QA-005 emulator instrumentation are required after publishing this candidate. The local VPS lacks an Android SDK and Gradle executable; no local Android build or emulator is claimed. Independent security review, actual owner CryptoObject proof, key invalidation, same-UID/cross-UID abuse tests, spoken TalkBack, physical Pixel 9 Pro StrongBox/credential validation, reproducible signed OTA and recovery remain **PENDING**. No milestone M1–M8 is independently complete.

**Provenance:** `PROJECT-ADAPTER.md` is a local project-specific adapter. No upstream shared `SKILL.md` or authorized shared package was verified or installed. The feature branch and all eight PR heads remain unchanged.
