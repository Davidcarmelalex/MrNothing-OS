# AGENT-006I — Quarantine unsafe legacy Web3 wallet generation

**Branch:** `feat/phase1-agentic-phone`
**Audited parent:** `09319ee5dee644e52cd5648e144f790cb5c9cdc0`
**Scope:** `modules/web3-wallet/wallet.py` and mocked offline regression tests.

## Finding
The legacy Ethereum creator wrote raw private keys into plaintext `wallets.json`. Its ImportError fallback fabricated unrelated random address/key strings; they were not a cryptographic wallet. The Bitcoin stub generated a random `bc1` prefix without valid Bech32 encoding, key derivation or recovery. The balance stub reported zero without an RPC. These could mislead users into depositing real funds or exposing credentials.

## Safe bounded change
- **Disable** both Ethereum and Bitcoin wallet generation until a separately audited hardware-backed signer, chain-specific derivation and recovery flow exists. No new keys, addresses or funds are generated.
- Reject loading an existing record containing nonempty `private_key`; **do not delete, rewrite, export, migrate or log** that file. An owner-led, independently audited offline recovery procedure is required.
- Keep watch-only metadata viewing and deletion, but serialize no private-key field. Before replacing a watch-only file, recheck its contents; use a temporary mode-0600 file and atomic replacement. Reject symlinked storage paths. This is a single-process prototype, not a defense against malicious same-user races.
- Refuse malformed legacy storage without rewriting it. Restore in-memory records if a deletion save fails.
- Represent unavailable balances as `null`/unknown rather than fabricated zero.
- Preserve the Android native executor's disconnected state. No wallet operation is registered as an agent capability.

## Acceptance tests
`tests/test_legacy_wallet_quarantine.py` covers refusal to create keys/fake addresses, refusal to serialize keys, byte-preserving rejection of legacy secrets, pre-save recheck, null-key watch-only migration, mode-0600 writes, symlink rejection, rollback of failed deletion, unknown balance, and malformed-file preservation.

Tests use temporary synthetic files only. No actual wallet, keys, funds, RPC, signing, blockchain broadcast or physical device was used.

## Release and review blockers
This change does **not** provide a safe wallet, key recovery, secure erase, hardware signing, blockchain RPC or production migration. Existing secret-bearing `wallets.json` files may still be present on user devices and must be treated as exposed if their storage was insecure. Do not automatically delete or migrate them. Require independent security review, threat analysis, chain-specific test vectors, StrongBox/Keystore design, explicit owner consent and physical Pixel validation before enabling any wallet creation or transaction execution. No M1–M8 milestone is complete.
