"""AGENT-004D: real local mTLS socket tests; no public listener or device actions."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import os
import socket
import ssl
import tempfile
import time
import unittest

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from core.owner_consent_issuer import EnrolledOwnerDevice
from core.owner_consent_transport import (
    EnrolledTransportCertificate,
    OWNER_CONSENT_ALPN,
    OwnerConsentTlsAdapter,
)


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

    def lookup_active_device(self, device_id):
        if self.fail:
            raise OSError("registry unavailable")
        if self.record is None or self.record.device_id != device_id:
            return None
        return self.record


class OwnerConsentTlsAdapterTests(unittest.TestCase):
    NOW = int(time.time() * 1000)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
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
            clock_ms=lambda: self.NOW,
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


if __name__ == "__main__":
    unittest.main()
