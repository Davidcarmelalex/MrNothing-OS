# Server engineering environment

Development checkout: `/opt/mrnothing/repo` on the existing VPS. This is **not** a production device-control endpoint. No inbound ports, daemon, privileged bridge, credentials or remote shell for an LLM have been enabled.

## Safe development commands
```bash
cd /opt/mrnothing/repo
git pull --ff-only
bash scripts/phase1-preflight.sh
```

## Hermes boundary
The Python HERMES adapter validates a narrowly defined command envelope. It does not authenticate callers, connect to phones, or execute actions. Future transport work must include mutual authentication, device-bound keys, replay prevention, explicit consent and tamper-evident audit logs. Never expose root commands as a general agent tool.

## Next infrastructure steps
- Isolated non-root build user and pinned toolchain.
- Signed build artifacts, provenance and SBOM.
- Android emulator integration tests and screenshot comparisons.
- Device pairing and authenticated encrypted message channel.
- Observability without storing sensitive screen content by default.
