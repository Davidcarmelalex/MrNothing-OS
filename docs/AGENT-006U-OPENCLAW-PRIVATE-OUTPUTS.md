# AGENT-006U — Private, no-follow OpenClaw diagnostic outputs

**Scope:** Legacy Termux OpenClaw prototype only; based on
`feat/phase1-agentic-phone` at `f42af837bcb8eed478cadbc472b7571441449a7a`.
This is not a native Android permission grant or connected device executor.

## Threat and bounded correction

Previously `scan_network` created report directories by pathname and wrote a
predictable `.json` filename with `open(..., "w")`. An existing symlink could
therefore redirect or truncate a file within the agent user's privileges.
`log` also appended to a pathname without symlink or ownership checks.

Both outputs now traverse absolute path components through no-follow directory
descriptors. Unsafe owners, writable ancestors, symlink components and relative
paths fail closed; a root-owned sticky intermediate such as `/tmp` is allowed.
Report files use exclusive no-follow creation and owner-only `0600` permissions;
logs use no-follow append and refuse non-private files or multiple hardlinks.
A failed report-directory preflight blocks probes before network activity. A
report-write failure *after* owner-approved probes is labeled `FAILED`, never
falsely labeled as a denied scan.

This does not authorize a scan: the exact-target allowlist and fresh interactive
confirmation remain mandatory. No networking is added. Existing unsafe log files
are not silently migrated, truncated or permission-modified; an owner must review
and repair them separately. A same-IP, same-second report collision fails closed
rather than overwriting an existing report.

## Evidence and acceptance boundary

- `python3 -m unittest -q tests.test_openclaw_agent`: 24/24 passed.
- `PYTHONWARNINGS=ignore::ResourceWarning python3 -m unittest discover -s tests -p 'test_*.py' -q`: 945/945 passed.
- `python3 -m compileall -q core agents tests scripts`: passed.
- `python3 scripts/android_manifest_gate.py android/app/src/main/AndroidManifest.xml`: passed.
- `python3 scripts/launcher_accessibility_gate.py`: passed (source-only).
- `git diff --check`: passed.

All OpenClaw subprocess and socket boundaries were mocked in the focused tests.
No network scan, external request, Android installation, container build, Pixel
hardware test, root escalation, OTA, signing or deployment occurred.

**Required before acceptance:** exact-head hosted CI, independent non-author
security review (including Termux filesystem compatibility), and PR-stack
reconciliation. No M1–M8 milestone is independently accepted. The repository
has a project-specific `PROJECT-ADAPTER.md`; the upstream shared `SKILL.md`
package remains absent/unverified and was not installed.
