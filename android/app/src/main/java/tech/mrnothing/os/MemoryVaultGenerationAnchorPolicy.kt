package tech.mrnothing.os

import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.security.MessageDigest

/**
 * SEC-023B1B2D6: OFFLINE structural comparison of a MemoryVault generation
 * record, an append-only Keystore marker, and a separately pinned witness.
 *
 * All three inputs are caller-supplied. This class CANNOT authenticate witness
 * provenance, guarantee rollback resistance, authorize key use or enable
 * MemoryVault. It must not be wired to persistence or an agent executor.
 */
internal class MemoryVaultAnchorRecord(
    val generation: Long,
    val generationId: ByteArray,
    val referenceSha256: ByteArray
)

internal class MemoryVaultAnchorMarker(
    val highestGeneration: Long,
    val generationId: ByteArray
)

internal class MemoryVaultAnchorWitness(
    val highestGeneration: Long,
    val commitmentSha256: ByteArray
)

internal enum class MemoryVaultAnchorOutcome {
    BLOCKED,
    RECOVERY_REQUIRED_NOT_AUTHORIZED,
    CONSISTENT_INPUTS_NOT_AUTHORIZED
}

internal object MemoryVaultGenerationAnchorPolicy {
    private val domain = "mrnothing.memoryvault.anchor.v1\u0000"
        .toByteArray(StandardCharsets.US_ASCII)
    private const val HASH_BYTES = 32

    /** Canonical hash for an externally authenticated, independently retained witness. */
    internal fun commitment(record: MemoryVaultAnchorRecord): ByteArray? {
        if (!validRecord(record)) return null
        val generationBytes = ByteBuffer.allocate(java.lang.Long.BYTES)
            .putLong(record.generation).array()
        return MessageDigest.getInstance("SHA-256").digest(
            domain + generationBytes + record.generationId + record.referenceSha256
        )
    }

    /**
     * Diagnostic ONLY. A malicious caller can replace the witness as well as
     * the record and marker. No outcome means authorized or safe to persist.
     */
    fun inspect(
        record: MemoryVaultAnchorRecord?,
        marker: MemoryVaultAnchorMarker?,
        witness: MemoryVaultAnchorWitness?
    ): MemoryVaultAnchorOutcome {
        if (witness == null || !validGeneration(witness.highestGeneration) ||
            witness.commitmentSha256.size != HASH_BYTES
        ) return MemoryVaultAnchorOutcome.BLOCKED

        if (record == null) {
            return if (marker != null &&
                validGeneration(marker.highestGeneration) &&
                marker.generationId.size == HASH_BYTES &&
                (marker.highestGeneration > 0L || witness.highestGeneration > 0L)
            ) MemoryVaultAnchorOutcome.RECOVERY_REQUIRED_NOT_AUTHORIZED
            else MemoryVaultAnchorOutcome.BLOCKED
        }
        if (!validRecord(record) || marker == null ||
            !validGeneration(marker.highestGeneration) ||
            marker.generationId.size != HASH_BYTES
        ) return MemoryVaultAnchorOutcome.BLOCKED

        if (record.generation < marker.highestGeneration ||
            record.generation < witness.highestGeneration
        ) return MemoryVaultAnchorOutcome.RECOVERY_REQUIRED_NOT_AUTHORIZED

        // A record ahead of either witness/marker is an unanchored future state.
        if (record.generation != marker.highestGeneration ||
            record.generation != witness.highestGeneration
        ) return MemoryVaultAnchorOutcome.BLOCKED

        if (!MessageDigest.isEqual(record.generationId, marker.generationId)) {
            return MemoryVaultAnchorOutcome.BLOCKED
        }
        val expected = commitment(record) ?: return MemoryVaultAnchorOutcome.BLOCKED
        return try {
            if (MessageDigest.isEqual(expected, witness.commitmentSha256)) {
                MemoryVaultAnchorOutcome.CONSISTENT_INPUTS_NOT_AUTHORIZED
            } else {
                MemoryVaultAnchorOutcome.BLOCKED
            }
        } finally {
            expected.fill(0)
        }
    }

    private fun validGeneration(value: Long): Boolean = value > 0L && value < Long.MAX_VALUE

    private fun validRecord(record: MemoryVaultAnchorRecord): Boolean =
        validGeneration(record.generation) &&
            record.generationId.size == HASH_BYTES &&
            record.referenceSha256.size == HASH_BYTES
}
