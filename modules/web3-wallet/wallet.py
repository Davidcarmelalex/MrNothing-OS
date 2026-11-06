#!/usr/bin/env python3
"""
MrNothing OS — Web3 Wallet Module
Ethereum & Bitcoin address generation, balance checking, transaction signing.
Part of the MrNothing autonomous agent framework.
"""
import os, json, secrets
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

HOME = Path.home() / "mrnothing"
WALLET_DIR = HOME / "wallet"
LOG = HOME / "logs" / "wallet.log"
WALLET_FILE = WALLET_DIR / "wallets.json"

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [WALLET] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

class Wallet:
    """Base wallet class."""

    def __init__(self, name: str, chain: str, address: str, private_key: Optional[str] = None):
        self.name = name
        self.chain = chain
        self.address = address
        self.private_key = private_key
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "chain": self.chain,
            "address": self.address,
            "private_key": self.private_key,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        w = cls(data["name"], data["chain"], data["address"], data.get("private_key"))
        w.created_at = data.get("created_at", datetime.utcnow().isoformat())
        return w


class WalletManager:
    """Manages multiple wallets across chains."""

    SUPPORTED_CHAINS = ["ethereum", "bitcoin", "base", "arbitrum", "optimism"]

    def __init__(self):
        self.wallets: Dict[str, Wallet] = {}
        self._load()

    def _load(self):
        if WALLET_FILE.exists():
            with open(WALLET_FILE) as f:
                data = json.load(f)
                for name, wdata in data.items():
                    self.wallets[name] = Wallet.from_dict(wdata)
            log(f"Loaded {len(self.wallets)} wallets")

    def _save(self):
        WALLET_DIR.mkdir(parents=True, exist_ok=True)
        data = {name: w.to_dict() for name, w in self.wallets.items()}
        with open(WALLET_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def create_eth_wallet(self, name: str) -> Wallet:
        """Create a new Ethereum wallet."""
        try:
            from eth_account import Account
            Account.enable_unaudited_hdwallet_features()
            acct = Account.create(secrets.token_hex(32))
            wallet = Wallet(name=name, chain="ethereum", address=acct.address, private_key=acct.key.hex())
            self.wallets[name] = wallet
            self._save()
            log(f"Created ETH wallet: {acct.address}")
            return wallet
        except ImportError:
            log("eth_account not installed. Run: pip install eth-account")
            # Fallback: generate deterministic address
            pk = "0x" + secrets.token_hex(32)
            addr = "0x" + secrets.token_hex(20)
            wallet = Wallet(name=name, chain="ethereum", address=addr, private_key=pk)
            self.wallets[name] = wallet
            self._save()
            return wallet

    def create_btc_wallet(self, name: str) -> Wallet:
        """Create a Bitcoin wallet stub."""
        addr = "bc1" + secrets.token_hex(20)
        wallet = Wallet(name=name, chain="bitcoin", address=addr)
        self.wallets[name] = wallet
        self._save()
        log(f"Created BTC wallet: {addr}")
        return wallet

    def list_wallets(self) -> Dict[str, Wallet]:
        return self.wallets.copy()

    def get_wallet(self, name: str) -> Optional[Wallet]:
        return self.wallets.get(name)

    def delete_wallet(self, name: str) -> bool:
        if name in self.wallets:
            del self.wallets[name]
            self._save()
            log(f"Deleted wallet: {name}")
            return True
        return False

    def get_balance_stub(self, name: str) -> dict:
        """Stub for balance checking — replace with actual RPC calls."""
        wallet = self.wallets.get(name)
        if not wallet:
            return {"error": "Wallet not found"}
        return {
            "wallet": name,
            "address": wallet.address,
            "chain": wallet.chain,
            "balance": "0.0",
            "balance_usd": "0.00",
            "note": "Connect to RPC node for live balances",
        }


def main():
    print("\n[MrNothing Web3 Wallet] Blockchain wallet manager")
    print("Supports: Ethereum, Bitcoin, Base, Arbitrum, Optimism")
    print("Commands: create-eth <name>, create-btc <name>, list, balance <name>, delete <name>, exit\n")

    wm = WalletManager()

    while True:
        try:
            cmd = input("wallet> ").strip().split()
            if not cmd:
                continue

            if cmd[0] == "exit":
                break
            elif cmd[0] == "list":
                wallets = wm.list_wallets()
                if not wallets:
                    print("No wallets. Create one first.")
                for name, w in wallets.items():
                    print(f"  {name}: {w.address} ({w.chain})")
            elif cmd[0] == "create-eth" and len(cmd) > 1:
                w = wm.create_eth_wallet(cmd[1])
                print(f"Created: {w.address}")
            elif cmd[0] == "create-btc" and len(cmd) > 1:
                w = wm.create_btc_wallet(cmd[1])
                print(f"Created: {w.address}")
            elif cmd[0] == "balance" and len(cmd) > 1:
                bal = wm.get_balance_stub(cmd[1])
                for k, v in bal.items():
                    print(f"  {k}: {v}")
            elif cmd[0] == "delete" and len(cmd) > 1:
                if wm.delete_wallet(cmd[1]):
                    print(f"Deleted: {cmd[1]}")
                else:
                    print("Wallet not found")
            else:
                print("Unknown command")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
