package tech.mrnothing.os

import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties

/**
 * SEC-023B1B1: dormant specification for a future owner-initiated vault key.
 *
 * Never generates, imports, deletes, replaces or uses a key. Its inputs
 * are planning signals, NOT cryptographic proof of owner authentication.
 * A positive result is neither consent nor authorization.
 */
internal data class MemoryVaultProvisioningSignals(
    val apiLevel: Int,
    val primaryOwnerProfile: Boolean,
    val trustedAppCaller: Boolean,
    val foregroundOwnerUi: Boolean,
    val deviceUnlocked: Boolean,
    val secureDeviceCredentialConfigured: Boolean,
    val explicitMemoryOptIn: Boolean,
    val strongBoxAdvertised: Boolean,
    val aliasAbsent: Boolean
)

internal enum class MemoryVaultProvisioningReadiness {
    BLOCKED,
    REQUIRES_OWNER_CEREMONY
}

/** Pure policy. It cannot attest to the origin of any supplied signal. */
internal object MemoryVaultProvisioningPolicy {
    const val MIN_API = 31

    fun evaluate(s: MemoryVaultProvisioningSignals): MemoryVaultProvisioningReadiness =
        if (s.apiLevel >= MIN_API &&
            s.primaryOwnerProfile &&
            s.trustedAppCaller &&
            s.foregroundOwnerUi &&
            s.deviceUnlocked &&
            s.secureDeviceCredentialConfigured &&
            s.explicitMemoryOptIn &&
            s.strongBoxAdvertised &&
            s.aliasAbsent
        ) MemoryVaultProvisioningReadiness.REQUIRES_OWNER_CEREMONY
        else MemoryVaultProvisioningReadiness.BLOCKED
}

/**
 * Constructs an uninstalled Android Keystore specification for independent
 * review. No KeyStore access or key generation. This distinct alias matches
 * the read-only SEC-023B1B0 proposal, which remains unmerged.
 * StrongBox and per-use device credential are mandatory, never downgraded.
 */
internal object MemoryVaultKeySpecDraft {
    internal const val KEY_ALIAS = "mrnothing_memory_vault_aes_gcm_v1"

    fun forSecurityReview(
        signals: MemoryVaultProvisioningSignals
    ): KeyGenParameterSpec? {
        if (MemoryVaultProvisioningPolicy.evaluate(signals) !=
            MemoryVaultProvisioningReadiness.REQUIRES_OWNER_CEREMONY
        ) return null
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return null
        return KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setKeySize(256)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setRandomizedEncryptionRequired(true)
            .setUnlockedDeviceRequired(true)
            .setUserAuthenticationRequired(true)
            .setUserAuthenticationParameters(
                0, KeyProperties.AUTH_DEVICE_CREDENTIAL
            )
            .setIsStrongBoxBacked(true)
            .build()
    }
}
