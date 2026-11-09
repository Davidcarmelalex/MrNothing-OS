package tech.mrnothing.os

import android.os.Build
import android.security.keystore.KeyInfo
import android.security.keystore.KeyProperties
import java.io.IOException
import java.security.GeneralSecurityException
import java.security.KeyStore
import javax.crypto.SecretKeyFactory

/**
 * SEC-023B1B0: read-only inspection of an existing, distinct MemoryVault key.
 *
 * A positive result means only that the key's reported parameters satisfy the
 * local policy. It is NOT proof of owner authentication, authorization, consent,
 * a valid CryptoObject, or a usable encrypted-memory service. KeyInfo does not
 * expose unlocked-device or randomized-encryption policy; those must be
 * verified separately from a controlled key-generation specification.
 *
 * No key is created, imported, replaced, used for cryptography or deleted here.
 */
internal data class MemoryVaultKeySignals(
    val keyPresent: Boolean,
    val aesAlgorithm: Boolean,
    val keySizeBits: Int,
    val gcmOnly: Boolean,
    val noPaddingOnly: Boolean,
    val encryptDecryptOnly: Boolean,
    val generatedInKeystore: Boolean,
    val strongBoxBacked: Boolean,
    val credentialOnlyAuth: Boolean,
    val authenticationRequired: Boolean,
    val perUseAuthentication: Boolean
)

internal enum class MemoryVaultKeyReadiness {
    BLOCKED,
    EXISTING_KEY_REQUIRES_OWNER_AUTH
}

/** Pure JVM policy; never treats key metadata as evidence of an auth event. */
internal object MemoryVaultKeyPolicy {
    const val MIN_INSPECTION_API = 31
    const val REQUIRED_AES_BITS = 256

    fun evaluate(apiLevel: Int, s: MemoryVaultKeySignals): MemoryVaultKeyReadiness =
        if (apiLevel >= MIN_INSPECTION_API &&
            s.keyPresent && s.aesAlgorithm &&
            s.keySizeBits == REQUIRED_AES_BITS &&
            s.gcmOnly && s.noPaddingOnly && s.encryptDecryptOnly &&
            s.generatedInKeystore && s.strongBoxBacked &&
            s.credentialOnlyAuth && s.authenticationRequired &&
            s.perUseAuthentication
        ) MemoryVaultKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH
        else MemoryVaultKeyReadiness.BLOCKED
}

internal object MemoryVaultKeystorePreflight {
    // Deliberately distinct from the existing owner-consent signing identity.
    internal const val KEY_ALIAS = "mrnothing_memory_vault_aes_gcm_v1"

    /**
     * Read-only, fail-closed. Caller must independently establish owner identity,
     * foreground consent, prompt CryptoObject binding and revocation semantics.
     */
    fun inspectExisting(): MemoryVaultKeyReadiness {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            return MemoryVaultKeyReadiness.BLOCKED
        }
        return try {
            val store = KeyStore.getInstance("AndroidKeyStore")
            store.load(null)
            val entry = store.getEntry(KEY_ALIAS, null) as? KeyStore.SecretKeyEntry
                ?: return MemoryVaultKeyReadiness.BLOCKED
            val key = entry.secretKey
            val factory = SecretKeyFactory.getInstance(
                KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore"
            )
            val info = factory.getKeySpec(key, KeyInfo::class.java) as? KeyInfo
                ?: return MemoryVaultKeyReadiness.BLOCKED
            val purposes = KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            MemoryVaultKeyPolicy.evaluate(
                Build.VERSION.SDK_INT,
                MemoryVaultKeySignals(
                    keyPresent = true,
                    aesAlgorithm = key.algorithm.equals("AES", ignoreCase = true),
                    keySizeBits = info.keySize,
                    gcmOnly = info.blockModes.toSet() == setOf(KeyProperties.BLOCK_MODE_GCM),
                    noPaddingOnly = info.encryptionPaddings.toSet() ==
                        setOf(KeyProperties.ENCRYPTION_PADDING_NONE),
                    encryptDecryptOnly = info.purposes == purposes,
                    generatedInKeystore = info.origin == KeyProperties.ORIGIN_GENERATED,
                    strongBoxBacked = info.securityLevel ==
                        KeyProperties.SECURITY_LEVEL_STRONGBOX,
                    credentialOnlyAuth = info.userAuthenticationType ==
                        KeyProperties.AUTH_DEVICE_CREDENTIAL,
                    authenticationRequired = info.isUserAuthenticationRequired,
                    perUseAuthentication = info.userAuthenticationValidityDurationSeconds == -1
                )
            )
        } catch (_: GeneralSecurityException) {
            MemoryVaultKeyReadiness.BLOCKED
        } catch (_: IOException) {
            MemoryVaultKeyReadiness.BLOCKED
        } catch (_: RuntimeException) {
            MemoryVaultKeyReadiness.BLOCKED
        }
    }
}
