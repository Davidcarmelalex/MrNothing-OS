package tech.mrnothing.os

import android.hardware.biometrics.BiometricPrompt
import android.os.Build
import java.io.IOException
import java.security.GeneralSecurityException
import java.security.KeyStore
import javax.crypto.Cipher

/**
 * SEC-023B1B2D1/D3: dormant, one-shot read-only-key AES-GCM probe.
 * Never generates, imports, replaces or deletes keys. The only plaintext is
 * empty synthetic input, and the resulting tag is discarded. No persistence.
 * The result is NOT authorization; Pixel hardware and credential-only
 * CryptoObject interoperability remain unverified.
 */
internal enum class MemoryVaultCipherProbeOutcome {
    BLOCKED,
    CRYPTO_OPERATION_EXECUTED_NOT_AUTHORIZED
}

/** Pure JVM classification; synthetic inputs cannot prove hardware origin. */
internal object MemoryVaultCipherProbePolicy {
    fun evaluate(
        callback: MemoryVaultCryptoCallbackProgress,
        keyReadiness: MemoryVaultKeyReadiness,
        postOperationKeyReadiness: MemoryVaultKeyReadiness,
        gcmTagBytes: Int
    ): MemoryVaultCipherProbeOutcome =
        if (callback == MemoryVaultCryptoCallbackProgress.AWAITING_AUTHENTICATED_CIPHER_OPERATION &&
            keyReadiness == MemoryVaultKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH &&
            postOperationKeyReadiness == MemoryVaultKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH &&
            gcmTagBytes == 16
        ) MemoryVaultCipherProbeOutcome.CRYPTO_OPERATION_EXECUTED_NOT_AUTHORIZED
        else MemoryVaultCipherProbeOutcome.BLOCKED
}

internal class MemoryVaultAuthenticatedCipherProbe {
    private val callbackGate = MemoryVaultCryptoObjectCallbackGate()
    private val cancellationFence = MemoryVaultCompletionCancellationFence()
    private var attempted = false
    private var pendingCipher: Cipher? = null
    private var pendingDigest: String? = null
    private val digestFormat = Regex("^[0-9a-f]{64}$")

    /** Returns a CryptoObject for a FUTURE trusted UI; no prompt is launched. */
    @Synchronized
    fun prepare(
        consentProgress: MemoryVaultConsentProgress,
        consentDigest: String
    ): BiometricPrompt.CryptoObject? {
        if (attempted) return null
        attempted = true
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S ||
            consentProgress != MemoryVaultConsentProgress.AWAITING_CRYPTOOBJECT_PROOF ||
            !digestFormat.matches(consentDigest) ||
            MemoryVaultKeystorePreflight.inspectExisting() !=
                MemoryVaultKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH
        ) return null

        return try {
            val store = KeyStore.getInstance("AndroidKeyStore")
            store.load(null)
            val key = (store.getEntry(MemoryVaultKeystorePreflight.KEY_ALIAS, null)
                as? KeyStore.SecretKeyEntry)?.secretKey ?: return null
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, key)
            // Fail closed: no software-key or non-AndroidKeyStore provider.
            if (!cipher.provider.name.startsWith("AndroidKeyStore") ||
                cipher.iv?.size != 12
            ) return null
            val prompt = BiometricPrompt.CryptoObject(cipher)
            if (!callbackGate.arm(consentProgress, consentDigest, prompt)) return null
            pendingCipher = cipher
            pendingDigest = consentDigest
            prompt
        } catch (_: GeneralSecurityException) {
            null
        } catch (_: IOException) {
            null
        } catch (_: RuntimeException) {
            null
        }
    }

    /**
     * One-shot probe, not authorization. Only the pending-state transfer holds
     * the monitor; revoke() can therefore execute while doFinal() is blocked.
     * If revocation linearizes before finish(), the result is always BLOCKED.
     */
    fun complete(
        consentDigest: String,
        result: BiometricPrompt.AuthenticationResult?
    ): MemoryVaultCipherProbeOutcome {
        val (cipher, armedDigest) = synchronized(this) {
            val currentCipher = pendingCipher
            val currentDigest = pendingDigest
            pendingCipher = null
            pendingDigest = null
            currentCipher to currentDigest
        }
        if (cipher == null || armedDigest != consentDigest) {
            callbackGate.revoke()
            return MemoryVaultCipherProbeOutcome.BLOCKED
        }
        if (!cancellationFence.begin()) {
            callbackGate.revoke()
            return MemoryVaultCipherProbeOutcome.BLOCKED
        }

        var aad: ByteArray? = null
        var tag: ByteArray? = null
        return try {
            val callback = callbackGate.consume(consentDigest, result)
            if (callback != MemoryVaultCryptoCallbackProgress.AWAITING_AUTHENTICATED_CIPHER_OPERATION) {
                MemoryVaultCipherProbeOutcome.BLOCKED
            } else {
                val readiness = MemoryVaultKeystorePreflight.inspectExisting()
                if (readiness != MemoryVaultKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH) {
                    MemoryVaultCipherProbeOutcome.BLOCKED
                } else {
                    aad = ByteArray(32) { index ->
                        consentDigest.substring(index * 2, index * 2 + 2).toInt(16).toByte()
                    }
                    cipher.updateAAD(aad)
                    tag = cipher.doFinal(ByteArray(0))
                    // Reinspect AFTER the operation: deletion or policy downgrade must block.
                    // Matching metadata is NOT proof of same key generation after alias replacement.
                    val readinessAfter = MemoryVaultKeystorePreflight.inspectExisting()
                    val classified = MemoryVaultCipherProbePolicy.evaluate(
                        callback, readiness, readinessAfter, tag.size
                    )
                    if (cancellationFence.finish()) classified
                    else MemoryVaultCipherProbeOutcome.BLOCKED
                }
            }
        } catch (_: GeneralSecurityException) {
            MemoryVaultCipherProbeOutcome.BLOCKED
        } catch (_: RuntimeException) {
            MemoryVaultCipherProbeOutcome.BLOCKED
        } finally {
            cancellationFence.revoke()
            aad?.fill(0)
            tag?.fill(0)
        }
    }

    @Synchronized
    fun revoke() {
        attempted = true
        pendingCipher = null
        pendingDigest = null
        cancellationFence.revoke()
        callbackGate.revoke()
    }
}
