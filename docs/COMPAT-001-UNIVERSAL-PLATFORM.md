# COMPAT-001: shared platform, individually qualified devices

Proposed product architecture, 15 November 2026. Scope: isolated feature branch
rooted at `feat/phase1-agentic-phone`, baseline
`f42af837bcb8eed478cadbc472b7571441449a7a`. No device is qualified by this proposal.
This requirement expands the adapter's original Pixel-only product scope; it
does not change its security, review or release gates.

## Three editions

| Edition | Delivery and authority | Compatibility boundary |
| --- | --- | --- |
| AOSP ROM | Device-specific Android-derived OS image; reviewed privileged services only | Exact model, region/carrier variant, firmware and partition baseline; never a generic smartphone image |
| Mobile Linux | Native Linux distribution and services on individually supported hardware | Independent Linux kernel, display, telephony, power and driver evidence; Android support does not imply Linux support |
| Android app/launcher | Opt-in HOME app on the existing supported Android installation | Ordinary app permissions; no root, firmware replacement or assumed system authority |

Pixel 9 Pro (`caiman`) remains the first ROM reference target, currently research
only. Do not add unverified phones to a supported-device list. A locked carrier
variant may remain eligible only for the app edition after app qualification.
The app edition remains a distinct product, not evidence of a bootable ROM.

## Shared core and adapter contracts

The logical shared core owns typed plan/action/result schemas, deterministic
policy, model routing, consent binding, durable replay/cancellation, encrypted
memory lifecycle, content-minimized audit and emergency stop. This is a design
boundary, not a claim that existing Python and Kotlin implementations are already
one portable runtime. Reuse shared canonical fixtures and protocol tests first;
do not replace reviewed authorization code in a bulk refactor.

OS adapters implement capability discovery, owner authentication/key storage,
app launch, screen capture, accessibility, notifications, voice and persistence.
Android app adapters use framework APIs and explicit grants; AOSP adapters may
use narrowly scoped Binder services only after permission/SELinux review; Linux
adapters need reviewed service identities, sandboxing, key storage and compositor
permission integration. No adapter may supply an agent-controlled authorization
callback, silently downgrade StrongBox requirements, or treat a manifest as consent.
Unavailable authority disables the affected feature. Existing executor remains
disconnected until the existing independent security gates pass.

Device adapters provide kernel/HAL/driver/firmware bindings and manifests. Keep
product policy out of device trees and hardware assumptions out of the core.
Every runtime action requires a fresh capability and permission check in addition
to signed consent, live identity/revocation, replay prevention and cancellation.
A static capability record is neither runtime attestation nor authorization.

## Support tiers

| Tier | Meaning and promotion evidence |
| --- | --- |
| Research | Inventory or feasibility only; no installation/support claim |
| Candidate | All mandatory records present; reproducible build, licensing and lab plan ready for independent review; still unsupported |
| Experimental | Independently reviewed lab evidence for exact edition/device/build; published limitations, recovery and security status; no daily-driver guarantee |
| Supported | Independent release acceptance, physical acceptance, update/recovery drills, named maintainer and security-update commitment for exact variant |
| Retired | Support revoked or expired; publish last validated version and migration path; no new release eligibility |

The checker accepts research/candidate records only. Experimental/supported
promotion requires a separate signed review process not implemented here. Failed,
unknown or stale mandatory evidence blocks promotion. No aggregate score can
compensate for a failed safety gate. OS release readiness and M1–M8 acceptance
remain separate from the per-device tier.

## Initial engineering hardware policy

ARM64, 4 GiB RAM and 64 GiB total storage are proposed initial qualification
minimums; 8 GiB/128 GiB recommended. These are project performance targets, not
measured sufficiency or installation compatibility. Measure available storage,
memory pressure, battery and thermal behavior under representative workloads
before acceptance. Android app builds currently declare API 29 minimum/API 35
target; owner credential functionality requiring API 30 must remain unavailable
on API 29. Hardware-backed key requirements apply per sensitive feature; no
software-key fallback is authorized. Accelerated graphics and working Wi-Fi are
required for the intended full experience. Cellular service requires separately
verified modem/IMS. Offline large-model execution has model-specific RAM/storage
and accelerator requirements; cloud-assisted operation does not waive privacy
or explicit network consent. Linux has no Android API level and needs its own
maintained kernel/userspace baseline.

## Mandatory capability and evidence gates

| Manifest gate | Required qualification evidence |
| --- | --- |
| bootloader | Exact SKU/carrier unlock eligibility, partition map and documented recoverability; inspection only in this task |
| kernel | Pinned source/config, ABI/KMI and security maintenance; Linux requires native upstream/device-port evidence |
| vendor_blobs | Exact compatible versions, hashes, origin and redistribution rights; no rights inferred from availability |
| modem_ims | SIM/eSIM, calls/SMS/data, VoLTE/VoWiFi, regional/carrier IMS and emergency-call limitations; AI two-way SIM audio is a separate physical test |
| gpu | Driver/API, compositor acceleration, suspend/resume, rendering correctness and thermal tests |
| camera | HAL/driver, sensors, permissions, image/video correctness and privacy indicators |
| selinux | ROM enforcing policy, no permissive release domains; Linux may mark N/A only with reviewed alternate mandatory access control evidence |
| avb | ROM verified boot chain, rollback indices and key ownership/relock feasibility; Linux may mark N/A only with reviewed alternative verified-boot design |
| ota | Authenticated update, rollback protection, interrupted-update and rollback recovery drill; Linux needs native update evidence |
| accessibility | Spoken screen-reader navigation, large text, contrast, keyboard/switch navigation, consent and stop/recovery usability |
| recovery | Exact factory restore route, backup/restore, boot-loop/power-loss handling and owner-visible recovery documentation |
| secure_keys | Hardware security level, owner authentication, revocation and rollback behavior; absent capability disables protected features |

For the app edition, bootloader/kernel/vendor_blobs/SELinux/AVB/OTA/recovery may
be N/A because firmware is host-managed. Its update/uninstall and stock-launcher
recovery still require app acceptance testing. App modem/GPU/camera evidence is
framework-level behavior on the existing OS, not independent firmware support.
All N/A records require a reason; no ROM gate is waivable. Wi-Fi/Bluetooth,
sensors, charging, audio, suspend, battery and thermal tests are additional
physical acceptance requirements beyond this initial record schema.

Manifest identity is exact device + variant + edition + baseline, not model name
alone. `baseline` must identify the proposed OS/kernel/vendor/firmware combination;
the initial caiman baseline explicitly records it as unresolved. Evidence references
are repository-relative `evidence/` paths. A future evidence index must bind files
to exact source/artifact SHA, device variant, lab identity/date, procedure/results,
limitations and independent reviewer. The initial checker validates references
only: it does not open them, verify signatures/licenses, assess freshness, inspect
devices or prove truth. `review_ready=true` means record completeness only.
It always returns hardware_verified/release_authorized/flash_authorized=false.

## Ordered roadmap and validation

1. COMPAT-001: agree boundaries and fail-closed records; add offline regression
   cases without modifying Android permissions, command routing or workflows.
2. Reconcile ROM-001 PR #89's six-input inventory with a mutually compatible,
   license-reviewed caiman AOSP/device/kernel/vendor/firmware baseline. Do not
   copy its unfinished input gate or claim its branch is integrated here.
3. Add evidence-index integrity/freshness and exact variant binding, then
   portable core protocol conformance tests across Android and Linux adapters.
4. Establish isolated reproducible unsigned ROM builds and static security
   checks. Build success does not imply bootability or device support.
5. Plan independent, separately authorized physical qualification, recovery,
   telephony, power, accessibility and threat review. This run performs none.
6. Qualify additional device families individually. Investigate mobile Linux
   only after documented native port support; app qualification can proceed
   independently for devices unsuitable for firmware replacement.

Offline validation: run `python -m unittest discover -s tests -p
'test_device_manifest_gate.py' -v`, then `python scripts/device_manifest_gate.py
devices/caiman.aosp_rom.json`. Expected initial CLI result: valid record,
12 blocked gates, exit 1. Invalid records exit 2. Synthetic complete candidate
records may exit 0 but never authorize release or flashing.

## Factory coordination and audit limits

The complete 402-entry baseline tree contains PROJECT-ADAPTER.md and no SKILL.md
or AGENTS.md. Upstream shared factory package remains unverified. Latest relevant
open PRs #84–#89 were inspected: integration/UX evidence repair, runner drift
diagnostics, builder staging and ROM inputs remain separate draft stacks.
PR #89 head `77c2f97f816b9dee37bc02cc00f1b78ed624db93` has successful Phase 1
run 43633812668; this is prior APK/policy evidence, not ROM evidence or CI for
this change. CI-003 runner drift and independent security review remain blockers.
The Phase 1 PR workflow discovers Python tests automatically; no workflow change
is needed. Local clone transport failed; connector reads are pinned to baseline.

No local hourly automation configuration was found. Scheduler state/prompt and
remote worker locks are therefore unverified and unchanged. Handoff for the next
hourly run: read this document and its PR, re-read anchor/head SHAs and open PRs,
avoid duplicating COMPAT-001 or ROM-001, preserve existing stacks, select only the
next unblocked bounded task, and never promote support based on this checker.
This repository handoff is not confirmation that a scheduler consumed it.

## M1–M8 acceptance

M1 foundation and M2 interface IN PROGRESS; M3 agentic intelligence PARTIAL;
M4 device integrations NOT ACCEPTED; M5 reference-device compatibility NOT
ACCEPTED; M6 security/privacy IN PROGRESS; M7 hardware BLOCKED; M8 production
BLOCKED. Independently accepted: 0/8. Preserve the original roadmap evidence
requirements; additionally require per-edition/per-device acceptance before
claiming broader support. No flash, unlock, root, production signing, merge or
deployment is part of this proposal. Author tests/repetition cannot substitute
for independent non-author review; keep the PR draft pending that review and CI.

The seed manifest's hardware numbers are proposed qualification floors and its
API 35 value is a proposed build target, not observed Pixel specifications or a
verified firmware baseline. No runtime hardware inventory was collected.
