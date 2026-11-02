# AGENT-013 — Offline deterministic plan simulator

**Scope:** bounded, side-effect-free M3 engineering slice. This is NOT a deployed agent, device executor, remote command transport, or Pixel 9 Pro validation.

`core/agent_sandbox.py` validates a complete plan before simulating any step, limits plans to 20 uniquely identified commands, and allows only `get_battery` and `open_app` with exact argument schemas. Unknown, sensitive, malformed, unauthenticated or excessive plans fail closed. An injected monotonic clock and owner cancellation event permit deterministic deadline/cancellation tests. The simulated app catalog is supplied by the test; no Android APIs, real apps, shell, network or privileges are used.

Acceptance evidence: at least 20 independent sandbox scenarios in `tests/test_agent_sandbox.py`, all passing in CI. All `SandboxResult` records explicitly set `device_actions_executed=false` and `production_ready=false`. A successful simulated app-open means only `WOULD_OPEN_APP`, never that a real app was launched.

**Security boundary:** the boolean `transport_authenticated` is a test fixture, not an authentication implementation. Before any real executor is wired in, require signed admission from `core/command_admission.py`, Android Keystore enrollment, device binding, per-action owner consent, durable idempotency, revocation, explicit UI visibility, timeout enforcement and independent threat review. Do not expose this simulator as a network service.

**Next:** separately design and test authenticated, revocable device enrollment and a consent-bound execution state machine. M3 remains IN PROGRESS / acceptance unmet. QA-012 Android emulator CI passed at commit `2caa1b6e9d65159ad4c878b222610b71651e2bf2`; TalkBack spoken navigation remains unverified. No independent supervisor signoff.
