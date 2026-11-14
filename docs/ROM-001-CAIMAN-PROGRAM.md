# MrNothing OS Pixel 9 Pro engineering program — ROM-001

Audit: 15 November 2026 (Asia/Kolkata). Target: Pixel 9 Pro `caiman` only.
Status: **ROM NOT BUILT; NOT FLASHABLE; NOT SHIPPED.**

## Evidence baseline and scope

Development anchor: `feat/phase1-agentic-phone` at
`f42af837bcb8eed478cadbc472b7571441449a7a`; main:
`f3c9a701d2a337de8ef393ac14df044a79843d60`.
This change is isolated on `feat/rom001-caiman-readiness-20261115`.
It neither integrates nor accepts the existing security/UX stacks.

The complete recursive anchor tree contains an Android Gradle application,
Python agents/policy, source gates and APK/emulator CI. It has no AOSP Repo
manifest, Soong product configuration, BoardConfig, Pixel device/kernel/vendor
tree, firmware lock, partition layout or ROM image build workflow. The newest
CI-003 staging branch was also inspected for these paths; its Android manifests
are application manifests, not AOSP source manifests. No external AOSP workspace
or suitable ROM builder was verified. `docs/SERVER-ENGINEERING.md` describes
`/opt/mrnothing/repo` on a VPS, but that document is not a current host inspection.

`android/app/build.gradle.kts` builds `tech.mrnothing.os`, SDK 35, version
`0.1.0-dev`, with intentionally unsigned release output. The manifest declares
HOME eligibility and USE_BIOMETRIC; it does not install a new operating system.
`CommandRouter.kt` rejects all actions with VERIFIED_TRANSPORT_SESSION_REQUIRED.
The Python gateway recognizes get_battery/open_app envelopes but is not a phone
executor. Launcher selection, consent scaffolding and offline rehearsal are not
proof of working integrated autonomous device control.

GitHub release v1.0.0 contains small legacy module archives, not Pixel boot,
target-files, factory or OTA images. Its release label is not ROM evidence.

## PR stacks and CI snapshot

The open-PR API returned 80 draft PRs. Capture their exact current refs before
any reconciliation; PR descriptions sometimes name an older SHA than their head.
Relevant chains:

- #1: phase1 umbrella to main; must remain unmerged without approval.
- #12–#33: MemoryVault/consent work; #34–#64: admission/UX integration work
  (numbers are ranges with gaps, not assertions that every number is a PR).
- #65 → #67 → #68 → #69 → #70–#79 → #82 → #88: CI-003 builder hardening chain.
- #67 → #84 (review-only reconciliation with #64) → #85 → #86 → #87:
  emulator/UX and strict two-builder verification candidate.
- #80 → #81 and #83: separate legacy output hardening branches.

Latest inspected hosted evidence:

| Candidate head | Run | Verified result and boundary |
| --- | --- | --- |
| `f6ecb3a806bef412cb004134d3085f181eda937b` (#88) | [43627227221](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/43627227221) | Phase 1 success; APK/Python CI, not ROM |
| `25ffc1fa6017a3c13b4102bb6bdd958a68d97815` (#87) | [43606187959](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/43606187959) | Phase 1 success |
| same #87 head | [43606187949](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/43606187949) | Both builders succeeded; verifier failed at unsigned APK/SBOM/toolchain equivalence step |
| `0dc70715d077f21687612e7e73efbaa43dd6e543` (#85) | [43590877569](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/43590877569) | QA-005 emulator workflow success; not physical Pixel evidence |

[Issue #66](https://github.com/Davidcarmelalex/MrNothing-OS/issues/66)
documents host-image/package drift on earlier strict reproduction runs. The
latest #87 verifier log was also read: APK bytes, normalized contents, runtime
SBOM and toolchain matched; the full environment comparison failed on image_version
and 32 component-only-A / 28 component-only-B records. Do not weaken this gate.
An APK byte match alone is neither full environment reproducibility nor ROM
reproducibility. Independent non-author review remains pending.

## Build inputs and licensing blockers

Select a mutually compatible platform release, Pixel device tree, kernel,
vendor image, bootloader and radio firmware as one reviewed baseline. SDK 35
does not choose that baseline. Never use a moving branch as the release lock.
Record the resolved Repo manifests (every project pinned to a commit), upstream
URLs, local overlays, patch series, binary checksums and documented compatibility.

Google currently lists caiman in the `android-gs-caimito-6.1-android16` kernel
family; this is a discovery lead, not a selected or validated platform/kernel
combination. Driver binaries are published by Google for specific builds. Their
availability does not establish redistribution rights or complete HAL/IMS/eSIM
functionality. An Android 17 moving platform branch cannot be assumed compatible
with those inputs.

No root project LICENSE was found; GitHub repository metadata reports no license.
The existing third-party notices cover Bouncy Castle only. Before distribution,
the owner must settle the project license and reviewers must inventory source,
kernel modifications, prebuilts, firmware, fonts, models and assets. Preserve
upstream notices and applicable corresponding-source obligations. Obtain a
documented decision on proprietary vendor/radio/IMS/eSIM redistribution. Do not
invent permission to bundle Google Play services or proprietary Pixel apps.
No license or contractual approval is provided by this technical preflight.

Provision a separate non-root Linux x86-64 AOSP builder with pinned toolchain,
adequate storage/RAM, build logs, artifact retention and a second independent
builder. Official guidance currently calls for at least 400 GB disk and 64 GB
RAM. This Windows audit workspace and the existing short-lived APK jobs are not
verified ROM infrastructure. No infrastructure purchase or host changes occurred.

## Executable sequence and acceptance gates

Execute in order. Each gate needs exact source SHA, immutable input inventory,
commands/tool versions, logs, artifact SHA-256 and independent reviewer decision.
New software branches start from an agreed immutable parent; no automatic merges.

| Gate / accountable role | Work and deliverables | Acceptance evidence |
| --- | --- | --- |
| R0 — platform/release | Choose compatible baseline; resolve manifests, source license and proprietary-input review; inventory private staging | All six input groups present and hash-verified; reviewers approve compatibility and legal findings; no placeholders |
| R1 — build engineer | Create product/Soong overlay and default HOME integration without silently granting agent permissions; pinned Linux build recipe; build target-files and dist | Clean build logs and target-files zip; partition map and build fingerprint; artifact digests; no claims of hardware boot |
| R2 — platform/hardware | Derive image set from actual target-files/BoardConfig and boot-chain metadata | Inspect boot/init_boot/vendor_boot, dtbo and vbmeta chain as applicable; super or explicit logical partition images plus metadata. Mark omissions with target-derived reasons. Verify boot headers, fstab, dynamic groups, slot layout, AVB descriptors/rollback indices and matching firmware; reject wrong-device artifacts |
| R3 — supervised device operator | First boot on explicitly approved sacrificial caiman; preserve recovery route | Boot logs show init → zygote → system_server → SystemUI → MrNothing onboarding, repeated cold boots, encryption/unlock; SELinux enforcing with reviewed denials; no permissive policy or disable-verification acceptance |
| R4 — compatibility/hardware QA | CTS/VTS/CTS Verifier plan appropriate to chosen Android level; HAL and app matrix | arm64 app install/update, Wi-Fi, BT, NFC, GNSS, USB, sensors, thermals, suspend/battery; all camera lenses/modes/video; microphone/speakers; biometric, TEE/StrongBox keys and attestation behavior measured on ROM |
| R5 — telephony specialist | Per-carrier voice/SMS/data/IMS/eSIM matrix | Physical SIM and eSIM activation/reboot, VoLTE/VoWiFi and handover, incoming/outgoing calls, SMS, data, emergency-call behavior through authorized carrier/lab test procedures; modem crashes and recovery reviewed. No public emergency calls for testing; no claim of SIM audio capture from dialer/root status |
| R6 — agent/security/UX | Integrate verified transport, narrowly scoped tools, model runtime, voice and MemoryVault after security-stack reconciliation | End-to-end user request → visible plan → per-action argument-bound consent → least-privilege execution → audit/revocation; replay, expired/changed consent, lock, cancel, process death and prompt injection all deny safely. No blanket accessibility grants; emergency stop. Default launcher onboarding, offline/errors, recovery Settings, spoken TalkBack, large text, focus and privacy checks pass |
| R7 — release/security | Verified Boot policy, protected signing design, recovery and A/B OTA | Approval required before production keys. Test-key-only laboratory evidence first: signed target-files/factory/OTA, verified payloads, correct AVB trust chain and rollback counters; successful and interrupted OTA, failed-slot fallback, recovery/sideload. No relock until custom-root support and complete signed partition chain are proven |
| R8 — release/independent verifier | Reproduce, reset, restore and accept release | Two clean independent ROM builds compare unsigned image contents/metadata under declared deterministic policy; SBOM/provenance covers all inputs. Factory reset removes accounts/consent/vault keys; no action before new onboarding. Approved restore-to-known-good image tested within anti-rollback constraints; signed release evidence and independent sign-off |

Do not require a standalone recovery.img or monolithic super.img without checking
the actual product. Modern recovery may be incorporated in boot-family images;
OTA can carry logical partition payloads. ROM-001 intentionally supplies no
flash commands and no guessed partition files. R0–R8 remain NOT ACCEPTED.

## First implemented software gate

`scripts/rom_input_preflight.py` accepts a local JSON inventory and a private,
quiescent staging directory. It hashes six nonempty local input bundles plus
their separate review records; rejects missing kinds, duplicate JSON keys,
wrong devices, unsafe paths, symlinks, tampering and invented approval fields.
It never downloads, extracts, executes, signs, changes permissions or accesses a
device. Its result means only that supplied bytes match the supplied inventory;
it does not validate resolved-manifest contents, reviewer identity, compatibility,
license sufficiency or build/boot readiness. Concurrent same-user staging mutation
is outside its threat model. Treat staging as private and immutable during checks.

Run from repository root:

```text
python -m unittest discover -s tests -p test_rom_input_preflight.py -v
python scripts/rom_input_preflight.py rom/caiman-inputs.pending.json --staging-root .
```

The second command MUST return exit 1 today: no real inputs exist. To prepare a
candidate, copy the pending inventory outside the repository and add exactly one
entry for each `platform_manifest`, `device_manifest`, `kernel_manifest`,
`vendor`, `firmware`, `toolchain`. Each entry has `kind`, relative `path`, lowercase
64-character `sha256`, separate `review_path` and `review_sha256`. Bundle multi-file
inputs first; record provenance, compatibility and licensing findings in the
review record. Synthetic passing fixtures never count as real input evidence.
Exit 0 still always reports release_ready=false and flash_authorized=false.
Existing Phase 1 unittest discovery picks up the new tests without workflow edits.

## Automation coordination and authorization

No matching desktop automation definition exists in the local automation folder
(only the jitter salt was present), so the existing hourly scheduler's prompt,
host and active checkout could not be verified here. Repository PR timestamps
indicate other workers; they are not a scheduler lock. This run uses a fresh
clone and unique branch, touches only new ROM-001 paths, and leaves existing PRs,
anchor, workflows and VPS checkout untouched. Do not edit/rebase their branches.
Before a shared integration build, identify the scheduler owner/host, reserve a
branch/path lease with start/end and immutable parent, and recheck refs. Do not
disable or create duplicate automation. This run does not claim scheduler control.

No device approval is needed to continue software-only input/recipe work.
Needed artifacts: exact caiman model/region/carrier variant, current build ID and
bootloader/baseband versions, OEM-unlock availability, proposed matched upstream
source/binary URLs/checksums, proprietary terms and confirmed build host capacity.
Do not publish serials, IMEI, EID, SIM identifiers, keys or personal logs.

Before device work, obtain explicit approval for the exact device and each scoped
read/install/unlock/flash/wipe/relock/reset/restore operation, with backup and
known-good stock recovery artifacts plus anti-rollback review. Approval for audit
or APK testing does not authorize firmware operations. Separately obtain approval
for production key custody/provisioning, merging main and deployment. None was
performed or authorized by this plan.

## Primary references checked during audit

- [AOSP build prerequisites](https://source.android.com/docs/setup/start/requirements)
- [Pixel kernel families](https://source.android.com/docs/setup/build/building-pixel-kernels)
- [Google device driver binaries](https://developers.google.com/android/drivers)
- [AOSP build IDs](https://source.android.com/docs/setup/reference/build-numbers)

Read these as upstream references, not permission to execute their device commands.
