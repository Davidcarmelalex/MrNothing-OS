# SEC-019B — exact live TLS socket/session binding

**Status:** Implemented on `feat/phase1-agentic-phone`; exact-head CI is the acceptance source.  
**Scope:** Host-side library boundary only. No listener, public endpoint, executor, Android permission grant, device installation or production enrollment service.

## Problem

SEC-019A made enrollment validation and replay nonce insertion atomic in one SQLite transaction, but the verifier still accepted a caller-supplied `transport_authenticated` boolean plus certificate fingerprint and credential-generation snapshots. The challenge session identifier was not bound to the exact live TLS connection at verification time.

## Change

`OwnerConsentTlsAdapter` now owns both challenge issuance and verification for the exact server-side `ssl.SSLSocket` object.

- A random session identifier is generated inside the adapter and stored in a `WeakKeyDictionary` keyed by the exact socket object.
- The adapter records every issued challenge against that socket and requires exact challenge equality at verification.
- A different or resumed TLS connection has a different socket object and cannot reuse the old connection's challenges.
- Every verification rechecks socket liveness, the exact configured server context, TLS 1.2/1.3, the required ALPN, the peer certificate profile, current certificate enrollment, owner/device identity and credential generation.
- The current paired owner/device record supplies the P-256 public key. The atomic registry transaction rechecks the current key, fingerprint, generation and active status while consuming the nonce.
- Session and challenge deadlines are also tracked using monotonic time. Wall-clock rollback cannot revive an expired in-memory session or challenge.
- At most 64 outstanding challenges are retained per live socket. Expired entries are pruned only by monotonic deadline; capacity otherwise fails closed.
- The supported adapter verifier API accepts only `peer`, `envelope` and the adapter-issued `challenge`. No caller-supplied authentication boolean or identity snapshot is accepted.

The lower-level cryptographic helper is private and intended only for adapter use and focused unit tests. Production-facing host code must call `OwnerConsentTlsAdapter.verify_and_consume`.

## Tests

Synthetic local mTLS tests cover:

- same-socket admission and durable-registry replay rejection;
- challenge transfer to a second TLS socket;
- modified session ID and challenge not issued by the adapter;
- monotonic expiry despite wall-clock rollback;
- transport certificate revocation after issuance;
- credential-generation change after issuance;
- closed socket after challenge issuance;
- consent-registry outage during verification;
- the public adapter verifier signature, with no authentication boolean or caller-supplied snapshots.

The existing Python security suite, Android Gradle/JUnit build, repeat debug-APK comparison and disposable emulator workflow remain required exact-head CI gates.

## Limitations and remaining gates

- The adapter still does not accept sockets or expose a listener/RPC/HTTP endpoint.
- Session state is process-local and deliberately disappears on restart; old challenges fail closed.
- This does not establish TLS key custody, production CA provisioning, client certificate issuance, remote attestation, StrongBox-backed TLS identity or a real Android TLS client.
- It does not implement rate limiting, a production audit service, distributed revocation or safe replay compaction.
- It does not connect an executor, grant permissions, capture screens or perform device actions.
- A future executor must revalidate the live session and owner consent at its own execution boundary; this admission result remains `ADMITTED_NO_EXECUTION`.
- No physical Pixel 9 Pro test, firmware flash, production OTA or release signing is claimed.
- Independent security review remains **PENDING**.

No milestone is complete by this change. M3 remains partial and M6 remains in progress.



## Exact-head verification — 2026-11-05

Implementation commit: `02ac61a00f2f49f4ca0c9ff779ad8fa5fbf14e7a`.

- Push Phase 1 checks: [run 42004622475](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42004622475) — success.
- PR Phase 1 checks: [run 42004630428](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42004630428) — success.
- Both runs executed **358 Python tests**, all passed; Python compilation, launcher source accessibility/recovery gate and Android manifest security gate passed.
- Both Android jobs passed `:app:testDebugUnitTest` and `:app:assembleDebug`; a second debug build was byte-identical within each individual runner. Provenance was generated and the uploaded artifact is explicitly labelled not for release.
- Push-runner debug APK SHA-256: `94cc1d20431c95689b4c4bd459d3f09c226472cdd01f1a9add14262e3d19a1f7`.
- PR-runner debug APK SHA-256: `5b9e3d16c3f6fd5bc005afca12e92c46e74bddead840ff535dc9aecd0b39b9ae`.
- The two separate runners produced different debug APK hashes for the same source commit. Cross-run reproducibility is therefore **not established**. The default debug signing setup is a plausible source of variance, but the cause has not been isolated. Do not call the current debug artifact reproducible across hosts.
- Disposable x86_64 emulator: [QA-005 run 42004630445](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42004630445) — success. Emulator boot and QA-005 through QA-010 plus QA-013 passed. QA-011 reported `blocked_service_disabled` and is a preflight only. QA-012 passed structural semantics only; spoken TalkBack was not tested.
- QA evidence artifact: [not-for-release evidence](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42004630445/artifacts/13403942570).
- Debug APK artifact: [not-for-release APK and provenance](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/42004622475/artifacts/13404017202).

These results do not establish physical Pixel 9 Pro compatibility, spoken TalkBack acceptance, release signing, cross-host reproducibility or production readiness.
