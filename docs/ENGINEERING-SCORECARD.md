# Engineering scorecard — evidence-based

**Audit date:** 2026-11-02. **Source of truth:** [engineering roadmap](ENGINEERING-FACTORY-ROADMAP.md) and current GitHub Actions results.

| Area | Verified evidence | Remaining gate |
| --- | --- | --- |
| Android launcher | Kotlin HOME activity, app catalog, device diagnostics; Android CI build green at baseline commit `f159e14` | Emulator/device install, TalkBack and lifecycle tests |
| Security policy | Python policy tests; HMAC/freshness/replay prototypes | Device-bound enrollment, key revocation, audit and independent review |
| Command admission | Durable SQLite replay ledger, strict validation and negative tests | Network authentication, device key storage and production integration |
| HERMES orchestration | Constrained adapter and local validation tests | Actual agent planner, executor, cancellation and task verification |
| Voice and SIM telephony | Design only | Real Pixel hardware and legal/consent validation |
| Pixel AOSP firmware | Design only | Build, compatible drivers, secure boot, OTA and rollback |
| Release | CI debug APK artifact available at baseline | Signed reproducible release, SBOM and recovery drill |

**Gate status:** M1 IN PROGRESS; M2 IN PROGRESS; M3 NOT STARTED; M4 NOT STARTED; M5 NOT STARTED; M6 IN PROGRESS; M7 BLOCKED ON HARDWARE; M8 BLOCKED. **No milestone complete or independently approved.**

Previous overall completion percentages were subjective planning estimates, not objective evidence. Do not use them as a release metric. Verify latest CI before reporting green status for a new commit.
