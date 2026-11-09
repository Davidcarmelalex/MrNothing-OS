from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "android/app/src/main/java/tech/mrnothing/os/OwnerAttestationChainGate.kt"

class AttestationChainGateSourceTests(unittest.TestCase):
    def test_fail_closed_without_trust_roots(self):
        code = SOURCE.read_text()
        self.assertIn("trustedRoots.isEmpty()", code)
        self.assertIn("chain.isEmpty()", code)
        self.assertIn("CertPathValidator.getInstance(\"PKIX\")", code)

    def test_rejects_embedded_trust_anchor(self):
        code = SOURCE.read_text()
        self.assertIn("chain.dropLast(1).any { it in trustedRoots }", code)
        self.assertIn("if (pathCertificates.isEmpty()) return false", code)

    def test_no_authorization_or_implicit_remote_trust(self):
        code = SOURCE.read_text()
        self.assertIn("parameters.isRevocationEnabled = false", code)
        self.assertIn("cannot authorize agent actions", code)
        self.assertNotIn("PURPOSE_SIGN", code)
