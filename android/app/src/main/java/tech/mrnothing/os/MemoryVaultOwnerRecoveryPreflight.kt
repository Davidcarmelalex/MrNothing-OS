package tech.mrnothing.os

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.nio.charset.StandardCharsets
import java.security.MessageDigest

/**
 * SEC-023B1B2D9: offline owner-recovery intent preflight, never an authorization.
 *
 * All inputs, including the claimed independent pin and watermark, are caller
 * assertions. This code cannot prove their provenance, durability, or that an
 * Android credential prompt actually ran. No runtime caller is permitted yet.
 * The existing one-shot confirmation state supplies bounded lifetime semantics.
 */
internal data class MemoryVaultOwnerRecoverySnapshot(
    val enrollment: MemoryVaultEnrollmentSnapshot,
    val observedSignerPinSha256: ByteArray,
    val externallyPinnedSignerSha256: ByteArray,
    val externalHighWatermarkGeneration: Long,
    val requestNonceHex: String,
    val ownerUserId: Int,
    val foregroundOwnerUi: Boolean,
    val deviceUnlocked: Boolean,
    val secureCredentialConfigured: Boolean,
    val explicitOwnerAcknowledgement: Boolean
)

internal enum class MemoryVaultOwnerRecoveryOutcome {
    BLOCKED,
    OWNER_REVIEW_RECORDED_NOT_AUTHORIZED
}

internal class MemoryVaultOwnerRecoveryPreflight(clockNanos: () -> Long) {
    private val confirmation = OwnerAuthorityConfirmationState(clockNanos)
    private var attempted = false

    /** Preview only. Binding must be displayed by a future trusted owner UI. */
    @Synchronized
    fun begin(snapshot: MemoryVaultOwnerRecoverySnapshot): String? {
        if (attempted) return null
        attempted = true
        val binding = bindingFor(snapshot) ?: return null
        return if (confirmation.begin(binding)) binding else null
    }

    /** A reported credential success records intent only; it never grants recovery. */
    @Synchronized
    fun finish(
        snapshot: MemoryVaultOwnerRecoverySnapshot,
        platformCredentialReported: Boolean
    ): MemoryVaultOwnerRecoveryOutcome {
        val binding = bindingFor(snapshot) ?: ""
        return if (confirmation.finish(binding, platformCredentialReported)) {
            MemoryVaultOwnerRecoveryOutcome.OWNER_REVIEW_RECORDED_NOT_AUTHORIZED
        } else {
            MemoryVaultOwnerRecoveryOutcome.BLOCKED
        }
    }

    /** Cancellation, backgrounding and process teardown must revoke the attempt. */
    @Synchronized
    fun revoke() {
        attempted = true
        confirmation.revoke()
    }

    companion object {
        private const val DOMAIN = "MRNOTHING-MEMORYVAULT-OWNER-RECOVERY-INTENT-V1"
        private val noncePattern = Regex("^[0-9a-f]{64}$")

        internal fun bindingFor(snapshot: MemoryVaultOwnerRecoverySnapshot): String? {
            val enrollment = snapshot.enrollment
            val crash = MemoryVaultEnrollmentCrashPolicy.inspect(enrollment)
            if (crash != MemoryVaultEnrollmentCrashOutcome.RECOVERY_REQUIRED_NOT_AUTHORIZED &&
                crash != MemoryVaultEnrollmentCrashOutcome.STAGED_ABORT_REQUIRES_OWNER_REVIEW
            ) return null
            if (snapshot.ownerUserId != 0 || !snapshot.foregroundOwnerUi ||
                !snapshot.deviceUnlocked || !snapshot.secureCredentialConfigured ||
                !snapshot.explicitOwnerAcknowledgement ||
                !noncePattern.matches(snapshot.requestNonceHex)
            ) return null
            val observedPin = snapshot.observedSignerPinSha256.copyOf()
            val externalPin = snapshot.externallyPinnedSignerSha256.copyOf()
            if (observedPin.size != 32 || externalPin.size != 32 ||
                !MessageDigest.isEqual(observedPin, externalPin)
            ) return null
            // Equality of caller-supplied counters is NOT proof of anti-rollback.
            if (snapshot.externalHighWatermarkGeneration != enrollment.trustedWatermarkGeneration ||
                snapshot.externalHighWatermarkGeneration <= 0L
            ) return null

            val bytes = ByteArrayOutputStream()
            DataOutputStream(bytes).use { out ->
                val fields = listOf(
                    DOMAIN,
                    enrollment.previousGeneration.toString(),
                    enrollment.candidateGeneration.toString(),
                    (enrollment.stagedGeneration ?: -1L).toString(),
                    enrollment.markerGeneration.toString(),
                    enrollment.witnessGeneration.toString(),
                    enrollment.trustedWatermarkGeneration.toString(),
                    enrollment.activeGeneration.toString(),
                    snapshot.externalHighWatermarkGeneration.toString(),
                    snapshot.ownerUserId.toString(),
                    snapshot.requestNonceHex
                )
                for (field in fields) {
                    val value = field.toByteArray(StandardCharsets.US_ASCII)
                    out.writeInt(value.size)
                    out.write(value)
                }
                out.writeInt(externalPin.size)
                out.write(externalPin)
            }
            return MessageDigest.getInstance("SHA-256").digest(bytes.toByteArray())
                .joinToString("") { "%02x".format(it.toInt() and 0xff) }
        }
    }
}
