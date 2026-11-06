# SEC-014M — Offline attestation chain preflight (not an authorization gate)

The standalone `OwnerAttestationChainGate` rejects absent anchors, empty paths,
duplicate certificates, oversized paths, and PKIX-invalid paths. No trust anchors
are bundled or silently downloaded. An independently authenticated root
provisioning process remains required.

**Limitations:** This helper is not wired into enrollment or command execution.
PKIX validation alone does not establish Android verified boot, key ownership,
attestation freshness, root rotation, certificate revocation, or device identity.
Revocation is explicitly disabled for offline preflight and MUST be separately
implemented before any trusted owner binding or agent execution. No consent or
command signing is enabled by this change.
