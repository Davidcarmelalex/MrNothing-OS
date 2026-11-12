#!/usr/bin/env python3
"""MrNothing OS legacy Web3 wallet: quarantined, watch-only metadata.

This module is NOT a signer or a usable wallet generator. It deliberately
refuses new key/address generation until a separately reviewed, hardware-backed
signer and recovery design exists. Existing legacy secret-bearing files are
preserved byte-for-byte and refused, never silently migrated or overwritten.
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

HOME = Path.home() / "mrnothing"
WALLET_DIR = HOME / "wallet"
LOG = HOME / "logs" / "wallet.log"
WALLET_FILE = WALLET_DIR / "wallets.json"


class WalletSecurityError(RuntimeError):
    """A wallet operation was refused to protect credentials or funds."""


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{ts}] [WALLET] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as handle:
        handle.write(line + "\n")


def _safe_store_path():
    """Reject common path redirection; no guarantee against hostile local races."""
    if HOME.is_symlink() or WALLET_DIR.is_symlink() or WALLET_FILE.is_symlink():
        raise WalletSecurityError("Wallet storage symlink refused; no files changed")
    if WALLET_FILE.exists() and not WALLET_FILE.is_file():
        raise WalletSecurityError("Wallet storage is not a regular file")


def _read_records():
    _safe_store_path()
    if not WALLET_FILE.exists():
        return {}
    try:
        with open(WALLET_FILE, encoding="utf-8") as handle:
            records = json.load(handle)
    except (OSError, ValueError) as exc:
        raise WalletSecurityError("Wallet storage unreadable; existing file preserved") from exc
    if not isinstance(records, dict):
        raise WalletSecurityError("Wallet storage has an invalid structure; file preserved")
    for record in records.values():
        if not isinstance(record, dict):
            raise WalletSecurityError("Wallet record is invalid; file preserved")
        # A legacy file containing private keys is never automatically migrated.
        if record.get("private_key") not in (None, ""):
            raise WalletSecurityError(
                "Legacy plaintext private keys detected; file preserved. "
                "Use a separately audited offline recovery procedure."
            )
    return records


class Wallet:
    """Watch-only address metadata; never stores a private key."""

    def __init__(self, name: str, chain: str, address: str, private_key: Optional[str] = None):
        if private_key not in (None, ""):
            raise WalletSecurityError("Private keys are not accepted by the legacy wallet")
        if not all(type(value) is str and value for value in (name, chain, address)):
            raise WalletSecurityError("Invalid watch-only wallet metadata")
        self.name = name
        self.chain = chain
        self.address = address
        self.private_key = None
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        if self.private_key not in (None, ""):
            raise WalletSecurityError("Refusing to serialize private-key material")
        return {
            "name": self.name,
            "chain": self.chain,
            "address": self.address,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        if not isinstance(data, dict) or data.get("private_key") not in (None, ""):
            raise WalletSecurityError("Secret-bearing or invalid wallet record refused")
        try:
            wallet = cls(data["name"], data["chain"], data["address"])
        except (KeyError, TypeError) as exc:
            raise WalletSecurityError("Invalid watch-only wallet record") from exc
        wallet.created_at = data.get("created_at", wallet.created_at)
        return wallet


class WalletManager:
    """Read-only balance metadata and safe watch-only record management."""

    SUPPORTED_CHAINS = ["ethereum", "bitcoin", "base", "arbitrum", "optimism"]

    def __init__(self):
        self.wallets: Dict[str, Wallet] = {}
        self._load()

    def _load(self):
        records = _read_records()
        self.wallets = {name: Wallet.from_dict(record) for name, record in records.items()}
        if records:
            log(f"Loaded {len(records)} watch-only records")

    def _save(self):
        # Inspect the on-disk file again before any replacement. Never overwrite
        # a legacy secret-bearing file, including after a concurrent file change.
        _read_records()
        data = {name: wallet.to_dict() for name, wallet in self.wallets.items()}
        WALLET_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        _safe_store_path()
        fd, temporary = tempfile.mkstemp(prefix=".wallets-", suffix=".tmp", dir=WALLET_DIR)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, WALLET_FILE)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def create_eth_wallet(self, name: str) -> Wallet:
        """Refuse unsafe legacy key generation and plaintext persistence."""
        raise WalletSecurityError(
            "Ethereum wallet creation disabled until audited hardware-backed signing is available"
        )

    def create_btc_wallet(self, name: str) -> Wallet:
        """Refuse the legacy fake bc1 address generator."""
        raise WalletSecurityError(
            "Bitcoin wallet creation disabled: the old random bc1 stub was not a valid wallet"
        )

    def list_wallets(self) -> Dict[str, Wallet]:
        return self.wallets.copy()

    def get_wallet(self, name: str) -> Optional[Wallet]:
        return self.wallets.get(name)

    def delete_wallet(self, name: str) -> bool:
        if name not in self.wallets:
            return False
        previous = self.wallets.pop(name)
        try:
            self._save()
        except Exception:
            self.wallets[name] = previous
            raise
        log(f"Removed watch-only record: {name}")
        return True

    def get_balance_stub(self, name: str) -> dict:
        """No RPC is connected; never misrepresent an unknown balance as zero."""
        wallet = self.wallets.get(name)
        if not wallet:
            return {"error": "Wallet not found"}
        return {
            "wallet": name,
            "address": wallet.address,
            "chain": wallet.chain,
            "balance": None,
            "balance_usd": None,
            "note": "Balance unknown; no authenticated blockchain RPC is connected",
        }


def main():
    print("\n[MrNothing Web3] Quarantined watch-only metadata viewer")
    print("Wallet creation and signing are disabled; do not deposit funds using legacy addresses.")
    try:
        manager = WalletManager()
    except WalletSecurityError as error:
        print(f"Wallet access blocked: {error}")
        return
    print("Commands: list, balance <name>, delete <name>, exit")
    while True:
        try:
            cmd = input("wallet> ").strip().split()
            if not cmd or cmd[0] == "exit":
                if cmd:
                    break
                continue
            if cmd[0] == "list":
                for name, wallet in manager.list_wallets().items():
                    print(f"  {name}: {wallet.address} ({wallet.chain})")
            elif cmd[0] == "balance" and len(cmd) == 2:
                for key, value in manager.get_balance_stub(cmd[1]).items():
                    print(f"  {key}: {value}")
            elif cmd[0] == "delete" and len(cmd) == 2:
                print("Removed" if manager.delete_wallet(cmd[1]) else "Not found")
            elif cmd[0] in ("create-eth", "create-btc"):
                print("Wallet generation is disabled pending audited signer and recovery.")
            else:
                print("Unknown command")
        except WalletSecurityError as error:
            print(f"Operation blocked: {error}")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
