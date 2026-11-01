# Engineering scorecard — Phase 1

**Overall estimated maturity: 12% of final target (subjective engineering estimate, not test coverage).**

| Area | Estimate | Evidence |
| --- | ---: | --- |
| Architecture and product definition | 55% | Phase 1 plan and hardware handoff |
| Android launcher and app shell | 25% | Kotlin HOME role, app catalog and device dashboard |
| Authorization and policy | 25% | Python/Kotlin policies; Python CI tests passed |
| Remote authenticated command transport | 0% | No pairing, credential storage or live transport |
| Agent reasoning and tool execution | 5% | Limited local command router; no autonomous planner |
| Multilingual voice interface | 0% | Not implemented |
| Native SIM telephony and bidirectional audio | 0% | Not implemented; requires physical-device research |
| Custom Pixel 9 Pro firmware / root | 0% | Not implemented |
| One-click provisioning and rollback | 0% | Not implemented |
| End-to-end QA, reliability and release | 5% | CI authored, Android build not yet verified |

Estimates are approximate and not an arithmetic mean. Do not represent scaffolded code as production-ready. Android CI must pass before claiming an APK exists. Pixel hardware is necessary for modem and firmware validation.

## Definition of done
- Signed installable launcher with accessible UI and safe recovery.
- Authenticated owner pairing, encrypted transport and replay prevention.
- Permissioned agent task planning, human confirmation and auditable results.
- Voice commands, verified supported app workflows, and reliable error recovery.
- SIM call answering/placing and independently proven bidirectional speech path.
- Pixel-specific firmware verified with telephony, verified boot, OTA and rollback.
- Device provisioning with backups and explicit unlock/flash confirmations.
- Threat model, privacy review, tests and repeatable release artifacts.
