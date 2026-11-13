package tech.mrnothing.os

import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import org.junit.Assert.assertEquals
import org.junit.Test

/** Offline software JCE keys ONLY: not owner, Keystore or StrongBox evidence. */
class MemoryVaultGenerationCanaryVerifierTest {
    private val keyA = SecretKeySpec(ByteArray(32) { (it + 1).toByte() }, "AES")
    private val keyB = SecretKeySpec(ByteArray(32) { (it + 33).toByte() }, "AES")
    private val nonce = ByteArray(12) { (it + 1).toByte() }
    private val generationId = ByteArray(32) { (it + 50).toByte() }
    private val consentDigest = ByteArray(32) { (it + 100).toByte() }
    private val blocked = MemoryVaultGenerationCanaryOutcome.BLOCKED

    private fun reference(): MemoryVaultGenerationCanaryReference {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, keyA, GCMParameterSpec(128, nonce))
        cipher.updateAAD(MemoryVaultGenerationCanaryVerifier.associatedData(generationId, consentDigest))
        val ciphertext = cipher.doFinal(MemoryVaultGenerationCanaryVerifier.marker(generationId))
        return MemoryVaultGenerationCanaryReference(
            nonce.copyOf(), generationId.copyOf(), consentDigest.copyOf(), ciphertext
        )
    }

    private fun decrypt(key: SecretKeySpec, iv: ByteArray = nonce): Cipher =
        Cipher.getInstance("AES/GCM/NoPadding").apply {
            init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(128, iv))
        }

    @Test fun matchingKeyReferenceIsDiagnosticOnly() {
        assertEquals(MemoryVaultGenerationCanaryOutcome.REFERENCE_MATCH_NOT_AUTHORIZED,
            MemoryVaultGenerationCanaryVerifier.verify(decrypt(keyA), reference()))
    }

    @Test fun replacedSamePolicyKeyIsRejected() {
        // Both keys are AES-256/GCM with identical software-key policy.
        assertEquals(blocked, MemoryVaultGenerationCanaryVerifier.verify(decrypt(keyB), reference()))
    }

    @Test fun modifiedCiphertextIsRejected() {
        val r = reference()
        r.ciphertextAndTag[0] = (r.ciphertextAndTag[0].toInt() xor 1).toByte()
        assertEquals(blocked, MemoryVaultGenerationCanaryVerifier.verify(decrypt(keyA), r))
    }

    @Test fun modifiedGenerationIdIsRejected() {
        val r = reference()
        r.generationId[0] = (r.generationId[0].toInt() xor 1).toByte()
        assertEquals(blocked, MemoryVaultGenerationCanaryVerifier.verify(decrypt(keyA), r))
    }

    @Test fun modifiedConsentDigestIsRejected() {
        val r = reference()
        r.consentDigest[0] = (r.consentDigest[0].toInt() xor 1).toByte()
        assertEquals(blocked, MemoryVaultGenerationCanaryVerifier.verify(decrypt(keyA), r))
    }

    @Test fun wrongNonceIsRejected() {
        val r = reference()
        val otherNonce = nonce.copyOf().apply { this[0] = (this[0].toInt() xor 1).toByte() }
        assertEquals(blocked, MemoryVaultGenerationCanaryVerifier.verify(decrypt(keyA, otherNonce), r))
    }

    @Test fun missingReferenceIsRejected() {
        assertEquals(blocked, MemoryVaultGenerationCanaryVerifier.verify(decrypt(keyA), null))
    }

    @Test fun truncatedTagIsRejected() {
        val r = reference()
        val truncated = MemoryVaultGenerationCanaryReference(
            r.nonce, r.generationId, r.consentDigest,
            r.ciphertextAndTag.copyOf(r.ciphertextAndTag.size - 1)
        )
        assertEquals(blocked, MemoryVaultGenerationCanaryVerifier.verify(decrypt(keyA), truncated))
    }

    @Test fun arbitraryPlaintextIsRejected() {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        c.init(Cipher.ENCRYPT_MODE, keyA, GCMParameterSpec(128, nonce))
        c.updateAAD(MemoryVaultGenerationCanaryVerifier.associatedData(generationId, consentDigest))
        val forged = c.doFinal(ByteArray(MemoryVaultGenerationCanaryVerifier.marker(generationId).size))
        val r = MemoryVaultGenerationCanaryReference(nonce, generationId, consentDigest, forged)
        assertEquals(blocked, MemoryVaultGenerationCanaryVerifier.verify(decrypt(keyA), r))
    }
}
