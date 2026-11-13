package tech.mrnothing.os

import android.hardware.biometrics.BiometricPrompt
import android.os.Build
import android.os.SystemClock

/**
 * SEC-023B1B2D0: dormant, one-shot binding of a framework credential callback
 * to the exact CryptoObject and Cipher submitted to BiometricPrompt.
 *
 * A matching callback is NOT cryptographic proof. In particular, a software
 * Cipher can satisfy identity checks. A future trusted Activity must independently
 * obtain the key from AndroidKeyStore, verify its StrongBox metadata, run the
 * authenticated Cipher operation with the consent digest as AAD, and verify
 * the resulting operation before permitting any storage. This class neither
 * invokes a prompt nor performs any cryptographic operation.
 */
internal enum class MemoryVaultCryptoCallbackProgress {
    BLOCKED,
    AWAITING_AUTHENTICATED_CIPHER_OPERATION
}

/** Pure JVM state machine. Caller-provided objects/types are NOT trusted evidence. */
internal class MemoryVaultCryptoObjectBindingState(
    private val clockNanos: () -> Long
) {
    private data class Pending(
        val consentDigest: String,
        val promptObject: Any,
        val cipher: Any,
        val startedNanos: Long
    )
    private var attempted = false
    private var pending: Pending? = null
    private val digestFormat = Regex("^[0-9a-f]{64}$")

    @Synchronized
    fun arm(consentDigest: String, promptObject: Any?, cipher: Any?): Boolean {
        if (attempted) return false
        attempted = true
        if (!digestFormat.matches(consentDigest) || promptObject == null || cipher == null) {
            return false
        }
        val now = try { clockNanos() } catch (_: RuntimeException) { return false }
        if (now < 0L) return false
        pending = Pending(consentDigest, promptObject, cipher, now)
        return true
    }

    /** Always consumes the request, even on mismatch, cancellation or clock error. */
    @Synchronized
    fun consume(
        consentDigest: String,
        resultObject: Any?,
        resultCipher: Any?,
        authenticationType: Int,
        credentialType: Int
    ): MemoryVaultCryptoCallbackProgress {
        val active = pending ?: return MemoryVaultCryptoCallbackProgress.BLOCKED
        pending = null
        val now = try { clockNanos() } catch (_: RuntimeException) {
            return MemoryVaultCryptoCallbackProgress.BLOCKED
        }
        return if (
            now >= active.startedNanos &&
            now - active.startedNanos <= MAX_AGE_NANOS &&
            consentDigest == active.consentDigest &&
            resultObject === active.promptObject &&
            resultCipher === active.cipher &&
            authenticationType == credentialType
        ) MemoryVaultCryptoCallbackProgress.AWAITING_AUTHENTICATED_CIPHER_OPERATION
        else MemoryVaultCryptoCallbackProgress.BLOCKED
    }

    @Synchronized
    fun revoke() {
        attempted = true
        pending = null
    }

    companion object {
        const val MAX_AGE_NANOS = 30_000_000_000L
    }
}

/**
 * Android framework adapter: derive result type and CryptoObject directly from
 * the actual BiometricPrompt callback, never from agent or UI-reported booleans.
 * This adapter is intentionally unconnected to Activities and MemoryVaultService.
 */
internal class MemoryVaultCryptoObjectCallbackGate(
    clockNanos: () -> Long = { SystemClock.elapsedRealtimeNanos() }
) {
    private val binding = MemoryVaultCryptoObjectBindingState(clockNanos)

    fun arm(
        consentProgress: MemoryVaultConsentProgress,
        consentDigest: String,
        promptObject: BiometricPrompt.CryptoObject?
    ): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S ||
            consentProgress != MemoryVaultConsentProgress.AWAITING_CRYPTOOBJECT_PROOF
        ) {
            binding.revoke()
            return false
        }
        val cipher = promptObject?.cipher
        if (cipher?.algorithm != "AES/GCM/NoPadding" || cipher.iv?.size != 12) {
            binding.revoke()
            return false
        }
        return binding.arm(consentDigest, promptObject, cipher)
    }

    fun consume(
        consentDigest: String,
        result: BiometricPrompt.AuthenticationResult?
    ): MemoryVaultCryptoCallbackProgress {
        val resultObject = result?.cryptoObject
        return binding.consume(
            consentDigest,
            resultObject,
            resultObject?.cipher,
            result?.authenticationType ?: -1,
            BiometricPrompt.AUTHENTICATION_RESULT_TYPE_DEVICE_CREDENTIAL
        )
    }

    fun revoke() = binding.revoke()
}
