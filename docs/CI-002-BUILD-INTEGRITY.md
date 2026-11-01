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
