# CI-003F — Digest-pinned Android builder adoption preflight

Status (2026-11-13): OFFLINE CANDIDATE VALIDATION ONLY. No pinned image selected, built, published, deployed, or accepted.

## Motivation and observed evidence

CI-003 uses two GitHub-hosted Ubuntu 24.04 builders. In PR #65, two archived independent-runner failures showed byte-identical unsigned APKs but differing runner-image versions and OS-package inventories. PR #67 added bounded fail-closed drift diagnostics; PR #68 added strict validation of self-reported runner identity. The exact-head PR #68 Phase 1 and CI-003 workflows passed on 13 November 2026 (runs 43474706966 and 43474707022). A passing pair does not resolve the host-image drift in issue #66.

## Deliverable and limits

scripts/ci003_pinned_builder.py validates a FUTURE candidate policy with exactly these fields:

    {"schema_version":1,"platform":"linux/amd64","image":"registry.example.org/namespace/builder@sha256:<64 lowercase hex>"}

It checks that the proposed CI-003 build job declares the exact same literal image under container.image. Mutable tags, expressions, ambiguous or missing container declarations, wrong architecture, changed digest, symlinked policy and duplicate JSON keys are rejected. The existing CI-003 workflow has NO build container and is deliberately rejected. No candidate lockfile is committed, because no independently verified image digest exists.

The only positive result is PIN_SYNTAX_VALID_NOT_ATTESTED. A matching digest string does not prove registry resolution, image integrity, trustworthy provenance, image signatures, complete SBOM, installed Android SDK, or reproducible builds. This is not a general YAML parser or a release gate.

Example for an isolated future candidate checkout (not current CI):

    python3 scripts/ci003_pinned_builder.py --candidate-policy candidate.json --workflow proposed-ci003.yml

## Required acceptance sequence

1. Select an independently verified OCI image digest for linux/amd64 and document registry provenance, license, security scan, SBOM, supply-chain trust and owner.
2. Freeze OS packages using a reproducible snapshot; pin JDK 17.0.21+9, Python 3.11, Gradle 8.9 and its existing checksum, Android SDK 35/build-tools 35.0.0 and Android/Kotlin plugins.
3. Build and inspect the image in isolation, resolve its actual registry digest, independently review and sign/attest it using protected infrastructure. Do not invent a digest or store credentials in Git.
4. In a disposable PR, run two independently provisioned builds inside the SAME digest-pinned image. Preserve external runner metadata as evidence. Do not silently discard host drift.
5. Obtain explicit non-author security/release approval for any distinction between pinned controlled inputs and outer GitHub host drift. Existing full-host equality remains fail-closed until approval.
6. Verify raw JUnit results, unsigned APK byte equality, both SBOMs, provenance, negative controls, deterministic repeats, and security policy. Production signing/OTA and Pixel hardware require separate M7/M8 gates.

## Safety

No current CI workflow, Android runtime, permissions, keys, MemoryVault, executor, device, root, firmware, or protected branch was modified by this preflight. CI-003 issue #66 remains open. Independent review pending. M1–M8 independently accepted: 0/8. Local PROJECT-ADAPTER.md is present; upstream shared SKILL.md remains absent and unverified.


## CI-003G scoped YAML binding hardening (2026-11-14)

The candidate-only preflight now requires exactly one literal top-level `jobs:`
mapping, exactly one literal `jobs.build:` job, one `container:` mapping
inside that job and exactly one literal `image:` child. It rejects duplicate
or quoted shadow keys, image overrides, unsupported container mapping fields,
YAML merge keys at job/container scope, and ambiguous tab indentation. Sibling jobs remain supported.

This closes a candidate-preflight false-positive in which a `build:` key
outside `jobs:` or a second `image:` entry could be mistaken for the
actual GitHub Actions build container. The parser deliberately recognizes a
strict YAML subset; it does **not** establish general YAML equivalence or
prove GitHub Actions runtime interpretation. A real pinned image, signed
provenance, SBOM, dual-builder evidence and independent approval remain
separate mandatory gates. No workflow was activated or security policy relaxed.

## CI-003H — OCI reference grammar hardening (2026-11-14)

The candidate-only validator now rejects malformed registry DNS labels, invalid
registry ports (including zero, leading-zero ambiguity and values above 65535),
empty or dot-only repository components, and leading/trailing repository
separators. It retains valid explicit registry ports and Docker-style component
separators. The tests include adversarial negative controls and positive
compatibility cases. This is strictly offline syntax validation, not registry
resolution, image-signature verification, SBOM inspection, image selection or
builder adoption. The active CI-003 workflow remains unchanged and unpinned.

The upstream shared `SKILL.md` is still absent and unverified; the local
`PROJECT-ADAPTER.md` remains the project-specific engineering contract.
Independent security/release acceptance and hardware testing remain pending.
