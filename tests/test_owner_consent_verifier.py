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

    def test_revocation_capacity_overflow_fails_closed_for_every_session(self):
        self.verifier = ConsentVerifier(
            device_id="pixel9pro-1", owner_id="owner-1",
            owner_ui_verification_key=KEY, clock=lambda: self.now,
            max_revoked_sessions=1,
        )
        self.assertTrue(self.verifier.revoke_session("session-1"))
        self.assertFalse(self.verifier.revoke_session("session-2"))
        self.assertEqual(len(self.verifier._revoked), 1)
        self.assertTrue(self.verifier._revocation_overflow)
        for session_id, nonce in (
            ("session-1", "unique-nonce-00000001"),
            ("session-2", "unique-nonce-00000002"),
            ("session-3", "unique-nonce-00000003"),
        ):
            cap = self.mint(session_id=session_id, nonce=nonce)
            self.assertFalse(self.check(cap, session_id=session_id))

    def test_duplicate_revocation_is_idempotent_and_does_not_consume_capacity(self):
        self.verifier = ConsentVerifier(
            device_id="pixel9pro-1", owner_id="owner-1",
            owner_ui_verification_key=KEY, clock=lambda: self.now,
            max_revoked_sessions=1,
        )
        self.assertTrue(self.verifier.revoke_session("session-1"))
        self.assertTrue(self.verifier.revoke_session("session-1"))
        cap = self.mint(
            session_id="session-2",
            nonce="unique-nonce-00000002",
        )
        self.assertTrue(self.check(cap, session_id="session-2"))
        self.assertFalse(self.verifier._revocation_overflow)

    def test_concurrent_revocations_cannot_exceed_capacity_and_fail_closed(self):
        self.verifier = ConsentVerifier(
            device_id="pixel9pro-1", owner_id="owner-1",
            owner_ui_verification_key=KEY, clock=lambda: self.now,
            max_revoked_sessions=2,
        )
        sessions = [f"session-{index}" for index in range(10)]
        with ThreadPoolExecutor(max_workers=10) as pool:
            outcomes = list(pool.map(self.verifier.revoke_session, sessions))
        self.assertEqual(outcomes.count(True), 2)
        self.assertEqual(outcomes.count(False), 8)
        self.assertEqual(len(self.verifier._revoked), 2)
        self.assertTrue(self.verifier._revocation_overflow)
        for index, session_id in enumerate(sessions):
            cap = self.mint(
                session_id=session_id,
                nonce=f"unique-nonce-{index:08d}",
            )
            self.assertFalse(self.check(cap, session_id=session_id))

    def test_invalid_revocation_capacity_is_rejected(self):
        for limit in (True, 0, 100_001):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    ConsentVerifier(
                        device_id="pixel9pro-1", owner_id="owner-1",
                        owner_ui_verification_key=KEY, clock=lambda: self.now,
                        max_revoked_sessions=limit,
                    )

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
