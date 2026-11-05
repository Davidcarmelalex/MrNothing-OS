# CI-002 — Android debug build integrity gate

This task hardens the existing experimental Android CI without claiming a release.

- **Toolchain:** JDK 17, Gradle 8.9, AGP 8.7.3, Kotlin 2.0.21, compile SDK 35.
- **Gradle ZIP:** SHA-256 `d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab`, independently published at https://gradle.org/release-checks/ for Gradle 8.9 binary distribution. The workflow checks this pinned digest before extracting or running Gradle.
- **Source manifest:** fail-closed allowlist for the sole exported HOME activity; backup and cleartext traffic disabled; new permissions or components require explicit review. This is a source-only check; merged manifest inspection remains future work.
- **Artifact:** debug APK SHA-256 and source-commit metadata are generated and uploaded with the APK. Metadata is **not signed** and is **not a supply-chain attestation**.
- **Repeatability:** CI compares two APKs built with the same debug signing identity in one runner. This tests local byte identity, not cross-host reproducibility.
- **Scope:** no release signing keys, production deployment, device flashing, root changes, network control endpoint, or hardware claims.

## Acceptance evidence
1. Python unit tests and manifest gate pass on VPS.
2. GitHub CI Android unit tests, APK build and repeatability check pass.
3. Artifact contains APK plus deterministic provenance JSON.
4. Independent reviewer confirms SHA, workflow safety and scope. Until then, gate remains **PENDING_INDEPENDENT_REVIEW**.

## Residual risks
GitHub Actions currently use major-version action tags, not immutable commit SHAs; Android SDK components are version-selected but not independently checksum-pinned; Maven plugin/dependency checksums are not locked. The debug keystore is not suitable for production releases. These remain release blockers.


## Cross-run reproducibility finding — 2026-11-05

For SEC-019B commit `02ac61a00f2f49f4ca0c9ff779ad8fa5fbf14e7a`, push and PR GitHub Actions runs both built the same source revision and each produced byte-identical repeat debug APKs within its own runner. However, the APK hashes differed between runners:

- Push run 42004622475: `94cc1d20431c95689b4c4bd459d3f09c226472cdd01f1a9add14262e3d19a1f7`.
- PR run 42004630428: `5b9e3d16c3f6fd5bc005afca12e92c46e74bddead840ff535dc9aecd0b39b9ae`.

The app module has no explicit signing configuration, so the default per-run debug keystore is a plausible cause; this has not been experimentally isolated. The result does **not** prove source/build nondeterminism, but it does prove that cross-run APK byte identity has not been established. Do not claim cross-host reproducibility or release readiness.

Next: build a deterministic unsigned artifact or controlled non-production CI signing profile, compare normalized contents across independent runners, record all toolchain inputs, and generate an SBOM. Do not commit or create production signing keys.
