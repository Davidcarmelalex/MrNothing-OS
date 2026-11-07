import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from core.action_reservation import (
    ActionReservationRequest,
    DurableActionReservationLedger,
    ReservationStoreUnavailable,
    RESERVED,
    DISPATCH_STARTED,
    COMPLETED,
    FAILED_NO_EFFECT,
    CANCELLED,
    UNKNOWN_OUTCOME,
    derive_idempotency_key,
)

HEX_A = "a" * 64
HEX_B = "b" * 64
NONCE = "1" * 32


class DurableActionReservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, "actions.sqlite")
        self.now = 1_800_000_000_000
        self.ledger = DurableActionReservationLedger(
            self.path, clock_ms=lambda: self.now, max_entries=32
        )

    def tearDown(self):
        self.temp.cleanup()

    def request(self, **changes):
        base = ActionReservationRequest(
            owner_id="owner-1",
            device_id="pixel-caiman-1",
            session_id="session-1",
            capability_nonce=NONCE,
            protocol_version=2,
            action_id="navigate",
            arguments_sha256=HEX_A,
            issued_at_epoch_ms=self.now - 100,
            expires_at_epoch_ms=self.now + 29_900,
            transport_certificate_sha256=HEX_B,
            credential_generation=7,
            consent_public_key_sha256="c" * 64,
        )
        return replace(base, **changes)

    def reserve(self, request=None, ledger=None):
        return (ledger or self.ledger).reserve(self.request() if request is None else request)

    def test_first_reservation_is_durable_and_bound(self):
        decision = self.reserve()
        self.assertTrue(decision.applied)
        self.assertTrue(decision.created)
        self.assertEqual(decision.state, RESERVED)
        record = self.ledger.get(decision.idempotency_key)
        self.assertEqual(record.owner_id, "owner-1")
        self.assertEqual(record.device_id, "pixel-caiman-1")
        self.assertEqual(record.action_id, "navigate")
        self.assertEqual(record.arguments_sha256, HEX_A)
        self.assertEqual(record.credential_generation, 7)
        self.assertEqual(record.state, RESERVED)

    def test_same_capability_and_binding_is_idempotent_not_dispatchable(self):
        first = self.reserve()
        second = self.reserve()
        self.assertTrue(first.created)
        self.assertFalse(second.applied)
        self.assertFalse(second.created)
        self.assertEqual(second.reason, "IDEMPOTENT_REPLAY")
        self.assertEqual(first.idempotency_key, second.idempotency_key)
        self.assertEqual(second.state, RESERVED)

    def test_same_nonce_with_changed_arguments_is_conflict(self):
        first = self.reserve()
        second = self.reserve(self.request(arguments_sha256=HEX_B))
        self.assertTrue(first.applied)
        self.assertFalse(second.applied)
        self.assertEqual(second.reason, "IDEMPOTENCY_CONFLICT")
        self.assertEqual(second.state, RESERVED)

    def test_same_nonce_with_changed_transport_generation_is_conflict(self):
        first = self.reserve()
        second = self.reserve(self.request(credential_generation=8))
        self.assertTrue(first.applied)
        self.assertEqual(second.reason, "IDEMPOTENCY_CONFLICT")

    def test_new_consent_nonce_creates_distinct_reservation(self):
        first = self.reserve()
        second = self.reserve(self.request(capability_nonce="2" * 32))
        self.assertTrue(first.applied)
        self.assertTrue(second.applied)
        self.assertNotEqual(first.idempotency_key, second.idempotency_key)

    def test_dispatch_claim_is_one_use(self):
        reserved = self.reserve()
        first = self.ledger.claim_dispatch(reserved.idempotency_key)
        second = self.ledger.claim_dispatch(reserved.idempotency_key)
        self.assertTrue(first.applied)
        self.assertEqual(first.state, DISPATCH_STARTED)
        self.assertFalse(second.applied)
        self.assertEqual(second.reason, "ALREADY_CLAIMED")

    def test_concurrent_dispatch_claim_has_exactly_one_winner(self):
        reserved = self.reserve()
        ledgers = [
            DurableActionReservationLedger(self.path, clock_ms=lambda: self.now)
            for _ in range(12)
        ]
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(
                lambda ledger: ledger.claim_dispatch(reserved.idempotency_key),
                ledgers,
            ))
        self.assertEqual(sum(result.applied for result in results), 1)
        self.assertEqual(
            sum(result.reason == "ALREADY_CLAIMED" for result in results), 11
        )

    def test_concurrent_duplicate_reservations_have_exactly_one_creator(self):
        ledgers = [
            DurableActionReservationLedger(self.path, clock_ms=lambda: self.now)
            for _ in range(12)
        ]
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda ledger: ledger.reserve(self.request()), ledgers))
        self.assertEqual(sum(result.created for result in results), 1)
        self.assertEqual(sum(result.reason == "IDEMPOTENT_REPLAY" for result in results), 11)

    def test_cancel_only_before_dispatch(self):
        reserved = self.reserve()
        cancelled = self.ledger.cancel_before_dispatch(reserved.idempotency_key)
        self.assertTrue(cancelled.applied)
        self.assertEqual(cancelled.state, CANCELLED)
        self.assertFalse(self.ledger.claim_dispatch(reserved.idempotency_key).applied)

    def test_cancel_after_dispatch_is_not_reported_as_cancelled(self):
        reserved = self.reserve()
        self.assertTrue(self.ledger.claim_dispatch(reserved.idempotency_key).applied)
        cancelled = self.ledger.cancel_before_dispatch(reserved.idempotency_key)
        self.assertFalse(cancelled.applied)
        self.assertEqual(cancelled.reason, "DISPATCH_ALREADY_STARTED")
        self.assertEqual(cancelled.state, DISPATCH_STARTED)

    def test_cancel_is_idempotent(self):
        reserved = self.reserve()
        self.assertTrue(self.ledger.cancel_before_dispatch(reserved.idempotency_key).applied)
        repeated = self.ledger.cancel_before_dispatch(reserved.idempotency_key)
        self.assertTrue(repeated.applied)
        self.assertEqual(repeated.reason, "ALREADY_CANCELLED")

    def test_permission_denial_can_be_recorded_before_dispatch(self):
        reserved = self.reserve()
        denied = self.ledger.reject_before_dispatch(
            reserved.idempotency_key, reason_code="PERMISSION_REVOKED"
        )
        self.assertTrue(denied.applied)
        self.assertEqual(denied.state, FAILED_NO_EFFECT)
        record = self.ledger.get(reserved.idempotency_key)
        self.assertEqual(record.outcome_code, "PERMISSION_REVOKED")
        self.assertFalse(self.ledger.claim_dispatch(reserved.idempotency_key).applied)

    def test_pre_dispatch_denial_is_idempotent_and_conflicts_are_rejected(self):
        reserved = self.reserve()
        first = self.ledger.reject_before_dispatch(
            reserved.idempotency_key, reason_code="PERMISSION_REVOKED"
        )
        repeated = self.ledger.reject_before_dispatch(
            reserved.idempotency_key, reason_code="PERMISSION_REVOKED"
        )
        conflict = self.ledger.reject_before_dispatch(
            reserved.idempotency_key, reason_code="POLICY_DENIED"
        )
        self.assertTrue(first.applied)
        self.assertTrue(repeated.applied)
        self.assertEqual(repeated.reason, "DENIAL_ALREADY_RECORDED")
        self.assertFalse(conflict.applied)
        self.assertEqual(conflict.reason, "OUTCOME_CONFLICT")

    def test_pre_dispatch_denial_loses_to_dispatch_claim_race(self):
        reserved = self.reserve()
        self.assertTrue(self.ledger.claim_dispatch(reserved.idempotency_key).applied)
        denied = self.ledger.reject_before_dispatch(
            reserved.idempotency_key, reason_code="PERMISSION_REVOKED"
        )
        self.assertFalse(denied.applied)
        self.assertEqual(denied.reason, "DISPATCH_ALREADY_STARTED")

    def test_completed_outcome_is_persisted_and_idempotent(self):
        reserved = self.reserve()
        self.ledger.claim_dispatch(reserved.idempotency_key)
        first = self.ledger.record_outcome(
            reserved.idempotency_key, state=COMPLETED,
            outcome_code="ACTION_RESULT_VERIFIED", outcome_sha256=HEX_A,
        )
        second = self.ledger.record_outcome(
            reserved.idempotency_key, state=COMPLETED,
            outcome_code="ACTION_RESULT_VERIFIED", outcome_sha256=HEX_A,
        )
        self.assertTrue(first.applied)
        self.assertEqual(first.reason, "OUTCOME_RECORDED")
        self.assertTrue(second.applied)
        self.assertEqual(second.reason, "OUTCOME_ALREADY_RECORDED")
        self.assertEqual(self.ledger.get(reserved.idempotency_key).state, COMPLETED)

    def test_conflicting_terminal_outcome_is_rejected(self):
        reserved = self.reserve()
        self.ledger.claim_dispatch(reserved.idempotency_key)
        self.assertTrue(self.ledger.record_outcome(
            reserved.idempotency_key, state=COMPLETED,
            outcome_code="DONE",
        ).applied)
        conflict = self.ledger.record_outcome(
            reserved.idempotency_key, state=UNKNOWN_OUTCOME,
            outcome_code="UNCERTAIN",
        )
        self.assertFalse(conflict.applied)
        self.assertEqual(conflict.reason, "INVALID_STATE")

    def test_unknown_outcome_is_sticky_and_never_reclaimed(self):
        reserved = self.reserve()
        self.ledger.claim_dispatch(reserved.idempotency_key)
        self.assertTrue(self.ledger.record_outcome(
            reserved.idempotency_key, state=UNKNOWN_OUTCOME,
            outcome_code="PROCESS_INTERRUPTED",
        ).applied)
        retry = self.ledger.claim_dispatch(reserved.idempotency_key)
        self.assertFalse(retry.applied)
        self.assertEqual(retry.reason, "TERMINAL_STATE")
        self.assertEqual(retry.state, UNKNOWN_OUTCOME)

    def test_dispatch_started_survives_restart_without_auto_retry(self):
        reserved = self.reserve()
        self.assertTrue(self.ledger.claim_dispatch(reserved.idempotency_key).applied)
        reopened = DurableActionReservationLedger(
            self.path, clock_ms=lambda: self.now
        )
        record = reopened.get(reserved.idempotency_key)
        self.assertEqual(record.state, DISPATCH_STARTED)
        self.assertFalse(reopened.claim_dispatch(reserved.idempotency_key).applied)
        self.assertEqual(
            reopened.claim_dispatch(reserved.idempotency_key).reason,
            "ALREADY_CLAIMED",
        )

    def test_restart_preserves_terminal_outcome_and_replay_binding(self):
        reserved = self.reserve()
        self.ledger.claim_dispatch(reserved.idempotency_key)
        self.ledger.record_outcome(
            reserved.idempotency_key, state=FAILED_NO_EFFECT,
            outcome_code="PRECONDITION_FAILED",
        )
        reopened = DurableActionReservationLedger(
            self.path, clock_ms=lambda: self.now
        )
        self.assertEqual(
            reopened.get(reserved.idempotency_key).state, FAILED_NO_EFFECT
        )
        duplicate = reopened.reserve(self.request())
        self.assertFalse(duplicate.applied)
        self.assertEqual(duplicate.reason, "IDEMPOTENT_REPLAY")
        self.assertEqual(duplicate.state, FAILED_NO_EFFECT)

    def test_capacity_is_fail_closed_and_terminal_records_are_not_evicted(self):
        path = os.path.join(self.temp.name, "small.sqlite")
        small = DurableActionReservationLedger(
            path, max_entries=1, clock_ms=lambda: self.now
        )
        first = small.reserve(self.request())
        small.cancel_before_dispatch(first.idempotency_key)
        second = small.reserve(self.request(capability_nonce="2" * 32))
        self.assertFalse(second.applied)
        self.assertEqual(second.reason, "CAPACITY_REACHED")

    def test_invalid_boolean_integer_fields_are_rejected(self):
        for change in (
            {"protocol_version": True},
            {"credential_generation": True},
            {"issued_at_epoch_ms": True},
            {"expires_at_epoch_ms": True},
        ):
            with self.subTest(change=change):
                result = self.reserve(self.request(**change))
                self.assertFalse(result.applied)
                self.assertEqual(result.reason, "INVALID_REQUEST")

    def test_invalid_digest_nonce_and_ttl_are_rejected(self):
        invalid = (
            self.request(arguments_sha256="A" * 64),
            self.request(capability_nonce="not-a-nonce"),
            self.request(expires_at_epoch_ms=self.now + 30_001),
            self.request(expires_at_epoch_ms=self.now - 101),
        )
        for request in invalid:
            with self.subTest(request=request):
                self.assertFalse(self.reserve(request).applied)

    def test_unknown_action_identifier_is_rejected(self):
        for action in ("root_shell", "send_message", "transfer_money", "root shell"):
            with self.subTest(action=action):
                result = self.reserve(self.request(action_id=action))
                self.assertFalse(result.applied)

    def test_v1_is_limited_to_empty_screen_action_schema(self):
        invalid = self.request(protocol_version=1, action_id="navigate")
        self.assertFalse(self.reserve(invalid).applied)

    def test_invalid_outcome_data_is_rejected(self):
        reserved = self.reserve()
        self.assertFalse(self.ledger.record_outcome(
            reserved.idempotency_key, state=COMPLETED,
            outcome_code="contains spaces",
        ).applied)
        self.assertFalse(self.ledger.record_outcome(
            reserved.idempotency_key, state=COMPLETED,
            outcome_code="DONE", outcome_sha256="bad",
        ).applied)
        self.assertFalse(self.ledger.record_outcome(
            reserved.idempotency_key, state=["COMPLETED"],
            outcome_code="DONE",
        ).applied)

    def test_outcome_cannot_be_recorded_before_dispatch(self):
        reserved = self.reserve()
        result = self.ledger.record_outcome(
            reserved.idempotency_key, state=COMPLETED,
            outcome_code="DONE",
        )
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "INVALID_STATE")

    def test_missing_reservation_cannot_be_claimed(self):
        result = self.ledger.claim_dispatch("f" * 64)
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "RESERVATION_NOT_FOUND")

    def test_raw_arguments_and_results_are_not_database_columns(self):
        with closing(sqlite3.connect(self.path)) as db:
            columns = {
                row[1] for row in db.execute("PRAGMA table_info(action_reservations)")
            }
        self.assertNotIn("arguments_json", columns)
        self.assertNotIn("raw_arguments", columns)
        self.assertNotIn("result_json", columns)
        self.assertIn("arguments_sha256", columns)
        self.assertIn("outcome_sha256", columns)

    def test_idempotency_key_binds_all_security_context(self):
        base = self.request()
        key = derive_idempotency_key(base)
        variants = (
            replace(base, owner_id="owner-2"),
            replace(base, device_id="pixel-caiman-2"),
            replace(base, session_id="session-2"),
            replace(base, protocol_version=1, action_id="read_screen"),
            replace(base, action_id="scroll"),
            replace(base, arguments_sha256=HEX_B),
            replace(base, transport_certificate_sha256="d" * 64),
            replace(base, credential_generation=8),
            replace(base, consent_public_key_sha256="e" * 64),
            replace(base, expires_at_epoch_ms=self.now + 29_800),
        )
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertNotEqual(key, derive_idempotency_key(variant))

    def test_database_path_must_be_file_backed_and_private(self):
        with self.assertRaises(ValueError):
            DurableActionReservationLedger(":memory:")
        with self.assertRaises(ValueError):
            DurableActionReservationLedger(self.temp.name)
        with self.assertRaises(ReservationStoreUnavailable):
            DurableActionReservationLedger(
                os.path.join(self.temp.name, "missing", "actions.sqlite")
            )
        if os.name == "posix":
            public_path = os.path.join(self.temp.name, "public.sqlite")
            with open(public_path, "wb"):
                pass
            os.chmod(public_path, 0o644)
            with self.assertRaises(ValueError):
                DurableActionReservationLedger(public_path)

    def test_symlink_database_is_rejected(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        target = os.path.join(self.temp.name, "target.sqlite")
        with open(target, "wb"):
            pass
        link = os.path.join(self.temp.name, "link.sqlite")
        os.symlink(target, link)
        with self.assertRaises(ValueError):
            DurableActionReservationLedger(link)

    def test_database_uses_wal_full_sync_and_versioned_schema(self):
        with closing(self.ledger._connect()) as db:
            self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0], "wal")
            self.assertEqual(db.execute("PRAGMA synchronous").fetchone()[0], 2)
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_corrupt_database_fails_closed(self):
        corrupt = os.path.join(self.temp.name, "corrupt.sqlite")
        with open(corrupt, "wb") as stream:
            stream.write(b"not a sqlite database")
        if os.name == "posix":
            os.chmod(corrupt, 0o600)
        with self.assertRaises(ReservationStoreUnavailable):
            DurableActionReservationLedger(corrupt)


if __name__ == "__main__":
    unittest.main()
