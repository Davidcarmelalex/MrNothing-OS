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
