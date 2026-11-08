# AGENT-006J — consent-gated legacy network diagnostics

**Date:** 2026-11-09  
**Branch:** feat/phase1-agentic-phone  
**Audited parent:** 3554fefab1a1745bfc485b8becdef3562a7c40c1  
**Scope:** modules/network/network.py, offline regression tests, threat model and engineering evidence.

## Finding

The legacy network module previously sent traffic without an owner confirmation:
- public-IP lookup invoked curl against a third-party service;
- ping accepted arbitrary hostnames/addresses and caller-selected counts;
- speedtest-cli selected external servers automatically and could download/upload data;
- connectivity monitoring repeatedly pinged a fixed public address without per-probe consent;
- local-IP discovery used a UDP socket connect to a fixed external address to select a route.

The module was a standalone Termux CLI, not a registered Android capability, but its functions could still be called by a local process.

## Implemented boundary

### Private IPv4 ping
- A bounded environment allowlist, MRNOTHING_NETWORK_ALLOWED_TARGETS, accepts at most 32 exact private/local IPv4 literals and at most 1,024 characters. One malformed entry denies the entire allowlist.
- Hostnames, URLs, public IPv4 addresses, IPv6, shell syntax, whitespace variants and option-like input are rejected before confirmation or network activity.
- Every ping requires an internal exact challenge bound to the canonical target and count, for example ALLOW PING 192.168.56.10 COUNT-1.
- The confirmation is read inside the module; callers cannot inject a callback that returns approval.
- Count is an exact integer from 1 through 3. The executable is resolved to a direct, non-symlink regular executable; argv is fixed, shell=False, and the process timeout is 10 seconds.
- A thread-safe but process-local limiter enforces a 10-second per-target cooldown, at most 3 probes per target per rolling 60 seconds, and at most 6 probes globally per rolling 60 seconds.

### Public-IP lookup
- Only the fixed HTTPS host api.ipify.org is contacted, and only after a fresh exact typed confirmation.
- The request uses TLS certificate validation, disables ambient proxies and redirects, has a 6-second timeout and reads at most 46 bytes before validating the returned IP literal.
- The user is explicitly told that the provider receives the request and can observe the source IP.

### Monitoring, speed tests and local interface lookup
- Monitoring requires an allowlisted private IPv4 target, duration 1–300 seconds, interval 30–60 seconds, no more than 10 probes, and a fresh confirmation for each individual ping. EOF/cancellation stops the sequence; it is not an unattended background task.
- Provider-selected speed tests are disabled because the selected servers and upload/download destinations cannot be bound to one exact target consent.
- Local IPv4 discovery uses a local interface ioctl; it does not open a connection or send a packet.

## Tests and evidence boundaries

The new tests mock subprocess, input, HTTP and interface ioctl boundaries. They cover target parsing/allowlisting, malformed allowlists, exact confirmation, noninteractive denial, bounded counts/timeouts, fixed argv, rate limits, fixed-host HTTPS/no-proxy/no-redirect behavior, response-size validation, disabled speed tests, per-probe monitoring consent and packet-free local interface lookup.

No network probe, public-IP lookup, speed test, DNS lookup, HTTP request, real target scan, Termux installation, Android installation or physical-device operation is performed by the tests.

## Residual risks

- The allowlist is configuration, not proof of target ownership; a malicious same-user process can alter its own environment.
- Typed CLI confirmation is not Android system-credential authentication or a cryptographic owner identity.
- Rate limiting is process-local and resets on process restart; it is not a shared or durable abuse-control service.
- The ping binary and Termux environment remain within the same user's trust boundary.
- The fixed public-IP provider receives a request and observes the source IP; consent must be fresh for every lookup.
- The module remains disconnected from the native Android tool registry and is not an Android permission provider or sandbox.

The network row in AGENT-006H's legacy inventory is superseded by this implementation as of this commit. Voice capture/transcript retention and PaperClip plaintext memory remain separate open workstreams.

## Acceptance gate

The code author cannot approve the security design. Independent review must challenge allowlist tampering, process-local rate-limit resets, fixed provider disclosure, proxy/redirect behavior and same-user Termux trust. Exact-head Phase 1, CI-003 and QA-005 results must be recorded before this slice is considered CI-verified.

All M1–M8 milestone states remain unchanged; no milestone is COMPLETE. The native Android executor remains disconnected.
