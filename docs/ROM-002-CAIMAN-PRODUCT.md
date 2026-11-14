# ROM-002 — Pixel product integration candidate

Status: engineering source integration only; no ROM compiled or device booted.
Parent: ROM-001 `77c2f97f816b9dee37bc02cc00f1b78ed624db93` (draft #89),
ultimately rooted in `feat/phase1-agentic-phone`.

## Actual implementation

`rom/aosp/caiman/` is an AOSP product directory intended to be staged at
`device/mrnothing/caiman` in an independently prepared AOSP tree. The new product
inherits `device/google/caimito/aosp_caiman.mk`, keeps hardware identity `caiman`,
registers `mrnothing_caiman-trunk_staging-userdebug`, and includes the existing
launcher APK through an ordinary non-privileged product app import. It does not
invent device drivers or replace Google's BoardConfig, radio, AVB or SELinux policy.

The module explicitly uses the public AOSP `testkey` certificate, not a platform
certificate and not a production identity. No key is generated or provisioned by
this patch. The product rejects `user`, `eng` and unspecified variants; only
engineering `userdebug` is supported. Never relock or distribute this candidate.
This variant has AOSP debug capabilities and is not a production security posture.

Upstream HOME/Quickstep packages are retained so recents and the recovery launcher
are not removed. First boot still uses upstream setup/default-role behavior;
this does not yet boot directly into MrNothing onboarding. Owner-driven HOME
selection remains necessary. No permissions, accessibility service, role grants,
transport, executor or bypass of the current command router is introduced.

## Upstream evidence and version boundary

The caiman product was fetched from Google's `android-15.0.0_r36` tag, resolving
to caimito commit `26a0f4faf91d0f14570832d74f7dbe73353246fb`. It specifies kernel
6.1, inherits zumapro/aosp_common and caimito/caiman_generic, sets device caiman,
and uses the caimito manifest. The product import is derived from those observed
paths, not a guessed `device/google/caiman` path. Soong's `app_import.go` at the
same Android tag was inspected for certificate/import semantics.

This old tag is a **reference for product structure**, not an approved security
baseline or a full resolved manifest. It must not be selected for a 2026 release
merely because its product source exists. A current compatible platform, kernel,
vendor and firmware set still needs ROM-001 R0 approval. Any selected branch must
be inspected for product/release-config compatibility, then fully commit-locked.

Sources:
- https://android.googlesource.com/device/google/caimito/+/26a0f4faf91d0f14570832d74f7dbe73353246fb/aosp_caiman.mk
- https://android.googlesource.com/platform/build/soong/+/refs/tags/android-15.0.0_r36/java/app_import.go
- https://source.android.com/docs/setup/create/new-device

## Build handoff (not executed)

1. Prepare and independently review the six real ROM-001 input groups. Pin all
   projects, toolchain and vendor/kernel/firmware artifacts. Pass the integrity
   preflight and separately approve compatibility, security and licensing.
2. Build the exact reviewed MrNothing source SHA using the pinned Gradle release
   recipe with strict dependency verification, unit tests, release manifest and
   packaged APK gates, SBOM/provenance and independent reproduction evidence.
   Keep the imported APK unsigned so Soong signs it with its engineering identity.
3. In a separate private AOSP engineering workspace, copy this directory to the
   previously absent `device/mrnothing/caiman`. Never overwrite an existing
   product directory. Place the verified APK at
   `prebuilts/app-release-unsigned.apk`; record its SHA-256, source SHA and
   provenance. Do not substitute a debug APK. Include the exact source's
   third-party notices in the staged NOTICE. Imported-APK digest verification
   is an operator handoff requirement, not implemented by these makefiles.
4. With all upstream inputs present, use AOSP's `source build/envsetup.sh`, then
   `lunch mrnothing_caiman-trunk_staging-userdebug`, then
   `m -j8 target-files-package otatools`. Confirm the release-config name on the
   chosen baseline rather than silently replacing it if unsupported. Capture
   the build logs and actual output paths; do not assume successful commands.
5. Inspect the generated target-files/partition metadata under ROM-001 R2 before
   packaging any factory/OTA artifact. Sign/release/flash acceptance is separate.

These instructions contain no physical-device commands. Building is blocked
today by unselected/unverified ROM inputs and insufficient verified host capacity.
No absent prebuilt is committed and no Soong/APK import build has been claimed.

## Infrastructure inspection — 15 November 2026

The connected `maverix-vps` was inspected read-only using Gateway SSH. It has
8 logical CPUs, 32,859,780 KiB RAM (about 31.3 GiB), no swap, and
307,791,736,832 available bytes on the filesystem containing `/opt` (about
286.7 GiB). This is below the published AOSP guidance of 64 GB RAM and 400 GB
free disk. Do not consume the shared server with a source sync or ROM build.

`/opt/mrnothing/repo` is clean but remains at
`0826ecea65edb0fe98cb82773a88c668a18effa5` on the phase1 branch, behind the
GitHub anchor. It has no `.repo/manifest.xml`, `build/envsetup.sh` or upstream
caiman product file. Running MrNothing services were observed; none was changed.
No mrnothing-named hourly systemd timer was returned; that does not rule out
another scheduler. Existing checkout and services remain untouched.

Evidence jobs: hardware `job_01M7E4EPGB0009RH3G1CEN7T3N`, storage
`job_01M7E4F3N300EVK529KYEG4669`, repository
`job_01M7E4HVVQ00B0VWYBB27Q9N5A`. They completed successfully; no host mutation.

## Verification and remaining work

The tests invoke GNU make with a disposable upstream fixture to execute product
inheritance, preserve upstream recovery packages, verify product registration,
reject disallowed variants and fail on missing upstream. They do not compile
Soong, build a kernel, run the packaged launcher, sign images or test a phone.
Windows skips these tests when GNU make is absent; Linux CI must execute them.
Independent non-author review remains pending.

Next software work: obtain sufficient isolated build capacity and matched source
inputs; enforce staged APK/source provenance, parse/build the real AOSP product,
then implement consented first-run integration and the real authenticated agent
execution path. Voice/model/communications and hardware gates remain separate.
