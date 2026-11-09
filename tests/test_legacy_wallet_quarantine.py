"""Fail-closed regression tests for the quarantined legacy wallet module."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "legacy_wallet_under_test", ROOT / "modules" / "web3-wallet" / "wallet.py"
)
WALLET = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WALLET)


class LegacyWalletQuarantineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "mrnothing"
        self.directory = self.home / "wallet"
        self.path = self.directory / "wallets.json"
        for key, value in (
            ("HOME", self.home),
            ("WALLET_DIR", self.directory),
            ("WALLET_FILE", self.path),
            ("LOG", self.home / "logs" / "wallet.log"),
        ):
            patcher = patch.object(WALLET, key, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _write(self, records):
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(records), encoding="utf-8")

    def test_ethereum_creation_refused_without_writing(self):
        manager = WALLET.WalletManager()
        with self.assertRaises(WALLET.WalletSecurityError):
            manager.create_eth_wallet("test")
        self.assertFalse(self.path.exists())
        self.assertEqual(manager.list_wallets(), {})

    def test_bitcoin_fake_address_generation_refused(self):
        manager = WALLET.WalletManager()
        with self.assertRaises(WALLET.WalletSecurityError):
            manager.create_btc_wallet("test")
        self.assertFalse(self.path.exists())

    def test_secret_constructor_and_serialization_refused(self):
        with self.assertRaises(WALLET.WalletSecurityError):
            WALLET.Wallet("name", "ethereum", "0x123", private_key="secret")
        watch = WALLET.Wallet("name", "ethereum", "0x123")
        watch.private_key = "secret"
        with self.assertRaises(WALLET.WalletSecurityError):
            watch.to_dict()

    def test_legacy_secret_file_refused_and_preserved_byte_for_byte(self):
        self._write({"old": {"name": "old", "chain": "ethereum",
                             "address": "0x123", "private_key": "sensitive-test-secret"}})
        original = self.path.read_bytes()
        with self.assertRaisesRegex(WALLET.WalletSecurityError, "plaintext private keys"):
            WALLET.WalletManager()
        self.assertEqual(self.path.read_bytes(), original)

    def test_save_rechecks_legacy_secret_before_overwriting(self):
        manager = WALLET.WalletManager()
        manager.wallets["watch"] = WALLET.Wallet("watch", "ethereum", "0x123")
        self._write({"old": {"name": "old", "chain": "ethereum",
                             "address": "0x123", "private_key": "secret"}})
        original = self.path.read_bytes()
        with self.assertRaises(WALLET.WalletSecurityError):
            manager._save()
        self.assertEqual(self.path.read_bytes(), original)

    def test_legacy_null_secret_field_loads_and_saves_without_key_field(self):
        self._write({"watch": {"name": "watch", "chain": "ethereum",
                               "address": "0x123", "private_key": None}})
        manager = WALLET.WalletManager()
        manager._save()
        self.assertNotIn("private_key", json.loads(self.path.read_text())["watch"])
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_symlinked_storage_file_is_refused_without_following(self):
        self.directory.mkdir(parents=True)
        target = Path(self.temp.name) / "outside.json"
        target.write_text("outside")
        self.path.symlink_to(target)
        with self.assertRaises(WALLET.WalletSecurityError):
            WALLET.WalletManager()
        self.assertEqual(target.read_text(), "outside")

    def test_delete_restores_memory_if_storage_refuses(self):
        manager = WALLET.WalletManager()
        manager.wallets["watch"] = WALLET.Wallet("watch", "ethereum", "0x123")
        with patch.object(manager, "_save", side_effect=WALLET.WalletSecurityError("refused")):
            with self.assertRaises(WALLET.WalletSecurityError):
                manager.delete_wallet("watch")
        self.assertIn("watch", manager.wallets)

    def test_balance_stub_does_not_fabricate_zero_balance(self):
        manager = WALLET.WalletManager()
        manager.wallets["watch"] = WALLET.Wallet("watch", "ethereum", "0x123")
        result = manager.get_balance_stub("watch")
        self.assertIsNone(result["balance"])
        self.assertIsNone(result["balance_usd"])
        self.assertIn("unknown", result["note"].lower())

    def test_invalid_existing_json_preserved(self):
        self.directory.mkdir(parents=True)
        self.path.write_text("{not valid json")
        original = self.path.read_bytes()
        with self.assertRaises(WALLET.WalletSecurityError):
            WALLET.WalletManager()
        self.assertEqual(self.path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
