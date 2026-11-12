# AGENT-006Q — PaperClip event-log directory privacy

## Scope and finding

The existing AGENT-006P event logger already used directory-relative open with
O_NOFOLLOW, rejected symlink/hardlink/nonregular log targets, and applied 0600
to its regular log file. However, a pre-existing mrnothing/ or logs/ directory
could be group/other-writable. In that configuration another local account with
write access to the directory could interfere with log-file names and retention.
Pre-existing directories with 0755 also exposed filenames.

## Bounded change

agents/paperclip/agent.py now checks each opened HOME and logs directory
descriptor before creating/opening the next child. Both directories must be
owned by the effective user and must not be writable by group or others.
Otherwise logging returns False without creating/opening the log file.
Owner-owned directories that are merely readable/searchable by group/others
are tightened to 0700 using fchmod on the already-open directory descriptor.
Existing log-file checks (regular, one hardlink, owner UID, 0600) remain.

No new permissions, listeners, network calls, persistent conversation memory,
agent tools, Android executor or device controls were added. Only four
content-free events are eligible for logging.

## Regression and evidence

Three additional offline tests cover: tightening 0755 directories to 0700;
rejecting group-writable HOME without creating logs; and rejecting world-writable
logs without creating paperclip.log.

Local VPS verification against the source branch before publication:
- Focused PaperClip tests: 42/42 passed.
- Full Python unittest discovery: 938/938 passed.
- Python compileall for PaperClip and the new test file: passed.
- git diff --check: passed.
- Python 3.14 emits existing SQLite ResourceWarning messages in unrelated tests.
- GitHub Actions exact-head, Android emulator and independent review: pending at
  time of implementation, to be reconciled after publication.

## Residual limits and acceptance

The file-system owner and mode checks do not protect against a privileged
attacker, hostile same-UID processes, prior log disclosure, or an untrusted
filesystem/kernel. Directory ownership is checked against the process UID;
no Android-specific storage provider or hardware security claim is made.
An independent reviewer must inspect descriptor lifetime, mode transitions,
concurrent directory mutation and failure behavior before accepting this
security gate. No physical Pixel 9 Pro validation or signed release occurred.
