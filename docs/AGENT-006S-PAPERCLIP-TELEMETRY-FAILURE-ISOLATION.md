# AGENT-006S — isolate optional PaperClip telemetry failures

## Scope and risk
PaperClip's content-free logger is noncritical telemetry. Prior code printed the
allowlisted event before entering its guarded file-I/O block and closed file
descriptors unconditionally in a finally block. A closed/broken stdout pipe or
an OSError during close could propagate and interrupt inference or teardown.
No prompt content was added to logging.

## Change
Catch OSError/ValueError from stdout printing, then attempt the existing
bounded owner-only log append. Close every opened descriptor exactly once;
suppress OSError during close, without retrying an ambiguous close. Preserve
all existing directory, symlink, hardlink, regular-file, allowlist, advisory
lock and 1 MiB append-limit controls. The log remains optional: failures may
drop events without changing model execution. No logging target is truncated,
deleted or migrated.

## Acceptance and residual risk
Four new offline regressions cover BrokenPipeError, closed stdout, cleanup
errors after a successful append, and cleanup errors during unsafe-target
refusal. Re-run focused/full Python tests, compilation, Android manifest and
launcher source gates; independently review the diff and exact-head CI.

An OSError from close may represent a flush or durability failure; a True
return only indicates the append loop completed, not durable persistence.
stdout output and log contents are not confidentiality boundaries against
same-user processes. No real llama-cli, Android executor, Pixel hardware,
signed build or production installation is enabled. Independent review pending.
