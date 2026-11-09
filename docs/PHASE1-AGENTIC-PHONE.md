# MrNothing OS — Phase 1 Agentic Phone

Status: Engineering kickoff; implementation and physical-device validation pending.

## Mission
A dedicated Android phone receives authenticated instructions by Telegram, WhatsApp (approved integration), and cellular voice; operates supported apps through visible UI interaction; places and receives cellular calls; and reports verified outcomes to its owner.

## Architecture
1. Native Kotlin Android app: foreground service, AccessibilityService with explicit user enablement, UIAutomator instrumentation, MediaProjection with user consent, notification listener where permitted, Android Telecom/InCallService for eligible default-dialer behavior.
2. Python HERMES orchestrator: typed task state machine, policy decisions, tool registry, memory, audit log, idempotency keys and retries.
3. Voice gateway: streaming STT/LLM/TTS, interruption handling, language detection, transparent AI identification and consent controls.
4. Cellular audio research spike: test real inbound and outbound two-way audio on target Android model and OS version. Default dialer role and root DO NOT guarantee uplink/downlink capture or injection. Evaluate OEM privileged integration and lawful carrier/SIP bridging if unavailable.
5. Remote channels: Telegram Bot API with allowlisted chat IDs; WhatsApp Business Platform where eligible; mutual TLS or WireGuard for device-to-server transport.
6. Observability: live task timeline, screenshots with redaction, traces, failure classification, owner callbacks and kill switch.

## Non-negotiable safeguards
- Owner authentication and device enrollment; no unauthenticated voice instructions.
- Outbound calling only to approved contacts unless explicitly authorized.
- Disclose AI identity to call participants; respect recording and privacy consent.
- Require human approval for money transfers, purchases, deletion, security changes, and unfamiliar recipients.
- Never attempt to defeat CAPTCHA, banking protections, biometrics, or platform restrictions.
- Encrypt credentials, redact sensitive screen contents, limit retention and provide remote revoke.
- Explicit opt-in for accessibility and screen capture; foreground status indication and immediate stop control.

## First vertical slice
1. Pair device with owner via short-lived enrollment token.
2. Receive authenticated Telegram command: 'Open Settings and report battery level.'
3. Produce task plan; approve allowed tools.
4. Launch Settings, inspect accessibility tree, optionally capture permitted screenshot.
5. Extract battery level, verify, log evidence and reply.
6. Test failed permissions, offline state, timeouts and cancellation.

## Telephony acceptance test
1. On real SIM and selected hardware, dial allowlisted test contact.
2. Prove bidirectional AI speech over the cellular call without speakerphone hacks.
3. Answer inbound allowlisted call and identify as AI.
4. Interrupt, resume, end call and produce transcript only with consent.
5. Initiate callback to owner with task report.
Mark each test BLOCKED until physically validated.

## Milestones
M0: repository audit, device choice, security threat model, baseline CI.
M1: Kotlin app + permissioned device bridge + first Telegram-to-UI task.
M2: robust UI planner and verification across five ordinary apps.
M3: inbound/outbound cellular audio feasibility and prototype.
M4: multilingual calls, owner callback, WhatsApp channel, end-to-end tests.
M5: reliability, accessibility, battery, privacy and recovery hardening.

## Definition of done
No 'fully agentic' label until the same device passes 100 scripted scenarios with measured completion rates, explicit failure reporting and no unauthorized actions. Track latency, tokens, power, thermal state and cost. No guarantee of every app; maintain per-app capability matrix.
