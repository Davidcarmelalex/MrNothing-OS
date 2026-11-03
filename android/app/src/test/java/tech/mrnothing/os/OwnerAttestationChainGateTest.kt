package tech.mrnothing.os

import java.security.cert.CertificateFactory
import java.security.cert.X509Certificate
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Synthetic, offline PKIX regression fixtures. Not production trust roots. */
class OwnerAttestationChainGateTest {
    private fun cert(name: String): X509Certificate {
        val stream = requireNotNull(javaClass.getResourceAsStream("/attestation/$name.pem"))
        return stream.use {
            CertificateFactory.getInstance("X.509").generateCertificate(it) as X509Certificate
        }
    }

    @Test fun trustedSignedLeafSucceedsWithRootAppended() {
        assertTrue(OwnerAttestationChainGate.validatesPath(listOf(cert("leaf"), cert("root")), setOf(cert("root"))))
    }

    @Test fun trustedSignedLeafSucceedsWithoutRootAppended() {
        assertTrue(OwnerAttestationChainGate.validatesPath(listOf(cert("leaf")), setOf(cert("root"))))
    }

    @Test fun untrustedRootFailsClosed() {
        assertFalse(OwnerAttestationChainGate.validatesPath(listOf(cert("leaf"), cert("root")), setOf(cert("rogue"))))
    }

    @Test fun injectedRootAsLeafFailsClosed() {
        assertFalse(OwnerAttestationChainGate.validatesPath(listOf(cert("root"), cert("leaf")), setOf(cert("root"))))
    }

    @Test fun duplicateCertificateFailsClosed() {
        assertFalse(OwnerAttestationChainGate.validatesPath(listOf(cert("leaf"), cert("leaf"), cert("root")), setOf(cert("root"))))
    }

    /** Distinct, correctly signed offline fixtures isolate the eight-certificate boundary. */
    @Test fun eightDistinctCertificatesAtLimitValidate() {
        val root = cert("boundary-root")
        // Leaf is signed by intermediate 7; this eight-element path omits the root.
        val chain = listOf(cert("boundary-leaf")) +
            (7 downTo 1).map { cert("boundary-int$it") }
        assertTrue(OwnerAttestationChainGate.validatesPath(chain, setOf(root)))
    }

    @Test fun nineDistinctCertificatesOverLimitFailClosed() {
        val root = cert("boundary-root")
        val chain = listOf(cert("boundary-leaf")) +
            (7 downTo 1).map { cert("boundary-int$it") } + root
        assertTrue("fixtures must be distinct", chain.distinct().size == 9)
        assertFalse(OwnerAttestationChainGate.validatesPath(chain, setOf(root)))
    }

    @Test fun untrustedCertificateInsertedBeforeRootFailsClosed() {
        assertFalse(OwnerAttestationChainGate.validatesPath(
            listOf(cert("leaf"), cert("rogue"), cert("root")), setOf(cert("root"))
        ))
    }

    @Test fun missingAnchorsFailClosed() {
        assertFalse(OwnerAttestationChainGate.validatesPath(listOf(cert("leaf")), emptySet()))
    }
}
