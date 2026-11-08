# AGENT-014 — legacy HERMES shell-task approval boundary

**Status:** bounded hardening of the legacy Termux helper; not a native Android executor.  
**Branch:** \`feat/phase1-agentic-phone\`  
**Baseline:** \`92680812645c3d8f549e049bb7d75b80ed702ec6\`

## Finding

\`agents/hermes/agent.py\` previously accepted free-form command strings and called \`subprocess.run(..., shell=True)\`. The background scheduler could execute due shell tasks without a fresh interactive owner decision. This behavior did not establish a supervised execution boundary and was not suitable for a future Android bridge.

## Change

- Shell tasks now require an explicit confirmation callback; the normal scheduler never supplies one.
- Interactive mode displays the exact command and requires the user to type \`RUN <10-hex SHA-256 prefix>\`. This short digest binds the confirmation to the displayed text; it is **not** an authentication token.
- Commands are parsed with \`shlex.split\` and launched as an argument vector using \`shell=False\`; shell interpreters and control characters are rejected.
- Direct command execution has a 30-second timeout.
- The background scheduler leaves due shell tasks pending, marks \`approval_required\`, and sends one approval-required notification. It continues to process explicit notification tasks.
- Regression tests cover default denial, decline, non-boolean approval, exact-command confirmation, shell-interpreter rejection, malformed/oversized input, timeout and unattended scheduler behavior.

## Security limits

This is not a sandbox, strong owner authentication, privilege boundary, process-tree containment mechanism or production executor. A user-approved executable still runs with the Termux process's OS privileges and inherited environment. The local task JSON has no signature or tamper-evident storage. Do not use this helper for root, irreversible device operations, remote commands, production deployment or physical flashing. Do not connect it to the native Android command router. The future product path must use typed, reviewed tools with independent authorization and OS-level permission checks.

## Acceptance

- Python regression tests and the repository Phase 1 CI must pass at the exact commit.
- Static review must confirm this file contains no \`shell=True\` invocation and that the scheduler cannot invoke shell tasks.
- This task does not satisfy the independent review of SEC-021A/B/C or SEC-022, and does not authorize executor integration.
