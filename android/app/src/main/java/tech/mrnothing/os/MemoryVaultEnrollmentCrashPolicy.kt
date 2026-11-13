package tech.mrnothing.os

/**
 * SEC-023B1B2D8: OFFLINE crash-window model for a proposed generation rotation.
 *
 * These values are untrusted observations, NOT evidence of fsync, signature
 * verification, independent signer pinning, or rollback-resistant storage.
 * No outcome authorizes recovery, key use, memory persistence, or execution.
 * This policy deliberately has no Android, filesystem, or Keystore dependency.
 */
internal data class MemoryVaultEnrollmentSnapshot(
    val previousGeneration: Long,
    val candidateGeneration: Long,
    val stagedGeneration: Long?,
    val markerGeneration: Long,
    val witnessGeneration: Long,
    val trustedWatermarkGeneration: Long,
    val activeGeneration: Long
)

internal enum class MemoryVaultEnrollmentCrashOutcome {
    BLOCKED,
    UNCHANGED_NOT_AUTHORIZED,
    STAGED_ABORT_REQUIRES_OWNER_REVIEW,
    RECOVERY_REQUIRED_NOT_AUTHORIZED,
    STRUCTURALLY_COMPLETE_NOT_AUTHORIZED
}

internal object MemoryVaultEnrollmentCrashPolicy {
    /**
     * Proposed write ordering: durable candidate -> marker -> signed witness ->
     * independently durable watermark -> active pointer. Never auto-resume.
     * This models ordering only; caller-supplied generations cannot prove it.
     */
    fun inspect(snapshot: MemoryVaultEnrollmentSnapshot?): MemoryVaultEnrollmentCrashOutcome {
        if (snapshot == null) return MemoryVaultEnrollmentCrashOutcome.BLOCKED
        val previous = snapshot.previousGeneration
        val target = snapshot.candidateGeneration
        if (previous <= 0L || previous >= Long.MAX_VALUE - 1L || target != previous + 1L) {
            return MemoryVaultEnrollmentCrashOutcome.BLOCKED
        }
        val stage = snapshot.stagedGeneration
        if (stage != null && stage != target) return MemoryVaultEnrollmentCrashOutcome.BLOCKED
        val values = listOf(
            snapshot.markerGeneration,
            snapshot.witnessGeneration,
            snapshot.trustedWatermarkGeneration,
            snapshot.activeGeneration
        )
        if (values.any { it != previous && it != target }) {
            return MemoryVaultEnrollmentCrashOutcome.BLOCKED
        }
        val markerAdvanced = snapshot.markerGeneration == target
        val witnessAdvanced = snapshot.witnessGeneration == target
        val watermarkAdvanced = snapshot.trustedWatermarkGeneration == target
        val activeAdvanced = snapshot.activeGeneration == target
        // A later publication before its predecessor is never a valid crash window.
        if ((markerAdvanced && stage == null) ||
            (witnessAdvanced && !markerAdvanced) ||
            (watermarkAdvanced && !witnessAdvanced) ||
            (activeAdvanced && !watermarkAdvanced)
        ) return MemoryVaultEnrollmentCrashOutcome.BLOCKED

        return when {
            activeAdvanced -> MemoryVaultEnrollmentCrashOutcome.STRUCTURALLY_COMPLETE_NOT_AUTHORIZED
            markerAdvanced -> MemoryVaultEnrollmentCrashOutcome.RECOVERY_REQUIRED_NOT_AUTHORIZED
            stage != null -> MemoryVaultEnrollmentCrashOutcome.STAGED_ABORT_REQUIRES_OWNER_REVIEW
            else -> MemoryVaultEnrollmentCrashOutcome.UNCHANGED_NOT_AUTHORIZED
        }
    }
}
