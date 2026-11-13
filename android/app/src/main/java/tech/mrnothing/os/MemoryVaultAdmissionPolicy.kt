package tech.mrnothing.os

import java.nio.charset.StandardCharsets
import java.security.MessageDigest

/**
 * SEC-023B0: pure, in-process preflight for a future private Android MemoryVault.
 *
 * Every field must originate from a trusted Android platform/owner-UI adapter,
 * never from a Binder parcel, agent plan, remote message, or model output.
 * A Boolean reporting cryptographic authentication is NOT itself a proof:
 * the future native implementation must validate the actual Keystore
 * CryptoObject operation before supplying authenticatedKeyUse=true.
 *
 * This file has no Android service, IPC, storage, key access, or executor.
 */
internal enum class MemoryVaultOperation { READ, WRITE, EXPORT, DELETE }

internal data class MemoryVaultTrustedSnapshot(
    val callingUid: Int,
    val applicationUid: Int,
    val callingUserId: Int,
    val ownerUserId: Int,
    val callingSigningSha256: String,
    val applicationSigningSha256: String,
    val foregroundOwnerUi: Boolean,
    val deviceUnlocked: Boolean,
    val explicitMemoryConsent: Boolean,
    val authenticatedKeyUse: Boolean
)

internal object MemoryVaultAdmissionPolicy {
    private val digestPattern = Regex("^[0-9a-f]{64}$")

    /** Preconditions for presenting an explicit owner-authentication prompt. */
    fun canRequestAuthentication(snapshot: MemoryVaultTrustedSnapshot): Boolean {
        if (snapshot.callingUid <= 0 || snapshot.callingUid != snapshot.applicationUid ||
            snapshot.callingUserId != 0 || snapshot.ownerUserId != 0 ||
            !snapshot.foregroundOwnerUi || !snapshot.deviceUnlocked ||
            !snapshot.explicitMemoryConsent
        ) return false

        val caller = snapshot.callingSigningSha256
        val expected = snapshot.applicationSigningSha256
        return digestPattern.matches(caller) && digestPattern.matches(expected) &&
            MessageDigest.isEqual(
                caller.toByteArray(StandardCharsets.US_ASCII),
                expected.toByteArray(StandardCharsets.US_ASCII)
            )
    }

    /** Additional prerequisite only; not a substitute for Keystore CryptoObject proof. */
    fun canUseKey(snapshot: MemoryVaultTrustedSnapshot): Boolean =
        canRequestAuthentication(snapshot) && snapshot.authenticatedKeyUse
}

/**
 * One outstanding process-local owner intent. Tokens use object identity, not
 * caller-controlled IDs; they must NEVER be serialized or accepted over IPC.
 * Process death, cancellation, replacement, expiration, or clock rollback
 * destroys the intent. This is not a persistent replay ledger.
 */
internal class MemoryVaultOwnerIntentRegistry(
    private val elapsedRealtimeMillis: () -> Long
) {
    internal class IntentToken private constructor(
        internal val operation: MemoryVaultOperation,
        internal val callingUid: Int,
        internal val ownerUserId: Int,
        internal val signingSha256: String,
        internal val expiresAtMillis: Long
    ) {
        companion object {
            internal fun create(
                operation: MemoryVaultOperation,
                callingUid: Int,
                ownerUserId: Int,
                signingSha256: String,
                expiresAtMillis: Long
            ): IntentToken = IntentToken(
                operation, callingUid, ownerUserId, signingSha256, expiresAtMillis
            )
        }
    }

    private val lock = Any()
    private var active: IntentToken? = null
    private var lastObservedMillis = -1L
    private var closed = false

    private fun observedTime(): Long? {
        val now = try {
            elapsedRealtimeMillis()
        } catch (_: RuntimeException) {
            active = null
            return null
        }
        if (now < 0L || now < lastObservedMillis) {
            active = null
            return null
        }
        lastObservedMillis = now
        return now
    }

    fun begin(
        operation: MemoryVaultOperation,
        snapshot: MemoryVaultTrustedSnapshot
    ): IntentToken? = synchronized(lock) {
        if (closed || !MemoryVaultAdmissionPolicy.canRequestAuthentication(snapshot)) {
            active = null
            return@synchronized null
        }
        val now = observedTime() ?: return@synchronized null
        if (now > Long.MAX_VALUE - MAX_INTENT_AGE_MILLIS) {
            active = null
            return@synchronized null
        }
        IntentToken.create(
            operation, snapshot.callingUid, snapshot.ownerUserId,
            snapshot.applicationSigningSha256, now + MAX_INTENT_AGE_MILLIS
        ).also { active = it }
    }

    /**
     * Consumes the exact intent once, including when the trusted preflight
     * fails. The caller must separately prove a successful Keystore operation.
     */
    fun claim(
        token: IntentToken,
        operation: MemoryVaultOperation,
        snapshot: MemoryVaultTrustedSnapshot
    ): Boolean = synchronized(lock) {
        if (closed || active !== token) return@synchronized false
        active = null
        val now = observedTime() ?: return@synchronized false
        now < token.expiresAtMillis &&
            token.operation == operation &&
            token.callingUid == snapshot.callingUid &&
            token.ownerUserId == snapshot.ownerUserId &&
            token.signingSha256 == snapshot.applicationSigningSha256 &&
            MemoryVaultAdmissionPolicy.canUseKey(snapshot)
    }

    fun cancel() = synchronized(lock) { active = null }

    fun close() = synchronized(lock) {
        active = null
        closed = true
    }

    private companion object {
        const val MAX_INTENT_AGE_MILLIS = 30_000L
    }
}
