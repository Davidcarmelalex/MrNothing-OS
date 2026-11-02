# SEC-014I — exact StrongBox and device-credential readiness gate

Scope: feat/phase1-agentic-phone. The previous read-only Keystore check
accepted any hardware-backed key, including TEE keys. That was insufficient
for the StrongBox-only enrollment policy introduced in SEC-014H.

The read-only gate now requires **Android 12/API 31+**, where
KeyInfo.securityLevel can distinguish StrongBox from TEE. Only
KeyProperties.SECURITY_LEVEL_STRONGBOX is accepted; unknown, software,
TEE and unavailable signals fail closed. A key must also permit Android
device-credential authentication, require owner authentication per use,
be P-256 EC and exist under the fixed alias. Enrollment itself is also
blocked below API 31. The launcher still supports its existing minSdk;
only optional owner-key enrollment requires Android 12+.

Evidence: Kotlin pure policy tests for TEE and biometric-only rejection,
Python source gates for exact Android platform checks, Python suite,
Android manifest/source checks and GitHub Android/JUnit CI.

This is **local policy verification**, not key attestation. No actual
StrongBox device, emulator key generation, credential prompt, remote
owner binding, signed commands, screen execution, revocation or OTA
has been validated by these source tests. Existing aliases are not
replaced or deleted; independent security review remains pending.

Reference: https://developer.android.com/reference/android/security/keystore/KeyInfo#getSecurityLevel()
