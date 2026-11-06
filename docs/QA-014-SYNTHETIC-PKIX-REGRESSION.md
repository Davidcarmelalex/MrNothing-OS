# QA-014 — synthetic offline PKIX regression coverage

The Kotlin JUnit suite `OwnerAttestationChainGateTest` checks an actual
X.509 leaf signed by a synthetic test root, an omitted terminal root,
an untrusted root, a misplaced trusted root, duplicate certificates,
and absent trust anchors. Fixtures are public certificates only; test
private keys were generated ephemerally and discarded.

This is **not** Google Android attestation verification, verified boot,
revocation, root provisioning, physical Pixel testing, or owner binding.
Certificate fixtures expire in 2036 and must be rotated before then.
The JVM suite must pass in exact-commit hosted Android CI before acceptance.
Independent security review remains mandatory.
