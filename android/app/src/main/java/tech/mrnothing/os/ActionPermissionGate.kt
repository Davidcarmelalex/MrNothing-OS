package tech.mrnothing.os

/** Read-only Android platform observations; none of these signals is owner consent. */
internal interface ActionPermissionProbe {
    fun isLaunchTargetVisibleAndLaunchable(packageName: String): Boolean
    fun isOwnAccessibilityServiceEnabled(): Boolean
    fun isOwnAccessibilityServiceConnected(): Boolean
    fun hasActiveUserApprovedProjectionSession(): Boolean
}

internal enum class ActionPermissionBlockReason {
    INVALID_ACTION_ARGUMENTS,
    LAUNCH_TARGET_NOT_VISIBLE_OR_LAUNCHABLE,
    ACCESSIBILITY_SERVICE_DISABLED,
    ACCESSIBILITY_SERVICE_NOT_CONNECTED,
    USER_APPROVED_PROJECTION_SESSION_NOT_ACTIVE,
    PLATFORM_STATE_UNAVAILABLE
}

/**
 * A positive result means only that the action-specific platform prerequisites
 * were observed. It is not authentication, owner consent, authorization, or
 * permission to dispatch. Every call performs fresh probe reads; no result is cached.
 */
internal sealed interface ActionPermissionDecision {
    data object PlatformPrerequisitesPresent : ActionPermissionDecision
    data class Blocked(val reason: ActionPermissionBlockReason) : ActionPermissionDecision
}

/** Pure-JVM policy boundary, deliberately independent of Android framework classes. */
internal class ActionPermissionGate(private val probe: ActionPermissionProbe) {
    fun evaluate(action: String, arguments: OwnerActionArguments?): ActionPermissionDecision {
        if (OwnerActionArgumentsCanonicalizer.canonicalJson(action, arguments) == null) {
            return ActionPermissionDecision.Blocked(
                ActionPermissionBlockReason.INVALID_ACTION_ARGUMENTS
            )
        }
        return try {
            when (arguments) {
                OwnerActionArguments.ReadScreen -> if (probe.hasActiveUserApprovedProjectionSession()) {
                    ActionPermissionDecision.PlatformPrerequisitesPresent
                } else {
                    ActionPermissionDecision.Blocked(
                        ActionPermissionBlockReason.USER_APPROVED_PROJECTION_SESSION_NOT_ACTIVE
                    )
                }
                is OwnerActionArguments.Navigate -> if (
                    probe.isLaunchTargetVisibleAndLaunchable(arguments.targetPackage)
                ) {
                    ActionPermissionDecision.PlatformPrerequisitesPresent
                } else {
                    ActionPermissionDecision.Blocked(
                        ActionPermissionBlockReason.LAUNCH_TARGET_NOT_VISIBLE_OR_LAUNCHABLE
                    )
                }
                is OwnerActionArguments.Scroll -> when {
                    !probe.isOwnAccessibilityServiceEnabled() ->
                        ActionPermissionDecision.Blocked(
                            ActionPermissionBlockReason.ACCESSIBILITY_SERVICE_DISABLED
                        )
                    !probe.isOwnAccessibilityServiceConnected() ->
                        ActionPermissionDecision.Blocked(
                            ActionPermissionBlockReason.ACCESSIBILITY_SERVICE_NOT_CONNECTED
                        )
                    else -> ActionPermissionDecision.PlatformPrerequisitesPresent
                }
                null -> ActionPermissionDecision.Blocked(
                    ActionPermissionBlockReason.INVALID_ACTION_ARGUMENTS
                )
            }
        } catch (_: SecurityException) {
            ActionPermissionDecision.Blocked(ActionPermissionBlockReason.PLATFORM_STATE_UNAVAILABLE)
        } catch (_: RuntimeException) {
            ActionPermissionDecision.Blocked(ActionPermissionBlockReason.PLATFORM_STATE_UNAVAILABLE)
        }
    }
}
