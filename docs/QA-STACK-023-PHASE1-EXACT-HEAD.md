# QA-STACK-023 — Phase 1 exact-head source provenance

## Evidence-triggered defect
The successful Phase 1 run 43119999642 for draft PR #52 reported a
provenance.json source commit of
3aba047a46c96b5cfc9eba688a1f8ddd0193fba1 (GitHub synthetic PR
merge), not PR #52's head
734ac424d824dfddbe37500abbc6ec3f7884ebb3.
The APK SHA-256 was verified against the downloaded artifact, but this
run **cannot** be labeled exact-head verification of the PR commit.

## Scoped fix
For both Python and Android Phase 1 jobs, checkout the pull-request head
SHA (or push SHA for push events) explicitly and assert that the checked-out
Git HEAD equals the event-derived expected SHA before any build or test.
Keep checkout credentials disabled, job permissions read-only, and the
existing pinned actions and dependency-verification controls unchanged.

## Acceptance and limits
- Static tests assert both jobs pin and verify exact head; full Python,
  manifest and accessibility source gates must pass.
- Fresh hosted Phase 1 jobs at this exact new commit must pass and the
  published provenance source commit must equal the new PR head.
- Synthetic PR merge compatibility remains a separate integration concern;
  this gate deliberately tests the exact head instead.
- No claim of emulator, Pixel hardware, TalkBack, StrongBox, signed release,
  OTA/recovery or independent human security approval.
- Upstream shared SKILL.md remains unverified. No M1–M8 acceptance.
