# QA-023B1B2D3 — Exact-head JVM security-test evidence

**Status:** Draft CI evidence improvement, stacked on PR #23 → #22 → #21 → authorized `feat/phase1-agentic-phone`. No merges, permissions, runtime authentication changes, device operations or release claims.

## Gap and bounded implementation

Prior Android CI ran `:app:testDebugUnitTest`, but the same shell step then executed `gradle clean` before collecting the per-case JUnit XML. A green Gradle task alone could not independently establish that the eight SEC-023B1B2D3 cancellation-fence methods and seven Cipher probe policy methods actually executed.

The new `scripts/qa023b1b2d3_unit_evidence.py` checks the Gradle XML **before clean**. It requires all fifteen named tests, rejects missing/duplicate required cases, missing/malformed reports, failures, errors, skips, contradictory aggregate counters and empty reports. The workflow archives the exact report XML and JSON summary with a seven-day retention period. It preserves strict Gradle dependency verification, repeat APK comparison and the existing negative control. The script does not accept success based on source declarations or a synthetic report during CI; it reads the Gradle-generated report directory.

Synthetic unit tests include positive controls and fail-closed negative controls. They are not proof of AndroidKeyStore operation, Android emulator execution, StrongBox provenance, a real owner credential, same-generation alias continuity, a physical Pixel 9 Pro, spoken TalkBack, or release readiness.

## Independent acceptance gates

1. Review workflow diff for placement **before** Gradle clean and absence of weakened build/security checks.
2. Run `python3 -m unittest tests.test_qa023b1b2d3_unit_evidence -v` and full Python preflight; record actual counts.
3. Require hosted exact-head Android Gradle/JUnit success, evidence JSON `result=pass`, and independently inspect the downloaded raw `TEST-*.xml` artifact.
4. Require independent security review before integrating any MemoryVault functionality. Alias replacement, authenticated Cipher interoperability, process death, owner-facing cancellation and physical Pixel hardware remain blocked.

The repository `PROJECT-ADAPTER.md` is a local adapter; the upstream shared `SKILL.md` was not found or verified. MemoryVault remains disabled and non-exported, PaperClip memory RAM-only, and Android executor disconnected. No M1–M8 milestone has independent completion approval.
