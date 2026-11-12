package tech.mrnothing.os

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.view.accessibility.AccessibilityManager

/**
 * SEC-014F: fail-closed prerequisites for FUTURE screen integrations.
 *
 * This is NOT an authorization API. PRECONDITIONS_PRESENT means a separate
 * trusted, owner-bound, one-use capability verifier and a live Android
 * permission check must still approve the action. No executor calls this.
 * Never populate these signals from an agent/LLM/remote command payload.
 */
internal enum class ScreenPreflightResult { BLOCKED, PRECONDITIONS_PRESENT }

internal data class ScreenPreflightSignals(
    val trustedOwnerSession: Boolean,
    val safeUnlockedDevice: Boolean,
    val ownAccessibilityServiceEnabled: Boolean,
    val activeProjectionSession: Boolean,
    val consentIndicatorVisible: Boolean,
    val restrictedSurface: Boolean,
    val emergencyStopEngaged: Boolean,
    val sessionRevoked: Boolean
)

internal object ScreenActionPreflight {
    private const val OWN_SERVICE = AccessibilityServiceContract.COMPONENT_CLASS_NAME

    fun evaluate(action: String, signals: ScreenPreflightSignals): ScreenPreflightResult {
        // These signals are common to every action. Sensitive platform
        // prerequisites are checked only by the action that actually needs them.
        if (!signals.trustedOwnerSession ||
            !signals.safeUnlockedDevice ||
            !signals.consentIndicatorVisible ||
            signals.restrictedSurface ||
            signals.emergencyStopEngaged ||
            signals.sessionRevoked
        ) return ScreenPreflightResult.BLOCKED

        return when (action) {
            // Screen capture uses the separately user-approved projection
            // session; it does not require an AccessibilityService.
            "read_screen" -> if (signals.activeProjectionSession) {
                ScreenPreflightResult.PRECONDITIONS_PRESENT
            } else ScreenPreflightResult.BLOCKED

            // App launch is performed through an exact, exported launch target
            // check in ActionPermissionGate, not through accessibility control.
            "navigate" -> ScreenPreflightResult.PRECONDITIONS_PRESENT

            // Scroll is the only current action that uses our AccessibilityService.
            "scroll" -> if (signals.ownAccessibilityServiceEnabled) {
                ScreenPreflightResult.PRECONDITIONS_PRESENT
            } else ScreenPreflightResult.BLOCKED

            else -> ScreenPreflightResult.BLOCKED
        }
    }

    /**
     * Read-only platform observation. The expected service is deliberately NOT
     * declared in the manifest yet; consequently this returns false in the
     * current launcher. It never enables a service or requests permissions.
     */
    fun isOwnAccessibilityServiceEnabled(context: Context): Boolean {
        return try {
            val manager = context.getSystemService(AccessibilityManager::class.java)
                ?: return false
            manager.getEnabledAccessibilityServiceList(
                AccessibilityServiceInfo.FEEDBACK_ALL_MASK
            ).any { service ->
                val info = service.resolveInfo?.serviceInfo
                info != null &&
                    info.packageName == context.packageName &&
                    info.name == OWN_SERVICE
            }
        } catch (_: SecurityException) {
            false
        } catch (_: RuntimeException) {
            false
        }
    }
}
