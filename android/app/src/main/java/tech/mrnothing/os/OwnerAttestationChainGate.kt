package tech.mrnothing.os

import java.security.GeneralSecurityException
import java.security.cert.CertPathValidator
import java.security.cert.CertificateFactory
import java.security.cert.PKIXParameters
import java.security.cert.TrustAnchor
import java.security.cert.X509Certificate

/**
 * SEC-014M: offline certificate-path preflight only, NOT an owner identity or
 * verified-boot assertion. An empty or unprovisioned trust-anchor set denies.
 * Trust anchors must be independently provisioned from authenticated sources.
 * Revocation is not implemented: this gate cannot authorize agent actions.
 */
internal object OwnerAttestationChainGate {
    fun validatesPath(
        chain: List<X509Certificate>,
        trustedRoots: Set<X509Certificate>
    ): Boolean {
        if (chain.isEmpty() || chain.size > 8 || trustedRoots.isEmpty() ||
            trustedRoots.size > 8 || chain.distinct().size != chain.size
        ) return false
        return try {
            val anchors = trustedRoots.map { TrustAnchor(it, null) }.toSet()
            // The root is a trust anchor, not an untrusted certificate in the path.
            val pathCertificates = if (chain.last() in trustedRoots) chain.dropLast(1) else chain
            if (pathCertificates.isEmpty()) return false
            val path = CertificateFactory.getInstance("X.509").generateCertPath(pathCertificates)
            val parameters = PKIXParameters(anchors)
            // Offline path validation is not revocation checking. A separate
            // online/freshness/revocation gate is mandatory before any trust decision.
            parameters.isRevocationEnabled = false
            CertPathValidator.getInstance("PKIX").validate(path, parameters)
            true
        } catch (_: GeneralSecurityException) {
            false
        } catch (_: IllegalArgumentException) {
            false
        }
    }
}
