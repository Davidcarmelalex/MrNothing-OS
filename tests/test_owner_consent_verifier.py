"""Synthetic signed fixtures; no real owner approval or Android permissions."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import hmac
import unittest

from core.owner_consent_verifier import (
    ConsentCapability, ConsentVerifier, MAX_TTL_NS, _canonical,
)


KEY = b"synthetic-test-only-owner-ui-key!!"


class ConsentVerifierTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_000_000_000_000
        self.verifier = ConsentVerifier(
            device_id="pixel9pro-1", owner_id="owner-1",
            owner_ui_verification_key=KEY, clock=lambda: self.now,
        )

    def mint(self, **changes):
        values = dict(
            version=1, device_id="pixel9pro-1", owner_id="owner-1",
            session_id="session-1", action="read_screen",
            nonce="unique-nonce-00000001", epoch=self.verifier.epoch,
            issued_mono_ns=self.now, expires_mono_ns=self.now + 10_000_000_000,
            signature="",
        )
        values.update(changes)
        cap = ConsentCapability(**values)
        return replace(cap, signature=hmac.new(KEY, _canonical(cap), hashlib.sha256).hexdigest())

    def check(self, cap, *, session_id="session-1", action="read_screen"):
        return self.verifier.verify_and_consume(cap, session_id=session_id, action=action)

    def test_valid_one_use_capability(self):
        cap = self.mint()
        self.assertTrue(self.check(cap))
        self.assertFalse(self.check(cap))

    def test_reject_cross_device_owner_session_action(self):
        for change in ({"device_id": "other"}, {"owner_id": "other"},
                       {"session_id": "other"}, {"action": "navigate"}):
            with self.subTest(change=change):
                self.assertFalse(self.check(self.mint(**change)))

    def test_reject_context_spoofing(self):
        cap = self.mint()
        self.assertFalse(self.check(cap, session_id="other"))
        self.assertFalse(self.check(cap, action="navigate"))

    def test_reject_unsupported_scope_even_if_signed(self):
        self.assertFalse(self.check(self.mint(action="transfer_money"), action="transfer_money"))

    def test_reject_expired_and_future(self):
        self.assertFalse(self.check(self.mint(expires_mono_ns=self.now)))
        self.assertFalse(self.check(self.mint(issued_mono_ns=self.now + 1)))

    def test_reject_oversized_and_zero_duration(self):
        self.assertFalse(self.check(self.mint(expires_mono_ns=self.now + MAX_TTL_NS + 1)))
        self.assertFalse(self.check(self.mint(expires_mono_ns=self.now)))

    def test_reject_tampered_signature(self):
        self.assertFalse(self.check(replace(self.mint(), signature="0" * 64)))
        self.assertFalse(self.check(replace(self.mint(), signature="invalid")))

    def test_reject_tampered_payload(self):
        self.assertFalse(self.check(replace(self.mint(), nonce="different-nonce-12345")))

    def test_reject_replayed_nonce_with_different_signature(self):
        cap = self.mint()
        self.assertTrue(self.check(cap))
        self.assertFalse(self.check(self.mint(expires_mono_ns=self.now + 9_000_000_000)))

    def test_revoke_blocks_existing_and_future_tokens(self):
        cap = self.mint()
        self.verifier.revoke_session("session-1")
        self.assertFalse(self.check(cap))
        self.assertFalse(self.check(self.mint(nonce="unique-nonce-00000002")))

    def test_process_restart_invalidates_old_epoch(self):
        cap = self.mint()
        restarted = ConsentVerifier(
            device_id="pixel9pro-1", owner_id="owner-1",
            owner_ui_verification_key=KEY, clock=lambda: self.now,
        )
        self.assertFalse(restarted.verify_and_consume(
            cap, session_id="session-1", action="read_screen"))

    def test_capacity_fails_closed(self):
        self.verifier = ConsentVerifier(
            device_id="pixel9pro-1", owner_id="owner-1",
            owner_ui_verification_key=KEY, clock=lambda: self.now, max_uses=1)
        self.assertTrue(self.check(self.mint()))
        self.assertFalse(self.check(self.mint(nonce="unique-nonce-00000002")))

    def test_concurrent_consumption_only_once(self):
        cap = self.mint()
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda _: self.check(cap), range(24)))
        self.assertEqual(sum(results), 1)

    def test_reject_malformed_types(self):
        self.assertFalse(self.check(self.mint(version=True)))
        self.assertFalse(self.check(self.mint(issued_mono_ns=True)))
        self.assertFalse(self.check(self.mint(nonce="x")))
        self.assertFalse(self.check(self.mint(session_id="\n")))
        self.assertFalse(self.check(object()))

    def test_reject_untrusted_key_and_identity(self):
        with self.assertRaises(ValueError):
            ConsentVerifier(device_id="d", owner_id="o", owner_ui_verification_key=b"short")
        with self.assertRaises(ValueError):
            ConsentVerifier(device_id="\n", owner_id="o", owner_ui_verification_key=KEY)

    def test_time_boundary_expiry(self):
        cap = self.mint()
        self.now = cap.expires_mono_ns
        self.assertFalse(self.check(cap))


if __name__ == "__main__":
    unittest.main()
