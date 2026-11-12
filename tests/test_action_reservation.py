import base64
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from core.owner_enrollment_registry import (
    SCHEMA_NAME, SQLiteOwnerEnrollmentRegistry, _canonical_payload,
)
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


class _CommitAcknowledgementLostConnection:
    """Test proxy: commit durably, then simulate losing the caller acknowledgement."""

    def __init__(self, connection):
        self._connection = connection
        self._lost = False

    @property
    def in_transaction(self):
        return self._connection.in_transaction

    def execute(self, sql, *args):
        if (
            type(sql) is str
            and sql.strip().upper() == "COMMIT"
            and not self._lost
        ):
            self._lost = True
            self._connection.execute(sql, *args)
            raise sqlite3.OperationalError(
                "injected loss of COMMIT acknowledgement after durable commit"
            )
        return self._connection.execute(sql, *args)

    def close(self):
        self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


_CLAIM_DISPATCH_SUBPROCESS = r"""
import base64
import json
import os
import sys
import time

from core.action_reservation import DurableActionReservationLedger
from core.owner_enrollment_registry import SQLiteOwnerEnrollmentRegistry

ledger_path, registry_path, authority_b64, key, now_text, gate_path = sys.argv[1:]
registry = SQLiteOwnerEnrollmentRegistry(
    registry_path,
    authority_public_key_spki_der=base64.urlsafe_b64decode(authority_b64),
    authority_key_id="test-authority",
    timeout_seconds=10.0,
)
ledger = DurableActionReservationLedger(
    ledger_path,
    clock_ms=lambda: int(now_text),
    busy_timeout_ms=10_000,
)
ready_path = f"{gate_path}.{os.getpid()}.ready"
with open(ready_path, "x", encoding="ascii") as ready:
    ready.write("ready\\n")
deadline = time.monotonic() + 15.0
while not os.path.exists(gate_path):
    if time.monotonic() >= deadline:
        raise SystemExit("claim start gate timed out")
    time.sleep(0.01)
decision = ledger.claim_dispatch(
    key,
    enrollment_registry=registry,
    final_admission_guard=lambda: True,
)
print(json.dumps({
    "applied": decision.applied,
    "reason": decision.reason,
    "state": decision.state,
}), flush=True)
# Abrupt process exit after the durable claim result: no interpreter cleanup
# is allowed to turn process shutdown into a hidden recovery/retry path.
os._exit(0)
"""

_CRASH_AFTER_LEDGER_COMMIT_SUBPROCESS = r"""
import base64
import sys
import time

from core.action_reservation import DurableActionReservationLedger
from core.owner_enrollment_registry import SQLiteOwnerEnrollmentRegistry


class CommitThenPause:
    def __init__(self, connection, marker_path):
        self._connection = connection
        self._marker_path = marker_path
        self._paused = False

    def execute(self, sql, *args):
        result = self._connection.execute(sql, *args)
        if (
            type(sql) is str
            and sql.strip().upper() == "COMMIT"
            and not self._paused
        ):
            self._paused = True
            with open(self._marker_path, "x", encoding="ascii") as marker:
                marker.write("ledger-commit-durable")
            # Parent terminates this process after the underlying COMMIT
            # succeeds but before the enrollment context can be released.
            while True:
                time.sleep(0.05)
        return result

    def close(self):
        self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


ledger_path, registry_path, authority_b64, key, now_text, marker_path = sys.argv[1:]
registry = SQLiteOwnerEnrollmentRegistry(
    registry_path,
    authority_public_key_spki_der=base64.urlsafe_b64decode(authority_b64),
    authority_key_id="test-authority",
    timeout_seconds=10.0,
)
ledger = DurableActionReservationLedger(
    ledger_path,
    clock_ms=lambda: int(now_text),
    busy_timeout_ms=10_000,
)
original_connect = ledger._connect
ledger._connect = lambda: CommitThenPause(original_connect(), marker_path)
ledger.claim_dispatch(
    key,
    enrollment_registry=registry,
    final_admission_guard=lambda: True,
)
raise SystemExit("commit pause unexpectedly returned")
"""


_CRASH_BEFORE_LEDGER_COMMIT_SUBPROCESS = r"""
import base64
import sys
import time

from core.action_reservation import DurableActionReservationLedger
from core.owner_enrollment_registry import SQLiteOwnerEnrollmentRegistry


class PauseBeforeCommit:
    def __init__(self, connection, marker_path):
        self._connection = connection
        self._marker_path = marker_path
        self._paused = False

    @property
    def in_transaction(self):
        return self._connection.in_transaction

    def execute(self, sql, *args):
        if (
            type(sql) is str
            and sql.strip().upper() == "COMMIT"
            and not self._paused
        ):
            self._paused = True
            # This marker is emitted before the underlying SQLite COMMIT call.
            # The parent kills this process while the UPDATE remains uncommitted.
            with open(self._marker_path, "x", encoding="ascii") as marker:
                marker.write("ledger-commit-not-executed")
            while True:
                time.sleep(0.05)
        return self._connection.execute(sql, *args)

    def close(self):
        self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


ledger_path, registry_path, authority_b64, key, now_text, marker_path = sys.argv[1:]
registry = SQLiteOwnerEnrollmentRegistry(
    registry_path,
    authority_public_key_spki_der=base64.urlsafe_b64decode(authority_b64),
    authority_key_id="test-authority",
    timeout_seconds=10.0,
)
ledger = DurableActionReservationLedger(
    ledger_path,
    clock_ms=lambda: int(now_text),
    busy_timeout_ms=10_000,
)
original_connect = ledger._connect
ledger._connect = lambda: PauseBeforeCommit(original_connect(), marker_path)
ledger.claim_dispatch(
    key,
    enrollment_registry=registry,
    final_admission_guard=lambda: True,
)
raise SystemExit("pre-commit pause unexpectedly returned")
"""

class DurableActionReservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, "actions.sqlite")
        self.now = 1_800_000_000_000
        self.authority = ed25519.Ed25519PrivateKey.generate()
        self.consent_key = ec.generate_private_key(ec.SECP256R1())
        self.consent_spki = self.consent_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.consent_digest = hashlib.sha256(self.consent_spki).hexdigest()
        self.registry = SQLiteOwnerEnrollmentRegistry(
            os.path.join(self.temp.name, "enrollment.sqlite"),
            authority_public_key_spki_der=self.authority.public_key().public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            ),
            authority_key_id="test-authority",
        )
        self.registry.initialize(explicit_first_install=True)
        payload = {
            "schema": SCHEMA_NAME,
            "version": 1,
            "operation": "enroll",
            "authority_key_id": "test-authority",
            "enrollment_id": "test-enrollment-1",
            "owner_id": "owner-1",
            "device_id": "pixel-caiman-1",
            "credential_generation": 1,
            "issued_at_epoch_ms": self.now - 1_000,
            "expires_at_epoch_ms": self.now + 60_000,
            "transport_certificate_sha256": HEX_B,
            "consent_public_key_spki_der": base64.urlsafe_b64encode(
                self.consent_spki
            ).rstrip(b"=").decode("ascii"),
            "consent_public_key_sha256": self.consent_digest,
        }
        envelope = json.dumps(
            {
                "payload": payload,
                "signature": base64.urlsafe_b64encode(
                    self.authority.sign(_canonical_payload(payload))
                ).rstrip(b"=").decode("ascii"),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        self.registry.apply_signed_enrollment(envelope, now_epoch_ms=self.now)
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
            credential_generation=1,
            consent_public_key_sha256=self.consent_digest,
        )
        return replace(base, **changes)

    def claim_dispatch(
        self, key, *, ledger=None, registry=None, final_admission_guard=lambda: True
    ):
        # The default is test-only storage evidence; production callers must
        # pass the live adapter-owned guard explicitly.
        return (ledger or self.ledger).claim_dispatch(
            key,
            enrollment_registry=registry or self.registry,
            final_admission_guard=final_admission_guard,
        )

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
        self.assertEqual(record.credential_generation, 1)
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
        first = self.claim_dispatch(reserved.idempotency_key)
        second = self.claim_dispatch(reserved.idempotency_key)
        self.assertTrue(first.applied)
        self.assertEqual(first.state, DISPATCH_STARTED)
        self.assertFalse(second.applied)
        self.assertEqual(second.reason, "ALREADY_CLAIMED")

    def test_expired_capability_cannot_create_a_reservation(self):
        request = self.request(expires_at_epoch_ms=self.now)
        result = self.ledger.reserve(request)
        self.assertFalse(result.applied)
        self.assertFalse(result.created)
        self.assertEqual(result.reason, "CAPABILITY_EXPIRED")
        self.assertIsNone(self.ledger.get(result.idempotency_key))

    def test_future_dated_capability_cannot_create_a_reservation(self):
        request = self.request(
            issued_at_epoch_ms=self.now + 1,
            expires_at_epoch_ms=self.now + 29_901,
        )
        result = self.ledger.reserve(request)
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "CAPABILITY_NOT_YET_VALID")
        self.assertIsNone(self.ledger.get(result.idempotency_key))

    def test_expired_reserved_capability_becomes_terminal_before_dispatch(self):
        reserved = self.reserve()
        record = self.ledger.get(reserved.idempotency_key)
        self.now = record.expires_at_epoch_ms

        result = self.claim_dispatch(reserved.idempotency_key)
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "CAPABILITY_EXPIRED")
        self.assertEqual(result.state, FAILED_NO_EFFECT)
        expired = self.ledger.get(reserved.idempotency_key)
        self.assertEqual(expired.state, FAILED_NO_EFFECT)
        self.assertEqual(expired.outcome_code, "CAPABILITY_EXPIRED")
        retry = self.claim_dispatch(reserved.idempotency_key)
        self.assertFalse(retry.applied)
        self.assertEqual(retry.reason, "TERMINAL_STATE")

    def test_future_dated_reserved_capability_waits_without_becoming_dispatchable(self):
        reserved = self.reserve()
        record = self.ledger.get(reserved.idempotency_key)
        self.now = record.issued_at_epoch_ms - 1

        early = self.claim_dispatch(reserved.idempotency_key)
        self.assertFalse(early.applied)
        self.assertEqual(early.reason, "CAPABILITY_NOT_YET_VALID")
        self.assertEqual(self.ledger.get(reserved.idempotency_key).state, RESERVED)

        self.now = record.issued_at_epoch_ms
        valid = self.claim_dispatch(reserved.idempotency_key)
        self.assertTrue(valid.applied)
        self.assertEqual(valid.state, DISPATCH_STARTED)

    def test_concurrent_dispatch_claim_has_exactly_one_winner(self):
        reserved = self.reserve()
        ledgers = [
            DurableActionReservationLedger(self.path, clock_ms=lambda: self.now)
            for _ in range(12)
        ]
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(
                lambda ledger: ledger.claim_dispatch(
                    reserved.idempotency_key, enrollment_registry=self.registry,
                    final_admission_guard=lambda: True,
                ),
                ledgers,
            ))
        self.assertEqual(sum(result.applied for result in results), 1)
        self.assertEqual(
            sum(result.reason == "ALREADY_CLAIMED" for result in results), 11
        )

    def test_cross_process_dispatch_claim_has_one_winner_and_survives_restart(self):
        reserved = self.reserve()
        authority_spki = self.authority.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        authority_b64 = base64.urlsafe_b64encode(authority_spki).decode("ascii")
        gate_path = os.path.join(self.temp.name, "release-claims")
        command = [
            sys.executable,
            "-c",
            _CLAIM_DISPATCH_SUBPROCESS,
            self.path,
            str(self.registry.path),
            authority_b64,
            reserved.idempotency_key,
            str(self.now),
            gate_path,
        ]
        processes = []
        results = []
        try:
            for _ in range(2):
                processes.append(subprocess.Popen(
                    command,
                    cwd=os.getcwd(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                ))
            ready_paths = [
                f"{gate_path}.{process.pid}.ready" for process in processes
            ]
            deadline = time.monotonic() + 15.0
            while not all(os.path.isfile(path) for path in ready_paths):
                if any(process.poll() is not None for process in processes):
                    details = [
                        process.communicate(timeout=5) for process in processes
                    ]
                    self.fail(f"claim subprocess exited before ready: {details!r}")
                if time.monotonic() >= deadline:
                    self.fail("claim subprocesses did not reach the start gate")
                time.sleep(0.01)

            with open(gate_path, "x", encoding="ascii") as gate:
                gate.write("go\n")

            for process in processes:
                stdout, stderr = process.communicate(timeout=20)
                self.assertEqual(process.returncode, 0, msg=stderr)
                results.append(json.loads(stdout))
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=5)

        self.assertEqual(len(results), 2)
        self.assertEqual(
            sum(result["applied"] is True for result in results), 1
        )
        self.assertEqual(
            sum(result["reason"] == "ALREADY_CLAIMED" for result in results), 1
        )
        self.assertTrue(all(
            result["state"] == DISPATCH_STARTED for result in results
        ))

        # Reopen from the parent after both child interpreters have exited.
        reopened = DurableActionReservationLedger(
            self.path, clock_ms=lambda: self.now
        )
        self.assertEqual(
            reopened.get(reserved.idempotency_key).state, DISPATCH_STARTED
        )
        retry = self.claim_dispatch(
            reserved.idempotency_key, ledger=reopened
        )
        self.assertFalse(retry.applied)
        self.assertEqual(retry.reason, "ALREADY_CLAIMED")




    def test_process_death_after_ledger_commit_before_enrollment_release_preserves_claim(self):
        reserved = self.reserve()
        authority_spki = self.authority.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        authority_b64 = base64.urlsafe_b64encode(authority_spki).decode("ascii")
        marker_path = os.path.join(self.temp.name, "ledger-commit-durable")
        command = [
            sys.executable,
            "-c",
            _CRASH_AFTER_LEDGER_COMMIT_SUBPROCESS,
            self.path,
            str(self.registry.path),
            authority_b64,
            reserved.idempotency_key,
            str(self.now),
            marker_path,
        ]
        process = subprocess.Popen(
            command,
            cwd=os.getcwd(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 20.0
            while not os.path.isfile(marker_path):
                if process.poll() is not None:
                    stdout, stderr = process.communicate(timeout=5)
                    self.fail(
                        "claim subprocess exited before durable-commit marker: "
                        f"returncode={process.returncode}, stdout={stdout!r}, "
                        f"stderr={stderr!r}"
                    )
                if time.monotonic() >= deadline:
                    process.kill()
                    stdout, stderr = process.communicate(timeout=5)
                    self.fail(
                        "claim subprocess did not reach post-commit pause: "
                        f"stdout={stdout!r}, stderr={stderr!r}"
                    )
                time.sleep(0.01)

            # Terminate after SQLite committed DISPATCH_STARTED but before the
            # enrollment context exits and before claim_dispatch can return.
            process.kill()
            process.communicate(timeout=10)
            self.assertNotEqual(process.returncode, 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)

        reopened = DurableActionReservationLedger(
            self.path, clock_ms=lambda: self.now
        )
        record = reopened.get(reserved.idempotency_key)
        self.assertEqual(record.state, DISPATCH_STARTED)

        # The killed process must not leave the enrollment writer lock stuck.
        with self.registry.hold_active_enrollment_for_dispatch(
            owner_id=record.owner_id,
            device_id=record.device_id,
            transport_certificate_sha256=record.transport_certificate_sha256,
            credential_generation=record.credential_generation,
            consent_public_key_sha256=record.consent_public_key_sha256,
        ) as status:
            self.assertEqual(status, "ENROLLMENT_ACTIVE")

        retry = reopened.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=lambda: True,
        )
        self.assertFalse(retry.applied)
        self.assertEqual(retry.reason, "ALREADY_CLAIMED")
        self.assertEqual(retry.state, DISPATCH_STARTED)

    def test_process_death_before_ledger_commit_rolls_back_and_allows_one_claim(self):
        reserved = self.reserve()
        authority_spki = self.authority.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        authority_b64 = base64.urlsafe_b64encode(authority_spki).decode("ascii")
        marker_path = os.path.join(self.temp.name, "ledger-commit-not-executed")
        command = [
            sys.executable,
            "-c",
            _CRASH_BEFORE_LEDGER_COMMIT_SUBPROCESS,
            self.path,
            str(self.registry.path),
            authority_b64,
            reserved.idempotency_key,
            str(self.now),
            marker_path,
        ]
        process = subprocess.Popen(
            command,
            cwd=os.getcwd(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 20.0
            while not os.path.isfile(marker_path):
                if process.poll() is not None:
                    stdout, stderr = process.communicate(timeout=5)
                    self.fail(
                        "claim subprocess exited before pre-commit marker: "
                        f"returncode={process.returncode}, stdout={stdout!r}, "
                        f"stderr={stderr!r}"
                    )
                if time.monotonic() >= deadline:
                    process.kill()
                    stdout, stderr = process.communicate(timeout=5)
                    self.fail(
                        "claim subprocess did not reach pre-commit pause: "
                        f"stdout={stdout!r}, stderr={stderr!r}"
                    )
                time.sleep(0.01)

            # The proxy writes this marker before calling the real SQLite
            # COMMIT. The preceding DISPATCH_STARTED UPDATE is still uncommitted.
            self.assertIsNone(process.poll())
            process.kill()
            process.communicate(timeout=10)
            self.assertNotEqual(process.returncode, 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)

        reopened = DurableActionReservationLedger(
            self.path, clock_ms=lambda: self.now
        )
        record = reopened.get(reserved.idempotency_key)
        self.assertEqual(record.state, RESERVED)

        # Process death must release the enrollment writer lock as well as
        # roll back the uncommitted action-ledger transaction.
        with self.registry.hold_active_enrollment_for_dispatch(
            owner_id=record.owner_id,
            device_id=record.device_id,
            transport_certificate_sha256=record.transport_certificate_sha256,
            credential_generation=record.credential_generation,
            consent_public_key_sha256=record.consent_public_key_sha256,
        ) as status:
            self.assertEqual(status, "ENROLLMENT_ACTIVE")

        first = reopened.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=lambda: True,
        )
        self.assertTrue(first.applied)
        self.assertEqual(first.state, DISPATCH_STARTED)

        duplicate = reopened.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=lambda: True,
        )
        self.assertFalse(duplicate.applied)
        self.assertEqual(duplicate.reason, "ALREADY_CLAIMED")
        self.assertEqual(duplicate.state, DISPATCH_STARTED)

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
        self.assertFalse(self.claim_dispatch(reserved.idempotency_key).applied)

    def test_cancel_after_dispatch_is_not_reported_as_cancelled(self):
        reserved = self.reserve()
        self.assertTrue(self.claim_dispatch(reserved.idempotency_key).applied)
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
        self.assertFalse(self.claim_dispatch(reserved.idempotency_key).applied)

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
        self.assertTrue(self.claim_dispatch(reserved.idempotency_key).applied)
        denied = self.ledger.reject_before_dispatch(
            reserved.idempotency_key, reason_code="PERMISSION_REVOKED"
        )
        self.assertFalse(denied.applied)
        self.assertEqual(denied.reason, "DISPATCH_ALREADY_STARTED")

    def test_completed_outcome_is_persisted_and_idempotent(self):
        reserved = self.reserve()
        self.claim_dispatch(reserved.idempotency_key)
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
        self.claim_dispatch(reserved.idempotency_key)
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
        self.claim_dispatch(reserved.idempotency_key)
        self.assertTrue(self.ledger.record_outcome(
            reserved.idempotency_key, state=UNKNOWN_OUTCOME,
            outcome_code="PROCESS_INTERRUPTED",
        ).applied)
        retry = self.claim_dispatch(reserved.idempotency_key)
        self.assertFalse(retry.applied)
        self.assertEqual(retry.reason, "TERMINAL_STATE")
        self.assertEqual(retry.state, UNKNOWN_OUTCOME)

    def test_dispatch_started_survives_restart_without_auto_retry(self):
        reserved = self.reserve()
        self.assertTrue(self.claim_dispatch(reserved.idempotency_key).applied)
        reopened = DurableActionReservationLedger(
            self.path, clock_ms=lambda: self.now
        )
        record = reopened.get(reserved.idempotency_key)
        self.assertEqual(record.state, DISPATCH_STARTED)
        self.assertFalse(self.claim_dispatch(reserved.idempotency_key, ledger=reopened).applied)
        self.assertEqual(
            self.claim_dispatch(reserved.idempotency_key, ledger=reopened).reason,
            "ALREADY_CLAIMED",
        )

    def test_restart_preserves_terminal_outcome_and_replay_binding(self):
        reserved = self.reserve()
        self.claim_dispatch(reserved.idempotency_key)
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
        result = self.claim_dispatch("f" * 64)
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


    def test_final_admission_guard_rejection_leaves_reservation_reserved(self):
        reserved = self.reserve()
        result = self.ledger.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=lambda: False,
        )
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "FINAL_ADMISSION_REJECTED")
        self.assertEqual(result.state, RESERVED)
        self.assertEqual(self.ledger.get(reserved.idempotency_key).state, RESERVED)

    def test_final_admission_guard_exception_fails_closed(self):
        reserved = self.reserve()

        def broken_guard():
            raise RuntimeError("synthetic guard failure")

        result = self.ledger.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=broken_guard,
        )
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "FINAL_ADMISSION_REJECTED")
        self.assertEqual(self.ledger.get(reserved.idempotency_key).state, RESERVED)

    def test_dispatch_claim_requires_explicit_final_admission_guard(self):
        reserved = self.reserve()
        with self.assertRaises(TypeError):
            self.ledger.claim_dispatch(
                reserved.idempotency_key, enrollment_registry=self.registry
            )

        result = self.ledger.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=None,
        )
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "INVALID_FINAL_ADMISSION_GUARD")
        self.assertIsNone(result.state)  # Rejected before loading the reservation row.
        self.assertEqual(self.ledger.get(reserved.idempotency_key).state, RESERVED)

    def test_dispatch_claim_rejects_non_boolean_final_admission_result(self):
        reserved = self.reserve()
        result = self.ledger.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=lambda: 1,
        )
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "FINAL_ADMISSION_REJECTED")
        self.assertEqual(result.state, RESERVED)
    def test_ledger_commit_ack_loss_is_not_replayed_after_restart(self):
        reserved = self.reserve()
        original_connect = self.ledger._connect
        self.ledger._connect = lambda: _CommitAcknowledgementLostConnection(
            original_connect()
        )
        try:
            claim = self.ledger.claim_dispatch(
                reserved.idempotency_key,
                enrollment_registry=self.registry,
                final_admission_guard=lambda: True,
            )
        finally:
            self.ledger._connect = original_connect

        # The API reports uncertainty using its pre-claim snapshot, while the
        # SQLite COMMIT actually succeeded. Recovery must inspect durable state.
        self.assertFalse(claim.applied)
        self.assertEqual(claim.reason, "RESERVATION_STORE_UNAVAILABLE")
        self.assertEqual(claim.state, RESERVED)

        reopened = DurableActionReservationLedger(
            self.path, clock_ms=lambda: self.now
        )
        self.assertEqual(
            reopened.get(reserved.idempotency_key).state, DISPATCH_STARTED
        )
        retry = reopened.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=lambda: True,
        )
        self.assertFalse(retry.applied)
        self.assertEqual(retry.reason, "ALREADY_CLAIMED")

        unknown = reopened.record_outcome(
            reserved.idempotency_key,
            state=UNKNOWN_OUTCOME,
            outcome_code="LEDGER_COMMIT_ACK_LOST",
        )
        self.assertTrue(unknown.applied)
        self.assertEqual(
            reopened.get(reserved.idempotency_key).state, UNKNOWN_OUTCOME
        )
        replay = reopened.reserve(self.request())
        self.assertFalse(replay.applied)
        self.assertEqual(replay.reason, "IDEMPOTENT_REPLAY")
        self.assertEqual(replay.state, UNKNOWN_OUTCOME)
        self.assertEqual(
            reopened.claim_dispatch(
                reserved.idempotency_key,
                enrollment_registry=self.registry,
                final_admission_guard=lambda: True,
            ).reason,
            "TERMINAL_STATE",
        )

    def test_enrollment_commit_ack_loss_is_reported_after_ledger_claim(self):
        reserved = self.reserve()
        original_connect = self.registry._connect
        self.registry._connect = lambda: _CommitAcknowledgementLostConnection(
            original_connect()
        )
        try:
            claim = self.ledger.claim_dispatch(
                reserved.idempotency_key,
                enrollment_registry=self.registry,
                final_admission_guard=lambda: True,
            )
        finally:
            self.registry._connect = original_connect

        # The enrollment context's COMMIT acknowledgement is lost only after
        # the action-ledger DISPATCH_STARTED commit has already succeeded.
        self.assertFalse(claim.applied)
        self.assertEqual(claim.reason, "ENROLLMENT_LOCK_COMMIT_UNCERTAIN")
        self.assertEqual(claim.state, DISPATCH_STARTED)
        self.assertEqual(
            self.ledger.get(reserved.idempotency_key).state, DISPATCH_STARTED
        )

        reopened = DurableActionReservationLedger(
            self.path, clock_ms=lambda: self.now
        )
        retry = reopened.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=lambda: True,
        )
        self.assertFalse(retry.applied)
        self.assertEqual(retry.reason, "ALREADY_CLAIMED")
        self.assertEqual(
            reopened.get(reserved.idempotency_key).state, DISPATCH_STARTED
        )

    def test_outcome_commit_ack_loss_preserves_terminal_unknown_state(self):
        reserved = self.reserve()
        self.assertTrue(self.claim_dispatch(reserved.idempotency_key).applied)
        original_connect = self.ledger._connect
        self.ledger._connect = lambda: _CommitAcknowledgementLostConnection(
            original_connect()
        )
        try:
            with self.assertRaises(ReservationStoreUnavailable):
                self.ledger.record_outcome(
                    reserved.idempotency_key,
                    state=UNKNOWN_OUTCOME,
                    outcome_code="OUTCOME_COMMIT_ACK_LOST",
                )
        finally:
            self.ledger._connect = original_connect

        reopened = DurableActionReservationLedger(
            self.path, clock_ms=lambda: self.now
        )
        self.assertEqual(
            reopened.get(reserved.idempotency_key).state, UNKNOWN_OUTCOME
        )
        duplicate = reopened.record_outcome(
            reserved.idempotency_key,
            state=UNKNOWN_OUTCOME,
            outcome_code="OUTCOME_COMMIT_ACK_LOST",
        )
        self.assertTrue(duplicate.applied)
        self.assertEqual(duplicate.reason, "OUTCOME_ALREADY_RECORDED")
        retry = reopened.claim_dispatch(
            reserved.idempotency_key,
            enrollment_registry=self.registry,
            final_admission_guard=lambda: True,
        )
        self.assertFalse(retry.applied)
        self.assertEqual(retry.reason, "TERMINAL_STATE")


if __name__ == "__main__":
    unittest.main()
