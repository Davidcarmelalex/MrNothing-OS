# AGENT-004D — mTLS peer-to-session adapter

**Scope:** `feat/phase1-agentic-phone` only.  
**Status:** transport adapter and local synthetic mTLS tests implemented; no listener, endpoint, production enrollment service or command executor.

## Purpose

AGENT-004C accepts an `AuthenticatedOwnerSession` value from its caller. That dataclass is constructible by any Python caller and is not proof of authentication. AGENT-004D adds a narrow adapter that derives the session assertion from an already-handshaken server-side `ssl.SSLSocket` rather than accepting a caller-supplied authenticated flag or session object.

## Admission sequence

1. A separately managed server accepts a connection using `build_owner_consent_server_context`.
2. The context requires client certificates, TLS 1.2 or later, the owner-consent ALPN identifier and an explicitly supplied client-enrollment CA bundle. System default roots are not loaded.
3. The adapter accepts only an open server-side `SSLSocket` created with that exact context and a negotiated TLS 1.2/1.3 session.
4. The adapter requires the exact ALPN protocol and a peer leaf certificate.
5. It validates the leaf certificate's current validity, non-CA status, digital-signature key usage, client-auth EKU and P-256 public-key curve.
6. It computes the SHA-256 leaf-certificate fingerprint and resolves that exact fingerprint through a trusted transport-enrollment registry. Inactive, unknown, mismatched or unavailable registry records fail closed.
7. It creates a fresh random session identifier internally, caps the session at 30 seconds and the certificate expiry, and passes the session to the existing AGENT-004C issuer.
8. AGENT-004C independently checks the owner/device record and obtains the separate enrolled P-256 owner-consent verification key.

The transport-certificate registry is queried for every challenge issuance, so revocation blocks subsequent issuances. The existing consent challenge remains valid only for its bounded lifetime; the verifier does not yet perform an online revocation lookup at consumption time.

## Credential separation

The mTLS client certificate is a **transport identity**, not the per-use owner-consent signing key. The transport registry and consent registry must be populated by one trusted enrollment ceremony that binds both credentials to the same owner/device. This commit does not implement that enrollment ceremony, remote attestation, Android client-certificate provisioning or proof that either key is StrongBox-backed.

The Android AGENT-004B signer remains a separate per-use biometric/device-credential-gated P-256 operation. It is not wired to TLS, and this adapter does not weaken or replace that owner prompt.

## Implemented files

- `core/owner_consent_transport.py` — strict mTLS peer validation and internal session construction.
- `tests/test_owner_consent_transport.py` — local socket-pair mTLS tests with ephemeral software-generated CA, server and client certificates.
- `docs/AGENT-004D-MTLS-SESSION-ADAPTER.md` — this design and limitation record.

The test harness does not open a public port. It uses synthetic certificates and an in-memory registry. It is not a Pixel 9 Pro, Android Keystore, StrongBox, remote-attestation or production TLS test.

## Explicit non-goals and remaining blockers

- No network listener, HTTP/RPC endpoint, socket accept loop or firewall change.
- No production CA, server private key, trust bundle, certificate enrollment database or key-rotation service.
- No OCSP/CRL validation or verified-boot/Android-key-attestation verification. Leaf revocation is represented by the trusted enrollment registry's active flag; CA trust rotation remains an operational dependency.
- No rate limiter, durable security audit log, persistent session store or distributed revocation service.
- No device permission grant, screen capture, accessibility control, action execution or HERMES executor integration.
- No proof that transport and consent keys were bound by a real owner-approved enrollment ceremony.
- No physical Pixel 9 Pro validation or production release.

The adapter is a host-side library boundary. The server must call it only with accepted sockets from the configured server context and trusted registry implementations. The in-memory test registries are not production substitutes.

## Acceptance gates

1. The full Python preflight passes with the pinned CI cryptography dependency.
2. Exact-head Android Gradle/JUnit and repeat debug-APK checks pass.
3. Exact-head disposable emulator workflow remains green; this does not prove hardware TLS or StrongBox behavior.
4. Independent security review verifies TLS-context provenance, CA provisioning, certificate profile, fingerprint enrollment, owner/device binding, session lifetime and revocation semantics.
5. A later enrollment task binds the transport certificate and per-use consent key in a deliberate owner-approved ceremony.
6. Rate limiting, audit logging, CA rotation and verifier-time revocation checks are implemented before any production endpoint is considered.

Keep M3 partial and M6 in progress. No milestone is complete by this adapter or its synthetic tests. The upstream shared `SKILL.md` remains unverified.
