package tech.mrnothing.os

import java.security.GeneralSecurityException
import java.security.MessageDigest
import javax.crypto.Cipher

/**
 * SEC-023B1B2D5: offline reference-ciphertext verifier for a future trusted
 * key-generation anchor. NO Keystore access, key generation, persistence,
 * consent UI, Android executor integration, or authorization.
 *
 * A successful match shows only that a supplied, initialized decrypt Cipher
 * can open the supplied reference. It does NOT establish that the reference
 * came from a trusted, rollback-protected enrollment record, that the Cipher
 * was hardware-backed or owner-authenticated, or that the alias is unchanged.
 */
internal class MemoryVaultGenerationCanaryReference(
    val nonce: ByteArray,
    val generationId: ByteArray,
    val consentDigest: ByteArray,
    val ciphertextAndTag: ByteArray
)

internal enum class MemoryVaultGenerationCanaryOutcome {
    BLOCKED,
    REFERENCE_MATCH_NOT_AUTHORIZED
}

internal object MemoryVaultGenerationCanaryVerifier {
    private val domain = "mrnothing.memoryvault.generation-canary.v1".toByteArray(Charsets.US_ASCII)
    internal const val NONCE_BYTES = 12
    internal const val ID_BYTES = 32
    internal const val TAG_BYTES = 16

    /** Domain-separated binding to the enrolled generation and consent. */
    internal fun associatedData(generationId: ByteArray, consentDigest: ByteArray): ByteArray =
        domain + generationId + consentDigest

    /** Known marker for the reference; NOT secret owner or conversation data. */
    internal fun marker(generationId: ByteArray): ByteArray = domain + generationId

    /**
     * The caller must supply a Cipher initialized for GCM decryption using
     * the original reference nonce. A future owner-authenticated integration
     * must independently validate the protected reference provenance and
     * bind the Cipher to the same Keystore key generation.
     */
    fun verify(
        decryptCipher: Cipher,
        reference: MemoryVaultGenerationCanaryReference?
    ): MemoryVaultGenerationCanaryOutcome {
        if (reference == null) return MemoryVaultGenerationCanaryOutcome.BLOCKED
        // Snapshot mutable byte arrays before any potentially blocking crypto.
        val nonce = reference.nonce.copyOf()
        val generationId = reference.generationId.copyOf()
        val consentDigest = reference.consentDigest.copyOf()
        val ciphertext = reference.ciphertextAndTag.copyOf()
        var plaintext: ByteArray? = null
        var aad: ByteArray? = null
        var expected: ByteArray? = null
        return try {
            if (nonce.size != NONCE_BYTES ||
                generationId.size != ID_BYTES ||
                consentDigest.size != ID_BYTES ||
                ciphertext.size != domain.size + ID_BYTES + TAG_BYTES ||
                decryptCipher.algorithm != "AES/GCM/NoPadding" ||
                !MessageDigest.isEqual(decryptCipher.iv ?: ByteArray(0), nonce)
            ) {
                MemoryVaultGenerationCanaryOutcome.BLOCKED
            } else {
                aad = associatedData(generationId, consentDigest)
                expected = marker(generationId)
                decryptCipher.updateAAD(aad)
                plaintext = decryptCipher.doFinal(ciphertext)
                if (MessageDigest.isEqual(plaintext, expected)) {
                    MemoryVaultGenerationCanaryOutcome.REFERENCE_MATCH_NOT_AUTHORIZED
                } else {
                    MemoryVaultGenerationCanaryOutcome.BLOCKED
                }
            }
        } catch (_: GeneralSecurityException) {
            MemoryVaultGenerationCanaryOutcome.BLOCKED
        } catch (_: RuntimeException) {
            MemoryVaultGenerationCanaryOutcome.BLOCKED
        } finally {
            nonce.fill(0)
            generationId.fill(0)
            consentDigest.fill(0)
            ciphertext.fill(0)
            plaintext?.fill(0)
            aad?.fill(0)
            expected?.fill(0)
        }
    }
}
