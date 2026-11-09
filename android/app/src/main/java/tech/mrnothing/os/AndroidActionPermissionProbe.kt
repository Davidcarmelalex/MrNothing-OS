package tech.mrnothing.os

import android.content.Context
import android.content.pm.PackageManager

/** Runtime observation supplied only by the app-owned AccessibilityService when one exists. */
internal fun interface AccessibilityServiceConnectionProbe {
    fun isConnected(packageName: String): Boolean
}

/** Runtime observation supplied only by an app-owned MediaProjection session manager. */
internal fun interface UserApprovedProjectionSessionProbe {
    fun isActive(packageName: String): Boolean
}

/**
 * Read-only Android framework adapter for ActionPermissionGate.
 *
 * The two session probes default to DENY because this repository does not yet
 * declare an AccessibilityService or own a MediaProjection foreground service.
 * No permission prompt, service enablement, capture, navigation or UI action is
 * performed here. Implementations must be app-owned; never derive these probes
 * from agent/request data.
 */
internal class AndroidActionPermissionProbe(
    context: Context,
    private val accessibilityConnectionProbe: AccessibilityServiceConnectionProbe =
        AccessibilityServiceConnectionProbe { false },
    private val projectionSessionProbe: UserApprovedProjectionSessionProbe =
        UserApprovedProjectionSessionProbe { false }
) : ActionPermissionProbe {
    private val appContext = context.applicationContext ?: context

    override fun isLaunchTargetVisibleAndLaunchable(packageName: String): Boolean {
        if (OwnerActionArgumentsCanonicalizer.canonicalJson(
                "navigate", OwnerActionArguments.Navigate(packageName)
            ) == null
        ) return false
        return try {
            val manager = appContext.packageManager
            val launchIntent = manager.getLaunchIntentForPackage(packageName) ?: return false
            val component = launchIntent.component ?: return false
            if (component.packageName != packageName || component.className.isBlank()) return false
            val activity = manager.getActivityInfo(component, 0)
            val requiredPermission = activity.permission
            val callerHasRequiredPermission = requiredPermission == null ||
                manager.checkPermission(requiredPermission, appContext.packageName) ==
                PackageManager.PERMISSION_GRANTED
            activity.exported && activity.enabled && activity.applicationInfo.enabled &&
                callerHasRequiredPermission
        } catch (_: PackageManager.NameNotFoundException) {
            false
        } catch (_: SecurityException) {
            false
        } catch (_: RuntimeException) {
            false
        }
    }

    override fun isOwnAccessibilityServiceEnabled(): Boolean =
        ScreenActionPreflight.isOwnAccessibilityServiceEnabled(appContext)

    override fun isOwnAccessibilityServiceConnected(): Boolean = try {
        accessibilityConnectionProbe.isConnected(appContext.packageName)
    } catch (_: SecurityException) {
        false
    } catch (_: RuntimeException) {
        false
    }

    override fun hasActiveUserApprovedProjectionSession(): Boolean = try {
        projectionSessionProbe.isActive(appContext.packageName)
    } catch (_: SecurityException) {
        false
    } catch (_: RuntimeException) {
        false
    }
}

/** Convenience wrapper; it is not wired into any request dispatcher or executor. */
internal class AndroidActionPermissionGate(
    context: Context,
    accessibilityConnectionProbe: AccessibilityServiceConnectionProbe =
        AccessibilityServiceConnectionProbe { false },
    projectionSessionProbe: UserApprovedProjectionSessionProbe =
        UserApprovedProjectionSessionProbe { false }
) {
    private val delegate = ActionPermissionGate(
        AndroidActionPermissionProbe(
            context,
            accessibilityConnectionProbe,
            projectionSessionProbe
        )
    )

    fun evaluate(action: String, arguments: OwnerActionArguments?): ActionPermissionDecision =
        delegate.evaluate(action, arguments)
}
