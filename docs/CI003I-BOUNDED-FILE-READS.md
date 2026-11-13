# CI-003I: Race-resistant offline candidate file reads

This bounded change hardens the **offline syntax preflight** for a future OCI builder.
The candidate JSON policy and workflow YAML are opened exactly once with
`O_NOFOLLOW | O_NONBLOCK` on POSIX, checked using `fstat` on the opened
descriptor, read within 4 KiB / 64 KiB limits, and checked for concurrent
size/mtime/ctime changes. Symlinks, FIFOs, oversized inputs and a tested
symlink substitution immediately before opening fail closed.

This does **not** establish trusted filesystem snapshots, registry provenance,
OCI image authenticity, SBOM completeness, an approved builder image, or
reproducible Android binaries. An adversary with privileged access may still
modify the underlying inode or its metadata. The existing CI-003 host-only
workflow remains unchanged. No production controls or device permissions are
enabled. Independent review is required before adoption.
