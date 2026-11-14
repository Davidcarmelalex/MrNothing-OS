# CI-003J — Project-owned OCI toolchain candidate (NOT ACCEPTED)

This is an **unapproved, unbuilt, partial** Android toolchain image recipe. It
does not install Android SDK platform 35 or build-tools 35.0.0 and is not
suitable for CI-003 adoption, signing, OTA or device use.

The two base images are pinned to **linux/amd64 platform manifest digests**
resolved from Docker Hub via read-only `docker buildx imagetools inspect` on
2026-11-14. Digest resolution is not a security audit, signature verification,
SBOM review or long-term upstream availability guarantee.

The Android command-line tools archive was downloaded read-only from
`https://dl.google.com/android/repository/commandlinetools-linux-16111833_latest.zip`
on 2026-11-14; its complete 181,052,239-byte archive was SHA-256 hashed and
zip-integrity tested. Gradle 8.9 SHA-256 matches the repository's existing
`scripts/download_gradle_distribution.sh` pinned value; its archive was not
downloaded during this candidate preparation.

## Inputs and build constraints

Supply both verified archives in `builder/inputs/` (never commit those files).
Run `python3 scripts/ci003_builder_inputs.py --directory builder/inputs`
before any experimental build. The Dockerfile copies **local** archives only,
uses digest-pinned bases, does not install apt packages, and runs the resulting
image as UID 10001. It deliberately contains no signing keys, secrets, license
acceptance automation, root escalation at runtime or production workflow changes.

A Dockerfile-specific deny-by-default build-context ignore file excludes the rest of the repository from the Docker build context. The recipe has **not been built or run**. It remains incomplete pending:
independent image signature/SBOM/provenance checks, build-and-run tests, JDK
and Python runtime verification, Android SDK 35 and build-tools 35.0.0
offline package hash inventory, AAPT2 native library compatibility, package
license approval, two independent build comparisons, external host-drift
evidence, and independent non-author security/release signoff.

The current CI-003 host-only workflow remains untouched and fail-closed.
Issue #66 remains open. Upstream shared SKILL.md is absent/unverified.

## CI-003M offline ZIP metadata preflight

The candidate input verifier now rejects malformed ZIP archives, unsafe or
ambiguous member paths, duplicate members, symlinks and other special files,
file/directory collisions, encrypted members, excessive member counts and
expanded-size or compression-ratio anomalies. It checks archive metadata only
after the locked SHA-256 check; it does not extract files or execute code.

This is a **local preflight**, not a proof of safe decompression or a signed
supply-chain attestation. The Dockerfile's own extractor and the provenance of
all archives still require independent review. Android SDK platform 35 and
build-tools 35.0.0 remain absent, so no complete builder or reproducible APK
is claimed.
