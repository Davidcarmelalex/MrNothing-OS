package tech.mrnothing.os

import android.app.KeyguardManager
import android.content.Context
import android.os.PowerManager
import android.os.UserManager

/**
 * SEC-014D: real Android lock/user/interactive-state preflight for a credential
 * PREVIEW ONLY. This is not owner enrollment, consent, or action authorization.
 * Never accept these signals from an LLM, a command payload, or a remote peer.
 */
internal data class CredentialSafetySignals(
    val secureLockConfigured: Boolean,
    val deviceLocked: Boolean,
    val keyguardLocked: Boolean,
    val userUnlocked: Boolean,
    val screenInteractive: Boolean
)

internal object OwnerCredentialSafetyGate {
    fun eligible(signals: CredentialSafetySignals): Boolean =
        signals.secureLockConfigured &&
            !signals.deviceLocked &&
            !signals.keyguardLocked &&
            signals.userUnlocked &&
            signals.screenInteractive

    /** Null services and failed platform reads are denied, never assumed safe. */
    fun isSafe(context: Context): Boolean = try {
        val keyguard = context.getSystemService(KeyguardManager::class.java)
        val power = context.getSystemService(PowerManager::class.java)
        val user = context.getSystemService(UserManager::class.java)
        keyguard != null && power != null && user != null &&
            eligible(
                CredentialSafetySignals(
                    secureLockConfigured = keyguard.isDeviceSecure,
                    deviceLocked = keyguard.isDeviceLocked,
                    keyguardLocked = keyguard.isKeyguardLocked,
                    userUnlocked = user.isUserUnlocked,
                    screenInteractive = power.isInteractive
                )
            )
    } catch (_: RuntimeException) {
        false
    }
}
