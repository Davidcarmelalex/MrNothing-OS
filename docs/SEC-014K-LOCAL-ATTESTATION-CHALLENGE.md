# SEC-014K — local attestation challenge prerequisite (development only)

Scope: `feat/phase1-agentic-phone`. An explicit owner-initiated StrongBox
enrollment now generates a fresh 32-byte SecureRandom challenge and supplies it
to Android KeyGenParameterSpec.setAttestationChallenge. After key generation,
the enrollment flow requires a local X.509 Android KeyDescription extension
whose challenge matches and whose attestation/keymaster security levels both
indicate StrongBox. Missing, truncated, oversized, malformed or TEE-only
extensions block the local success report. No existing alias is replaced.

**Trust boundary:** The extension parser checks local data structure and
challenge equality, not certificate authenticity. A locally matching
certificate extension does NOT establish a Google-trusted attestation chain,
verified boot, Pixel identity, a specific remote owner, revocation status,
owner consent or permission to run commands. This feature deliberately cannot
sign commands, grant consent, enable accessibility or screen capture, or
contact a network endpoint. Failed postgeneration checks may leave an inert
alias; automatic deletion is intentionally prohibited.

Acceptance: Kotlin synthetic DER policy tests, Python source gates, Android
debug build/unit CI, manifest gate, and review of no new Android permissions.
These are not physical StrongBox tests or independent security signoff.

Next: verify a certificate chain against independently pinned, current Google
Android attestation roots, parse verified boot and authorization tags, bind
an authenticated owner identity and trusted challenge context, and design
explicit key rotation/revocation. Physical Pixel 9 Pro evidence and independent
security review are required before enabling any agent integration.
