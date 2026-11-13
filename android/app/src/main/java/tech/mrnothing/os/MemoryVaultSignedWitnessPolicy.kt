package tech.mrnothing.os

import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.security.GeneralSecurityException
import java.security.KeyFactory
import java.security.MessageDigest
import java.security.Signature
import java.security.spec.X509EncodedKeySpec

/**
 * SEC-023B1B2D7: offline signed-witness provenance diagnostic ONLY.
 *
 * The caller must obtain the pinned public-key digest and high-watermark from
 * independent, authenticated, rollback-resistant trust domains. This policy
 * cannot establish their provenance and NEVER authorizes storage or execution.
 */
internal class MemoryVaultSignedWitness(
    val witness: MemoryVaultAnchorWitness,
    val signature: ByteArray
)

internal enum class MemoryVaultSignedWitnessOutcome {
    BLOCKED,
    RECOVERY_REQUIRED_NOT_AUTHORIZED,
    VERIFIED_PROVENANCE_NOT_AUTHORIZED
}

internal object MemoryVaultSignedWitnessPolicy {
    private val domain = "mrnothing.memoryvault.witness.v1\u0000"
        .toByteArray(StandardCharsets.US_ASCII)
    private const val HASH_BYTES = 32
    private const val SIGNATURE_BYTES = 64
    private const val MAX_PUBLIC_KEY_DER_BYTES = 512

    /** Canonical, domain-separated Ed25519 payload; never serialize with locale rules. */
    internal fun payload(witness: MemoryVaultAnchorWitness): ByteArray? {
        if (witness.highestGeneration <= 0L || witness.highestGeneration == Long.MAX_VALUE ||
            witness.commitmentSha256.size != HASH_BYTES
        ) return null
        return domain + ByteBuffer.allocate(java.lang.Long.BYTES)
            .putLong(witness.highestGeneration).array() + witness.commitmentSha256
    }

    fun inspect(
        record: MemoryVaultAnchorRecord?,
        marker: MemoryVaultAnchorMarker?,
        signedWitness: MemoryVaultSignedWitness?,
        publicKeyX509Der: ByteArray?,
        pinnedPublicKeySha256: ByteArray?,
        trustedHighWatermark: Long?
    ): MemoryVaultSignedWitnessOutcome {
        if (record == null || marker == null || signedWitness == null ||
            publicKeyX509Der == null || pinnedPublicKeySha256 == null ||
            trustedHighWatermark == null || trustedHighWatermark <= 0L ||
            trustedHighWatermark == Long.MAX_VALUE
        ) return MemoryVaultSignedWitnessOutcome.BLOCKED

        // Snapshot mutable caller-owned byte arrays before verification.
        val frozenRecord = MemoryVaultAnchorRecord(
            record.generation, record.generationId.copyOf(), record.referenceSha256.copyOf())
        val frozenMarker = MemoryVaultAnchorMarker(
            marker.highestGeneration, marker.generationId.copyOf())
        val frozenWitness = MemoryVaultAnchorWitness(
            signedWitness.witness.highestGeneration,
            signedWitness.witness.commitmentSha256.copyOf())
        val signatureBytes = signedWitness.signature.copyOf()
        val publicKeyBytes = publicKeyX509Der.copyOf()
        val pin = pinnedPublicKeySha256.copyOf()

        if (signatureBytes.size != SIGNATURE_BYTES || pin.size != HASH_BYTES ||
            publicKeyBytes.size !in 32..MAX_PUBLIC_KEY_DER_BYTES
        ) return MemoryVaultSignedWitnessOutcome.BLOCKED
        val actualKeyDigest = MessageDigest.getInstance("SHA-256").digest(publicKeyBytes)
        if (!MessageDigest.isEqual(actualKeyDigest, pin)) {
            return MemoryVaultSignedWitnessOutcome.BLOCKED
        }
        val message = payload(frozenWitness) ?: return MemoryVaultSignedWitnessOutcome.BLOCKED
        val validSignature = try {
            val publicKey = KeyFactory.getInstance("Ed25519")
                .generatePublic(X509EncodedKeySpec(publicKeyBytes))
            val verifier = Signature.getInstance("Ed25519")
            verifier.initVerify(publicKey)
            verifier.update(message)
            verifier.verify(signatureBytes)
        } catch (_: GeneralSecurityException) {
            false
        } catch (_: IllegalArgumentException) {
            false
        }
        if (!validSignature) return MemoryVaultSignedWitnessOutcome.BLOCKED

        // A correctly signed historical witness is not a current trusted witness.
        if (frozenWitness.highestGeneration < trustedHighWatermark) {
            return MemoryVaultSignedWitnessOutcome.RECOVERY_REQUIRED_NOT_AUTHORIZED
        }
        if (frozenWitness.highestGeneration > trustedHighWatermark) {
            return MemoryVaultSignedWitnessOutcome.BLOCKED
        }
        return when (MemoryVaultGenerationAnchorPolicy.inspect(
            frozenRecord, frozenMarker, frozenWitness
        )) {
            MemoryVaultAnchorOutcome.CONSISTENT_INPUTS_NOT_AUTHORIZED ->
                MemoryVaultSignedWitnessOutcome.VERIFIED_PROVENANCE_NOT_AUTHORIZED
            MemoryVaultAnchorOutcome.RECOVERY_REQUIRED_NOT_AUTHORIZED ->
                MemoryVaultSignedWitnessOutcome.RECOVERY_REQUIRED_NOT_AUTHORIZED
            MemoryVaultAnchorOutcome.BLOCKED -> MemoryVaultSignedWitnessOutcome.BLOCKED
        }
    }
}
