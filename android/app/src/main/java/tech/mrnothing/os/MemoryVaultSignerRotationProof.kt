package tech.mrnothing.os

import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.security.GeneralSecurityException
import java.security.KeyFactory
import java.security.MessageDigest
import java.security.Signature
import java.security.spec.X509EncodedKeySpec

/**
 * SEC-023B1B2D9B: OFFLINE dual-signature signer-rotation diagnostic.
 *
 * Both signatures prove possession of the supplied keys, not provenance of
 * the externally pinned old key, genuine owner consent, rollback resistance,
 * or durable enrollment. Never feed this outcome into an authorization gate.
 * No Android, Keystore, filesystem, or runtime dependency is permitted.
 */
internal data class MemoryVaultSignerRotationEvidence(
    val previousGeneration: Long,
    val candidateGeneration: Long,
    val ownerUserId: Int,
    val requestNonceHex: String,
    val oldPublicKeyX509Der: ByteArray,
    val newPublicKeyX509Der: ByteArray,
    val externallyPinnedOldKeySha256: ByteArray,
    val expectedNewKeySha256: ByteArray,
    val oldSignerSignature: ByteArray,
    val newSignerSignature: ByteArray
)

internal enum class MemoryVaultSignerRotationOutcome {
    BLOCKED,
    DUAL_SIGNATURES_VALID_NOT_AUTHORIZED
}

internal object MemoryVaultSignerRotationProof {
    private val domain = "mrnothing.memoryvault.signer-rotation.v1\u0000"
        .toByteArray(StandardCharsets.US_ASCII)
    private val noncePattern = Regex("^[0-9a-f]{64}$")
    private const val DIGEST_BYTES = 32
    private const val SIGNATURE_BYTES = 64
    private const val MAX_DER_BYTES = 512

    /**
     * Canonical signed payload. The old signer approves exactly this new pin;
     * the new signer proves possession of its key for the same transaction.
     */
    internal fun payload(evidence: MemoryVaultSignerRotationEvidence): ByteArray? {
        if (evidence.previousGeneration <= 0L ||
            evidence.previousGeneration >= Long.MAX_VALUE - 1L ||
            evidence.candidateGeneration != evidence.previousGeneration + 1L ||
            evidence.ownerUserId != 0 ||
            evidence.requestNonceHex.length != 64 ||
            !noncePattern.matches(evidence.requestNonceHex) ||
            evidence.externallyPinnedOldKeySha256.size != DIGEST_BYTES ||
            evidence.expectedNewKeySha256.size != DIGEST_BYTES ||
            MessageDigest.isEqual(
                evidence.externallyPinnedOldKeySha256, evidence.expectedNewKeySha256
            )
        ) return null

        return ByteBuffer.allocate(domain.size + 8 + 8 + 4 + 64 + 2 * DIGEST_BYTES)
            .put(domain)
            .putLong(evidence.previousGeneration)
            .putLong(evidence.candidateGeneration)
            .putInt(evidence.ownerUserId)
            .put(evidence.requestNonceHex.toByteArray(StandardCharsets.US_ASCII))
            .put(evidence.externallyPinnedOldKeySha256)
            .put(evidence.expectedNewKeySha256)
            .array()
    }

    fun inspect(untrusted: MemoryVaultSignerRotationEvidence?): MemoryVaultSignerRotationOutcome {
        if (untrusted == null ||
            untrusted.oldPublicKeyX509Der.size !in 32..MAX_DER_BYTES ||
            untrusted.newPublicKeyX509Der.size !in 32..MAX_DER_BYTES ||
            untrusted.oldSignerSignature.size != SIGNATURE_BYTES ||
            untrusted.newSignerSignature.size != SIGNATURE_BYTES ||
            untrusted.externallyPinnedOldKeySha256.size != DIGEST_BYTES ||
            untrusted.expectedNewKeySha256.size != DIGEST_BYTES
        ) return MemoryVaultSignerRotationOutcome.BLOCKED

        // Freeze mutable caller-owned arrays before hashing and verification.
        val evidence = untrusted.copy(
            oldPublicKeyX509Der = untrusted.oldPublicKeyX509Der.copyOf(),
            newPublicKeyX509Der = untrusted.newPublicKeyX509Der.copyOf(),
            externallyPinnedOldKeySha256 = untrusted.externallyPinnedOldKeySha256.copyOf(),
            expectedNewKeySha256 = untrusted.expectedNewKeySha256.copyOf(),
            oldSignerSignature = untrusted.oldSignerSignature.copyOf(),
            newSignerSignature = untrusted.newSignerSignature.copyOf()
        )
        val message = payload(evidence) ?: return MemoryVaultSignerRotationOutcome.BLOCKED
        if (MessageDigest.isEqual(evidence.oldPublicKeyX509Der, evidence.newPublicKeyX509Der) ||
            !MessageDigest.isEqual(
                sha256(evidence.oldPublicKeyX509Der), evidence.externallyPinnedOldKeySha256
            ) ||
            !MessageDigest.isEqual(
                sha256(evidence.newPublicKeyX509Der), evidence.expectedNewKeySha256
            ) ||
            !verify(evidence.oldPublicKeyX509Der, evidence.oldSignerSignature, message) ||
            !verify(evidence.newPublicKeyX509Der, evidence.newSignerSignature, message)
        ) return MemoryVaultSignerRotationOutcome.BLOCKED

        // Explicitly not permission to enroll, rotate, persist, or recover.
        return MemoryVaultSignerRotationOutcome.DUAL_SIGNATURES_VALID_NOT_AUTHORIZED
    }

    private fun sha256(bytes: ByteArray): ByteArray =
        MessageDigest.getInstance("SHA-256").digest(bytes)

    private fun verify(der: ByteArray, signature: ByteArray, payload: ByteArray): Boolean {
        return try {
            val key = KeyFactory.getInstance("Ed25519")
                .generatePublic(X509EncodedKeySpec(der))
            // Reject noncanonical or trailing DER representations of the same key.
            if (!MessageDigest.isEqual(key.encoded, der)) {
                false
            } else {
                val verifier = Signature.getInstance("Ed25519")
                verifier.initVerify(key)
                verifier.update(payload)
                verifier.verify(signature)
            }
        } catch (_: GeneralSecurityException) {
            false
        } catch (_: RuntimeException) {
            false
        }
    }
}
