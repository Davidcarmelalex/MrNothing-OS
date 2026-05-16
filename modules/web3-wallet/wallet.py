#!/usr/bin/env python3
"""
MrNothing Web3 Wallet — Self-custodial ETH/EVM wallet
Runs fully offline for key generation. No cloud, no API keys needed.
"""
import os, json, hashlib, secrets, time
from pathlib import Path

VERSION = "1.0.0"
HOME = Path.home() / "mrnothing"
WALLET_FILE = HOME / "wallet" / "keystore.enc"
LOG = HOME / "logs" / "web3.log"

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] [WEB3] {msg}"
    print(line)

def generate_entropy():
    """Generate 32 bytes of cryptographic entropy."""
    return secrets.token_bytes(32)

def bytes_to_hex(b):
    return b.hex()

def generate_keypair():
    """
    Generate an EVM-compatible private key.
    Full secp256k1 derivation requires eth-keys or web3.py.
    This generates the private key seed securely.
    """
    try:
        from eth_account import Account
        Account.enable_unaudited_hdwallet_features()
        acct, mnemonic = Account.create_with_mnemonic()
        return {
            "address": acct.address,
            "private_key": acct.key.hex(),
            "mnemonic": mnemonic,
            "method": "eth_account"
        }
    except ImportError:
        # Fallback: generate raw private key
        private_key = generate_entropy()
        # Derive a deterministic "address" from private key hash (not real secp256k1)
        pk_hash = hashlib.sha256(private_key).digest()
        addr_bytes = hashlib.new('sha256', pk_hash).digest()[-20:]
        address = "0x" + addr_bytes.hex()
        return {
            "address": address,
            "private_key": bytes_to_hex(private_key),
            "mnemonic": "Install eth-account for full BIP39 mnemonic support",
            "method": "raw_fallback"
        }

def encrypt_wallet(data, password):
    """XOR-based encryption for local storage."""
    key = hashlib.sha256(password.encode()).digest()
    data_bytes = json.dumps(data).encode()
    encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(data_bytes)])
    return encrypted.hex()

def decrypt_wallet(encrypted_hex, password):
    key = hashlib.sha256(password.encode()).digest()
    encrypted = bytes.fromhex(encrypted_hex)
    decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted)])
    return json.loads(decrypted.decode())

def save_wallet(wallet, password):
    WALLET_FILE.parent.mkdir(parents=True, exist_ok=True)
    encrypted = encrypt_wallet(wallet, password)
    with open(WALLET_FILE, "w") as f:
        json.dump({"encrypted": encrypted, "version": VERSION, "created": time.time()}, f)
    log(f"Wallet saved to {WALLET_FILE}")

def load_wallet(password):
    if not WALLET_FILE.exists():
        return None
    with open(WALLET_FILE) as f:
        data = json.load(f)
    return decrypt_wallet(data["encrypted"], password)

def check_balance(address):
    """Check balance via public RPC (requires internet)."""
    try:
        import urllib.request
        payload = json.dumps({
            "jsonrpc": "2.0", "method": "eth_getBalance",
            "params": [address, "latest"], "id": 1
        }).encode()
        req = urllib.request.Request(
            "https://cloudflare-eth.com",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            hex_balance = result.get("result", "0x0")
            wei = int(hex_balance, 16)
            eth = wei / 1e18
            return f"{eth:.6f} ETH"
    except Exception as e:
        return f"[Offline or error: {e}]"

def main():
    print(f"\n[WEB3 WALLET v{VERSION}] Self-Custodial EVM Wallet")
    print("⚠  This wallet runs locally. Back up your private key and mnemonic.\n")
    print("Commands: create, load, balance, show, export, exit\n")

    current_wallet = None

    while True:
        try:
            cmd = input("wallet> ").strip().lower()
            if not cmd: continue

            if cmd == "exit":
                break

            elif cmd == "create":
                print("Generating new wallet...")
                wallet = generate_keypair()
                password = input("Set wallet password: ")
                save_wallet(wallet, password)
                current_wallet = wallet
                print(f"\n✅ Wallet Created!")
                print(f"   Address:  {wallet['address']}")
                print(f"   Method:   {wallet['method']}")
                if wallet.get('mnemonic') and 'Install' not in wallet['mnemonic']:
                    print(f"\n⚠  WRITE THIS DOWN — Mnemonic (seed phrase):")
                    print(f"   {wallet['mnemonic']}")
                print(f"\n⚠  NEVER share your private key with anyone.")

            elif cmd == "load":
                if not WALLET_FILE.exists():
                    print("No wallet found. Create one first.")
                    continue
                password = input("Wallet password: ")
                try:
                    current_wallet = load_wallet(password)
                    print(f"✅ Wallet loaded: {current_wallet['address']}")
                except:
                    print("❌ Wrong password or corrupted wallet.")

            elif cmd == "balance":
                if not current_wallet:
                    print("Load a wallet first.")
                    continue
                print(f"Checking balance for {current_wallet['address']}...")
                bal = check_balance(current_wallet['address'])
                print(f"Balance: {bal}")

            elif cmd == "show":
                if not current_wallet:
                    print("Load a wallet first.")
                    continue
                print(f"  Address: {current_wallet['address']}")
                print(f"  Method:  {current_wallet['method']}")

            elif cmd == "export":
                if not current_wallet:
                    print("Load a wallet first.")
                    continue
                confirm = input("⚠  Export private key? This is sensitive. Type YES: ")
                if confirm == "YES":
                    print(f"  Private Key: {current_wallet.get('private_key', 'N/A')}")
                    if current_wallet.get('mnemonic') and 'Install' not in current_wallet['mnemonic']:
                        print(f"  Mnemonic: {current_wallet['mnemonic']}")

            else:
                print("Unknown command. Try: create, load, balance, show, export, exit")

        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    main()
