# OpenClaw legacy network-diagnostics safety boundary

**Status:** hardened legacy prototype; not integrated with the Android command router or device executor.

## Default-deny target scope

OpenClaw performs no network scan unless both conditions hold:

1. MRNOTHING_OPENCLAW_ALLOWED_TARGETS contains the exact target as a comma-separated IPv4 literal; and
2. the interactive operator types the exact one-time challenge SCAN <target> for that same address.

The allowlist accepts only exact IPv4 addresses in RFC1918 private, loopback, or link-local ranges. It rejects public/global addresses, hostnames, URLs, CIDRs, wildcard syntax, whitespace variants, malformed entries, and more than 32 entries. One malformed entry invalidates the entire allowlist. There is no default target.

Example configuration for a lab device that the operator owns or is expressly authorized to test:

    export MRNOTHING_OPENCLAW_ALLOWED_TARGETS="192.168.56.10,192.168.56.11"

Each scan still requires a fresh exact-target confirmation. Only scan systems you own or are expressly authorized to test. A private address or allowlist entry is not proof of ownership or authorization.

## Process execution

- All subprocess execution uses fixed executable names and argv arrays with shell=False.
- Only ping, nmap, curl, and termux-wifi-connectioninfo are accepted by the internal runner.
- Argument count, aggregate argument length, and command timeouts are bounded.
- Tool discovery uses shutil.which; it does not invoke which through a shell.
- Hostname/DNS probing was removed. Targets are literal IPv4 addresses, preventing target parsing from triggering name resolution.
- The manual port-check fallback uses a numeric IPv4 socket destination and is reached only after allowlist and interactive-confirmation checks.
- Wi-Fi information is read only when the operator explicitly enters the local wifi command.

## Verification and limitations

tests/test_openclaw_agent.py mocks subprocess and socket boundaries. The tests prove that denied, malformed, public, unallowlisted, or unconfirmed targets cause no network call; they do not perform a real scan. No network scan was run as part of this engineering change.

This remains a legacy Termux process. An environment allowlist and typed prompt are not strong owner authentication, a sandbox, a privilege boundary, or proof of target ownership. Any approved command still runs with the local Termux process privileges. Keep OpenClaw disconnected from the native Android command router until a separately reviewed typed API, platform authorization model, audit trail, and independent security review exist.
