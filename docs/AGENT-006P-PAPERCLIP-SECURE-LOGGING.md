# AGENT-006P — PaperClip owner-only event log boundary

**Scope:** legacy Termux PaperClip module only; no native Android executor, permission, model, network or device integration.

## Finding

The previous `log()` accepted arbitrary caller text and opened `~/mrnothing/logs/paperclip.log` by pathname with append mode. A symlinked log path could redirect writes, and default umask could leave log events group/world readable. Although current call sites redacted prompts, the unrestricted interface allowed future accidental disclosure.

## Mitigation

- Only four fixed, content-free event strings are accepted; arbitrary messages, exception details, prompts and model paths are refused before terminal output or file writes.
- Open the user-home parent, `mrnothing` and `logs` via directory descriptors with `O_DIRECTORY|O_NOFOLLOW`; create missing child directories with mode 0700.
- Open `paperclip.log` relative to the verified directory descriptor with `O_NOFOLLOW|O_NONBLOCK|O_APPEND`, reject non-regular files, hardlinks and files not owned by the current user; enforce 0600 on the accepted file.
- Treat logging failure as nonfatal and avoid writing any sensitive content as a fallback.
- Offline regression tests cover private creation, unknown-event denial, symlinked home/log/file, hardlink, FIFO and existing permissive file mode.

## Limits and gate

Existing directory modes are not recursively repaired; an already permissive home/logs directory may reveal filenames, so a future explicit migration/audit is needed. A hostile same-UID process, parent-directory replacement and OS-level memory/terminal capture are outside this boundary. This does not establish hardware/Termux acceptance or encrypted memory. Independent security review remains required. The upstream shared `SKILL.md` is unverified; `PROJECT-ADAPTER.md` is the local project-specific adapter. M1/M2/M6 remain in progress, M3 partial, M4 not started, M5 not accepted, M7/M8 blocked. No milestone complete.
