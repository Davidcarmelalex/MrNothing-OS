"""AGENT-004D: real local mTLS socket tests; no public listener or device actions."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import json
import os
import socket
import ssl
import tempfile
import time
import threading
import unittest

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from core.owner_consent_issuer import EnrolledOwnerDevice
from core.owner_consent_protocol import canonical_payload
from core.owner_consent_transport import (
    EnrolledTransportCertificate,
    OWNER_CONSENT_ALPN,
    OwnerConsentTlsAdapter,
    VerifiedOwnerActionCapability,
)
from core.noop_action_executor import NoOpActionExecutor


class _TransportRegistry:
    def __init__(self, record=None, *, fail=False):
        self.record = record
        self.fail = fail

    def lookup_active_certificate(self, certificate_sha256):
        if self.fail:
            raise OSError("registry unavailable")
        if self.record is None or self.record.certificate_sha256 != certificate_sha256:
            return None
        return self.record


class _ConsentRegistry:
    def __init__(self, record=None, *, fail=False):
        self.record = record
        self.fail = fail
        self.seen = set()
        self.lock = threading.Lock()

    def lookup_active_device(self, device_id):
        if self.fail:
            raise OSError("registry unavailable")
        if self.record is None or self.record.device_id != device_id:
            return None
        return self.record

    def consume_consent_nonce(self, *, owner_id, device_id, nonce,
                              transport_certificate_sha256, credential_generation,
                              consent_public_key_spki_der, now_epoch_ms):
        if self.fail:
            raise OSError("registry unavailable")
        record = self.record
        if record is None or record.active is not True:
            return "ENROLLMENT_NOT_ACTIVE"
        if record.owner_id != owner_id or record.device_id != device_id:
            return "ENROLLMENT_IDENTITY_MISMATCH"
        if (record.transport_certificate_sha256 != transport_certificate_sha256
                or record.credential_generation != credential_generation):
            return "ENROLLMENT_CREDENTIAL_MISMATCH"
        if record.public_key_spki_der != consent_public_key_spki_der:
            return "ENROLLMENT_KEY_MISMATCH"
        with self.lock:
            marker = (device_id, nonce)
            if marker in self.seen:
                return "REPLAY_OR_CAPACITY"
            self.seen.add(marker)
        return "ADMITTED"


class OwnerConsentTlsAdapterTests(unittest.TestCase):
    NOW = int(time.time() * 1000)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.now = [self.NOW]
        self.monotonic_now = [time.monotonic_ns()]
        self.paths = self._make_certificates()
        self.server_context = self._server_context()
        self.client_context = self._client_context()
        self.client_der = self.paths["client_cert"].public_bytes(
            serialization.Encoding.DER
        )
        self.fingerprint = hashlib.sha256(self.client_der).hexdigest()
        self.consent_private = ec.generate_private_key(ec.SECP256R1())
        self.consent_public_der = self.consent_private.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.consent_record = EnrolledOwnerDevice(
            owner_id="owner-1",
            device_id="pixel9pro-1",
            public_key_spki_der=self.consent_public_der,
            transport_certificate_sha256=self.fingerprint,
            credential_generation=1,
        )
        self.transport_record = EnrolledTransportCertificate(
            owner_id="owner-1",
            device_id="pixel9pro-1",
            certificate_sha256=self.fingerprint,
            credential_generation=1,
        )
        self.transport_registry = _TransportRegistry(self.transport_record)
        self.consent_registry = _ConsentRegistry(self.consent_record)
        self.adapter = OwnerConsentTlsAdapter(
            server_context=self.server_context,
            transport_registry=self.transport_registry,
            consent_registry=self.consent_registry,
            clock_ms=lambda: self.now[0],
            monotonic_ns=lambda: self.monotonic_now[0],
            session_id_factory=lambda size: "a" * (size * 2),
            nonce_factory=lambda size: "b" * (size * 2),
        )

    def tearDown(self):
        self.temp.cleanup()

    def _write(self, name, data):
        path = os.path.join(self.temp.name, name)
        with open(path, "wb") as output:
            output.write(data)
        return path

    def _make_cert(
        self, *, subject, public_key, issuer, issuer_key, ca, eku,
        san=None, valid_from=None, valid_to=None,
    ):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(valid_from or (now - timedelta(minutes=5)))
            .not_valid_after(valid_to or (now + timedelta(days=2)))
            .add_extension(
                x509.BasicConstraints(ca=ca, path_length=1 if ca else None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=ca,
                    crl_sign=ca,
                    encipher_only=None,
                    decipher_only=None,
                ),
                critical=True,
            )
        )
        if eku:
            builder = builder.add_extension(x509.ExtendedKeyUsage(eku), critical=False)
        if san:
            builder = builder.add_extension(x509.SubjectAlternativeName(san), critical=False)
        return builder.sign(issuer_key, hashes.SHA256())

    def _make_certificates(
        self,
        *,
        client_curve=ec.SECP256R1(),
        client_eku=(ExtendedKeyUsageOID.CLIENT_AUTH,),
        client_ca=False,
    ):
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "MrNothing Test CA")
        ])
        ca_cert = self._make_cert(
            subject=ca_name,
            public_key=ca_key.public_key(),
            issuer=ca_name,
            issuer_key=ca_key,
            ca=True,
            eku=None,
        )
        server_key = ec.generate_private_key(ec.SECP256R1())
        server_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost")
        ])
        server_cert = self._make_cert(
            subject=server_name,
            public_key=server_key.public_key(),
            issuer=ca_name,
            issuer_key=ca_key,
            ca=False,
            eku=(ExtendedKeyUsageOID.SERVER_AUTH,),
            san=(x509.DNSName("localhost"),),
        )
        client_key = ec.generate_private_key(client_curve)
        client_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "pixel9pro-1")
        ])
        client_cert = self._make_cert(
            subject=client_name,
            public_key=client_key.public_key(),
            issuer=ca_name,
            issuer_key=ca_key,
            ca=client_ca,
            eku=client_eku,
        )
        return {
            "ca_pem": self._write(
                "ca.pem", ca_cert.public_bytes(serialization.Encoding.PEM)
            ),
            "server_cert_pem": self._write(
                "server.pem", server_cert.public_bytes(serialization.Encoding.PEM)
            ),
            "server_key_pem": self._write(
                "server-key.pem",
                server_key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                ),
            ),
            "client_cert_pem": self._write(
                "client.pem", client_cert.public_bytes(serialization.Encoding.PEM)
            ),
            "client_key_pem": self._write(
                "client-key.pem",
                client_key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                ),
            ),
            "client_cert": client_cert,
        }

    def _server_context(
        self, *, alpn=OWNER_CONSENT_ALPN, verify_mode=ssl.CERT_REQUIRED
    ):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.verify_mode = verify_mode
        context.options |= ssl.OP_NO_COMPRESSION
        context.load_cert_chain(
            self.paths["server_cert_pem"], self.paths["server_key_pem"]
        )
        context.load_verify_locations(cafile=self.paths["ca_pem"])
        context.set_alpn_protocols([alpn])
        return context

    def _client_context(
        self, *, include_certificate=True, alpn=OWNER_CONSENT_ALPN
    ):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=self.paths["ca_pem"])
        if include_certificate:
            context.load_cert_chain(
                self.paths["client_cert_pem"], self.paths["client_key_pem"]
            )
        context.set_alpn_protocols([alpn])
        return context

    def _pair(self, *, server_context=None, client_context=None):
        server_context = server_context or self.server_context
        client_context = client_context or self.client_context
        raw_server, raw_client = socket.socketpair()
        server = server_context.wrap_socket(
            raw_server, server_side=True, do_handshake_on_connect=False
        )
        client = client_context.wrap_socket(
            raw_client, server_hostname="localhost", do_handshake_on_connect=False
        )
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                server_future = pool.submit(server.do_handshake)
                client_future = pool.submit(client.do_handshake)
                server_future.result(timeout=8)
                client_future.result(timeout=8)
        except Exception:
            server.close()
            client.close()
            raise
        return server, client

    def test_valid_mtls_peer_issues_owner_bound_short_challenge(self):
        server, client = self._pair()
        try:
            result = self.adapter.issue_challenge(server, action="read_screen")
            self.assertTrue(result.issued, result.reason)
            challenge = result.capability.challenge
            self.assertEqual(challenge.owner_id, "owner-1")
            self.assertEqual(challenge.device_id, "pixel9pro-1")
            self.assertEqual(challenge.action, "read_screen")
            self.assertEqual(challenge.session_id, "a" * 32)
            self.assertEqual(challenge.nonce, "b" * 32)
            self.assertLessEqual(
                challenge.expires_at_epoch_ms - challenge.issued_at_epoch_ms,
                30_000,
            )
        finally:
            server.close()
            client.close()

    def test_exact_server_context_and_alpn_are_required(self):
        server, client = self._pair()
        try:
            adapter = OwnerConsentTlsAdapter(
                server_context=self._server_context(),
                transport_registry=self.transport_registry,
                consent_registry=self.consent_registry,
                clock_ms=lambda: self.NOW,
            )
            self.assertEqual(
                adapter.issue_challenge(server, action="read_screen").reason,
                "TLS_CONTEXT_NOT_STRICT",
            )
        finally:
            server.close()
            client.close()

        server, client = self._pair(
            server_context=self._server_context(alpn="unrelated/1"),
            client_context=self._client_context(alpn="unrelated/1"),
        )
        try:
            adapter = OwnerConsentTlsAdapter(
                server_context=server.context,
                transport_registry=self.transport_registry,
                consent_registry=self.consent_registry,
                clock_ms=lambda: self.NOW,
            )
            self.assertEqual(
                adapter.issue_challenge(server, action="read_screen").reason,
                "ALPN_MISMATCH",
            )
        finally:
            server.close()
            client.close()

    def test_certificate_fingerprint_must_be_enrolled_and_active(self):
        server, client = self._pair()
        try:
            self.transport_registry.record = None
            self.assertEqual(
                self.adapter.issue_challenge(server, action="read_screen").reason,
                "TRANSPORT_CERT_NOT_ENROLLED",
            )
            self.transport_registry.record = EnrolledTransportCertificate(
                "owner-1", "pixel9pro-1", self.fingerprint, active=False,
                credential_generation=1,
            )
            self.assertEqual(
                self.adapter.issue_challenge(server, action="read_screen").reason,
                "TRANSPORT_CERT_REVOKED",
            )
        finally:
            server.close()
            client.close()

    def test_revocation_is_rechecked_for_each_challenge(self):
        server, client = self._pair()
        try:
            first = self.adapter.issue_challenge(server, action="read_screen")
            self.assertTrue(first.issued)
            self.transport_registry.record = EnrolledTransportCertificate(
                "owner-1", "pixel9pro-1", self.fingerprint, active=False,
                credential_generation=1,
            )
            second = self.adapter.issue_challenge(server, action="read_screen")
            self.assertEqual(second.reason, "TRANSPORT_CERT_REVOKED")
        finally:
            server.close()
            client.close()

    def test_transport_registry_errors_fail_closed(self):
        server, client = self._pair()
        try:
            self.transport_registry.fail = True
            self.assertEqual(
                self.adapter.issue_challenge(server, action="read_screen").reason,
                "TRANSPORT_REGISTRY_UNAVAILABLE",
            )
        finally:
            server.close()
            client.close()

    def test_wrong_curve_client_certificate_is_rejected(self):
        self.paths = self._make_certificates(client_curve=ec.SECP384R1())
        server_context = self._server_context()
        client_context = self._client_context()
        server, client = self._pair(
            server_context=server_context,
            client_context=client_context,
        )
        try:
            adapter = OwnerConsentTlsAdapter(
                server_context=server_context,
                transport_registry=self.transport_registry,
                consent_registry=self.consent_registry,
                clock_ms=lambda: self.NOW,
            )
            self.assertEqual(
                adapter.issue_challenge(server, action="read_screen").reason,
                "PEER_CERT_KEY_UNSUPPORTED",
            )
        finally:
            server.close()
            client.close()

    def test_closed_socket_is_rejected(self):
        server, client = self._pair()
        server.close()
        client.close()
        self.assertEqual(
            self.adapter.issue_challenge(server, action="read_screen").reason,
            "TLS_SOCKET_CLOSED",
        )

    def test_server_handshake_rejects_missing_client_certificate(self):
        with self.assertRaises(Exception):
            self._pair(client_context=self._client_context(include_certificate=False))

    def test_optional_client_certificate_context_is_rejected(self):
        server_context = self._server_context(verify_mode=ssl.CERT_OPTIONAL)
        server, client = self._pair(server_context=server_context)
        try:
            adapter = OwnerConsentTlsAdapter(
                server_context=server_context,
                transport_registry=self.transport_registry,
                consent_registry=self.consent_registry,
                clock_ms=lambda: self.NOW,
            )
            self.assertEqual(
                adapter.issue_challenge(server, action="read_screen").reason,
                "TLS_CONTEXT_NOT_STRICT",
            )
        finally:
            server.close()
            client.close()

    def test_invalid_clock_fails_closed(self):
        server, client = self._pair()
        try:
            adapter = OwnerConsentTlsAdapter(
                server_context=self.server_context,
                transport_registry=self.transport_registry,
                consent_registry=self.consent_registry,
                clock_ms=lambda: True,
            )
            self.assertEqual(
                adapter.issue_challenge(server, action="read_screen").reason,
                "INVALID_CLOCK",
            )
        finally:
            server.close()
            client.close()

    def test_consent_registry_owner_mismatch_fails_closed(self):
        server, client = self._pair()
        try:
            self.consent_registry.record = EnrolledOwnerDevice(
                owner_id="different-owner",
                device_id="pixel9pro-1",
                public_key_spki_der=self.consent_public_der,
            )
            self.assertEqual(
                self.adapter.issue_challenge(server, action="read_screen").reason,
                "OWNER_DEVICE_MISMATCH",
            )
        finally:
            server.close()
            client.close()


    def _signed_envelope(self, challenge):
        signature = self.consent_private.sign(
            canonical_payload(challenge), ec.ECDSA(hashes.SHA256())
        )
        encoded = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
        payload = json.loads(canonical_payload(challenge).decode("ascii"))
        return json.dumps(
            {"payload": payload, "signature": encoded},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")

    def test_live_tls_socket_admits_once_without_caller_authentication_flag(self):
        server, client = self._pair()
        try:
            issued = self.adapter.issue_challenge(server, action="read_screen")
            self.assertTrue(issued.issued, issued.reason)
            challenge = issued.capability.challenge
            envelope = self._signed_envelope(challenge)
            result = self.adapter.verify_and_consume(server, envelope, challenge)
            self.assertTrue(result.admitted, result.reason)
            self.assertEqual(result.reason, "ADMITTED_NO_EXECUTION")
            self.assertEqual(
                result.verified_public_key_sha256,
                hashlib.sha256(self.consent_public_der).hexdigest(),
            )
            replay = self.adapter.verify_and_consume(server, envelope, challenge)
            self.assertFalse(replay.admitted)
            self.assertEqual(replay.reason, "REPLAY_OR_CAPACITY")
        finally:
            server.close()
            client.close()

    def test_v2_live_mtls_consent_binds_arguments_but_does_not_mint_capability(self):
        server, client = self._pair()
        try:
            arguments = {"target_package": "com.example.notes"}
            issued = self.adapter.issue_challenge(server, action="navigate", arguments=arguments)
            self.assertTrue(issued.issued, issued.reason)
            challenge = issued.capability.challenge
            self.assertEqual(challenge.version, 2)
            envelope = self._signed_envelope(challenge)
            capability = self.adapter.verify_and_issue_capability(
                server, envelope, challenge, arguments=arguments
            )
            self.assertFalse(capability.issued)
            self.assertEqual(capability.reason, "V2_CAPABILITY_NOT_INTEGRATED")
            admitted = self.adapter.verify_and_consume(server, envelope, challenge)
            self.assertTrue(admitted.admitted, admitted.reason)
            replay = self.adapter.verify_and_consume(server, envelope, challenge)
            self.assertEqual(replay.reason, "REPLAY_OR_CAPACITY")
        finally:
            server.close()
            client.close()

    def test_challenge_cannot_be_transferred_to_another_tls_socket(self):
        server1, client1 = self._pair()
        server2, client2 = self._pair()
        try:
            issued = self.adapter.issue_challenge(server1, action="read_screen")
            self.assertTrue(issued.issued, issued.reason)
            result = self.adapter.verify_and_consume(
                server2,
                self._signed_envelope(issued.capability.challenge),
                issued.capability.challenge,
            )
            self.assertFalse(result.admitted)
            self.assertEqual(result.reason, "TRANSPORT_SESSION_NOT_ISSUED")
        finally:
            server1.close()
            client1.close()
            server2.close()
            client2.close()

    def test_modified_session_id_and_unissued_challenge_are_rejected(self):
        server, client = self._pair()
        try:
            issued = self.adapter.issue_challenge(server, action="read_screen")
            self.assertTrue(issued.issued, issued.reason)
            altered = replace(issued.capability.challenge, session_id="other-session")
            result = self.adapter.verify_and_consume(
                server, self._signed_envelope(altered), altered
            )
            self.assertFalse(result.admitted)
            self.assertEqual(result.reason, "CHALLENGE_NOT_ISSUED_ON_SESSION")
        finally:
            server.close()
            client.close()

    def test_expired_monotonic_session_is_not_revived_by_wall_clock_rollback(self):
        server, client = self._pair()
        try:
            issued = self.adapter.issue_challenge(server, action="read_screen")
            self.assertTrue(issued.issued, issued.reason)
            envelope = self._signed_envelope(issued.capability.challenge)
            self.monotonic_now[0] += 31_000_000_000
            self.now[0] -= 1_000
            result = self.adapter.verify_and_consume(
                server, envelope, issued.capability.challenge
            )
            self.assertFalse(result.admitted)
            self.assertEqual(result.reason, "TRANSPORT_SESSION_EXPIRED")
        finally:
            server.close()
            client.close()

    def test_transport_certificate_revocation_after_issuance_blocks_verification(self):
        server, client = self._pair()
        try:
            issued = self.adapter.issue_challenge(server, action="read_screen")
            self.assertTrue(issued.issued, issued.reason)
            self.transport_registry.record = replace(
                self.transport_record, active=False
            )
            result = self.adapter.verify_and_consume(
                server,
                self._signed_envelope(issued.capability.challenge),
                issued.capability.challenge,
            )
            self.assertFalse(result.admitted)
            self.assertEqual(result.reason, "TRANSPORT_CERT_REVOKED")
        finally:
            server.close()
            client.close()

    def test_transport_generation_change_invalidates_existing_tls_session(self):
        server, client = self._pair()
        try:
            issued = self.adapter.issue_challenge(server, action="read_screen")
            self.assertTrue(issued.issued, issued.reason)
            self.transport_registry.record = replace(
                self.transport_record, credential_generation=2
            )
            result = self.adapter.verify_and_consume(
                server,
                self._signed_envelope(issued.capability.challenge),
                issued.capability.challenge,
            )
            self.assertFalse(result.admitted)
            self.assertEqual(result.reason, "TRANSPORT_CREDENTIAL_CHANGED")
        finally:
            server.close()
            client.close()

    def test_closed_socket_after_challenge_issuance_is_rejected(self):
        server, client = self._pair()
        issued = self.adapter.issue_challenge(server, action="read_screen")
        self.assertTrue(issued.issued, issued.reason)
        envelope = self._signed_envelope(issued.capability.challenge)
        server.close()
        client.close()
        result = self.adapter.verify_and_consume(
            server, envelope, issued.capability.challenge
        )
        self.assertFalse(result.admitted)
        self.assertEqual(result.reason, "TLS_SOCKET_CLOSED")

    def test_consent_registry_outage_during_verification_fails_closed(self):
        server, client = self._pair()
        try:
            issued = self.adapter.issue_challenge(server, action="read_screen")
            self.assertTrue(issued.issued, issued.reason)
            self.consent_registry.fail = True
            result = self.adapter.verify_and_consume(
                server,
                self._signed_envelope(issued.capability.challenge),
                issued.capability.challenge,
            )
            self.assertFalse(result.admitted)
            self.assertEqual(result.reason, "ENROLLMENT_REGISTRY_UNAVAILABLE")
        finally:
            server.close()
            client.close()

    def test_adapter_verifier_signature_has_no_authentication_boolean_or_snapshots(self):
        import inspect
        parameters = tuple(inspect.signature(self.adapter.verify_and_consume).parameters)
        self.assertEqual(parameters, ("peer", "envelope", "challenge"))


    def _issue_read_screen_capability(self, server):
        issued = self.adapter.issue_challenge(server, action="read_screen")
        self.assertTrue(issued.issued, issued.reason)
        challenge = issued.capability.challenge
        result = self.adapter.verify_and_issue_capability(
            server,
            self._signed_envelope(challenge),
            challenge,
            arguments={},
        )
        self.assertTrue(result.issued, result.reason)
        self.assertIsNotNone(result.capability)
        return result.capability, challenge

    def test_opaque_capability_is_one_use_and_noop_only(self):
        server, client = self._pair()
        try:
            capability, _challenge = self._issue_read_screen_capability(server)
            executor = NoOpActionExecutor(self.adapter)
            result = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertTrue(result.accepted, result.reason)
            self.assertEqual(result.reason, "SIMULATED_ONLY")
            self.assertTrue(result.simulated)
            self.assertFalse(result.device_actions_executed)

            replay = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertFalse(replay.accepted)
            self.assertEqual(replay.reason, "CAPABILITY_NOT_ACTIVE")
            self.assertFalse(replay.device_actions_executed)
        finally:
            server.close()
            client.close()

    def test_v1_refuses_nonempty_arguments_without_consuming_owner_consent(self):
        server, client = self._pair()
        try:
            issued = self.adapter.issue_challenge(server, action="read_screen")
            self.assertTrue(issued.issued, issued.reason)
            challenge = issued.capability.challenge
            envelope = self._signed_envelope(challenge)

            rejected = self.adapter.verify_and_issue_capability(
                server, envelope, challenge, arguments={"query": "private"}
            )
            self.assertFalse(rejected.issued)
            self.assertEqual(rejected.reason, "ARGUMENTS_NOT_SUPPORTED_BY_V1")

            accepted = self.adapter.verify_and_issue_capability(
                server, envelope, challenge, arguments={}
            )
            self.assertTrue(accepted.issued, accepted.reason)
        finally:
            server.close()
            client.close()

    def test_argument_or_action_mismatch_does_not_consume_valid_capability(self):
        server, client = self._pair()
        try:
            capability, _challenge = self._issue_read_screen_capability(server)
            executor = NoOpActionExecutor(self.adapter)

            wrong_arguments = executor.simulate(
                server,
                capability,
                action="read_screen",
                arguments={"text": "not in signed consent"},
            )
            self.assertFalse(wrong_arguments.accepted)
            self.assertEqual(wrong_arguments.reason, "ARGUMENTS_MISMATCH")

            wrong_action = executor.simulate(
                server, capability, action="navigate", arguments={}
            )
            self.assertFalse(wrong_action.accepted)
            self.assertEqual(wrong_action.reason, "ACTION_MISMATCH")

            correct = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertTrue(correct.accepted, correct.reason)
            self.assertFalse(correct.device_actions_executed)
        finally:
            server.close()
            client.close()

    def test_caller_constructed_capability_cannot_substitute_for_adapter_handle(self):
        server, client = self._pair()
        try:
            capability, _challenge = self._issue_read_screen_capability(server)
            executor = NoOpActionExecutor(self.adapter)
            forged = VerifiedOwnerActionCapability()
            rejected = executor.simulate(
                server, forged, action="read_screen", arguments={}
            )
            self.assertFalse(rejected.accepted)
            self.assertEqual(rejected.reason, "CAPABILITY_NOT_ACTIVE")

            accepted = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertTrue(accepted.accepted, accepted.reason)
        finally:
            server.close()
            client.close()

    def test_capability_cannot_move_to_another_live_tls_socket(self):
        server1, client1 = self._pair()
        server2, client2 = self._pair()
        try:
            capability, _challenge = self._issue_read_screen_capability(server1)
            executor = NoOpActionExecutor(self.adapter)
            rejected = executor.simulate(
                server2, capability, action="read_screen", arguments={}
            )
            self.assertFalse(rejected.accepted)
            self.assertEqual(rejected.reason, "CAPABILITY_SESSION_NOT_FOUND")

            accepted = executor.simulate(
                server1, capability, action="read_screen", arguments={}
            )
            self.assertTrue(accepted.accepted, accepted.reason)
        finally:
            server1.close()
            client1.close()
            server2.close()
            client2.close()

    def test_transport_revocation_discards_issued_capability(self):
        server, client = self._pair()
        try:
            capability, _challenge = self._issue_read_screen_capability(server)
            self.transport_registry.record = replace(
                self.transport_record, active=False
            )
            executor = NoOpActionExecutor(self.adapter)
            rejected = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertFalse(rejected.accepted)
            self.assertEqual(rejected.reason, "TRANSPORT_CERT_REVOKED")

            self.transport_registry.record = self.transport_record
            replay = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertFalse(replay.accepted)
            self.assertEqual(replay.reason, "CAPABILITY_NOT_ACTIVE")
        finally:
            server.close()
            client.close()

    def test_consent_key_rotation_discards_issued_capability(self):
        server, client = self._pair()
        try:
            capability, _challenge = self._issue_read_screen_capability(server)
            self.consent_registry.record = replace(
                self.consent_record, public_key_spki_der=b"\x30\x00"
            )
            executor = NoOpActionExecutor(self.adapter)
            rejected = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertFalse(rejected.accepted)
            self.assertEqual(rejected.reason, "ENROLLMENT_KEY_MISMATCH")
        finally:
            server.close()
            client.close()

    def test_expired_capability_is_discarded_using_monotonic_time(self):
        server, client = self._pair()
        try:
            capability, _challenge = self._issue_read_screen_capability(server)
            self.monotonic_now[0] += 31_000_000_000
            executor = NoOpActionExecutor(self.adapter)
            rejected = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertFalse(rejected.accepted)
            self.assertEqual(rejected.reason, "CAPABILITY_EXPIRED")
        finally:
            server.close()
            client.close()

    def test_consent_registry_outage_fails_closed_without_consuming_capability(self):
        server, client = self._pair()
        try:
            capability, _challenge = self._issue_read_screen_capability(server)
            self.consent_registry.fail = True
            executor = NoOpActionExecutor(self.adapter)
            rejected = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertFalse(rejected.accepted)
            self.assertEqual(rejected.reason, "ENROLLMENT_REGISTRY_UNAVAILABLE")

            self.consent_registry.fail = False
            accepted = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertTrue(accepted.accepted, accepted.reason)
            self.assertFalse(accepted.device_actions_executed)
        finally:
            server.close()
            client.close()

    def test_enrollment_revocation_discards_issued_capability(self):
        server, client = self._pair()
        try:
            capability, _challenge = self._issue_read_screen_capability(server)
            self.consent_registry.record = replace(
                self.consent_record, active=False
            )
            executor = NoOpActionExecutor(self.adapter)
            rejected = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertFalse(rejected.accepted)
            self.assertEqual(rejected.reason, "DEVICE_NOT_ACTIVE")
        finally:
            server.close()
            client.close()


    def test_key_rotation_after_signature_and_nonce_verification_blocks_capability_mint(self):
        server, client = self._pair()
        try:
            issued = self.adapter.issue_challenge(server, action="read_screen")
            self.assertTrue(issued.issued, issued.reason)
            challenge = issued.capability.challenge
            envelope = self._signed_envelope(challenge)
            original_consume = self.consent_registry.consume_consent_nonce

            def consume_then_rotate(**kwargs):
                outcome = original_consume(**kwargs)
                self.consent_registry.record = replace(
                    self.consent_record, public_key_spki_der=b"\x30\x00"
                )
                return outcome

            self.consent_registry.consume_consent_nonce = consume_then_rotate
            result = self.adapter.verify_and_issue_capability(
                server, envelope, challenge, arguments={}
            )
            self.assertFalse(result.issued)
            self.assertIsNone(result.capability)
            self.assertEqual(
                result.reason, "ENROLLMENT_KEY_CHANGED_DURING_ADMISSION"
            )
        finally:
            server.close()
            client.close()

    def test_transport_owner_or_device_rebind_discards_issued_capability(self):
        for index, changes in enumerate((
            {"owner_id": "other-owner"},
            {"device_id": "other-device"},
        )):
            # The fixture nonce registry is persistent across this loop; use
            # a distinct deterministic nonce for each independent socket case.
            marker = "b" if index == 0 else "c"
            self.adapter._nonce_factory = (
                lambda size, marker=marker: marker * (size * 2)
            )
            server, client = self._pair()
            try:
                capability, _challenge = self._issue_read_screen_capability(server)
                self.transport_registry.record = replace(
                    self.transport_record, **changes
                )
                executor = NoOpActionExecutor(self.adapter)
                rejected = executor.simulate(
                    server, capability, action="read_screen", arguments={}
                )
                self.assertFalse(rejected.accepted)
                self.assertEqual(
                    rejected.reason, "CAPABILITY_CONTEXT_MISMATCH"
                )
            finally:
                self.transport_registry.record = self.transport_record
                server.close()
                client.close()

    def test_transport_generation_change_after_capability_mint_discards_it(self):
        server, client = self._pair()
        try:
            capability, _challenge = self._issue_read_screen_capability(server)
            self.transport_registry.record = replace(
                self.transport_record, credential_generation=2
            )
            executor = NoOpActionExecutor(self.adapter)
            rejected = executor.simulate(
                server, capability, action="read_screen", arguments={}
            )
            self.assertFalse(rejected.accepted)
            self.assertEqual(rejected.reason, "TRANSPORT_CREDENTIAL_CHANGED")
        finally:
            server.close()
            client.close()


if __name__ == "__main__":
    unittest.main()
