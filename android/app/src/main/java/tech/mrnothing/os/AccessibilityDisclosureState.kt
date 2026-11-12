package tech.mrnothing.os

/** One canonical component identity shared by read-only disclosure and preflight checks. */
internal object AccessibilityServiceContract {
    const val COMPONENT_CLASS_NAME = "tech.mrnothing.os.OwnerScreenControlAccessibilityService"
}

internal enum class AccessibilityDisclosureStatus {
    NOT_REGISTERED,
    REGISTERED_DISABLED,
    ENABLED_IN_SETTINGS,
    UNAVAILABLE
}

/** Read-only inputs. A settings-enabled result is not proof of a live service connection. */
internal interface AccessibilityDisclosureProbe {
    fun isDeclared(): Boolean
    fun isEnabled(): Boolean
}

/** Fresh platform observations; inability to verify is reported as UNAVAILABLE, never enabled. */
internal class AccessibilityDisclosureReader(
    private val probe: AccessibilityDisclosureProbe
) {
    fun read(): AccessibilityDisclosureStatus = try {
        if (!probe.isDeclared()) AccessibilityDisclosureStatus.NOT_REGISTERED
        else if (probe.isEnabled()) AccessibilityDisclosureStatus.ENABLED_IN_SETTINGS
        else AccessibilityDisclosureStatus.REGISTERED_DISABLED
    } catch (_: SecurityException) {
        AccessibilityDisclosureStatus.UNAVAILABLE
    } catch (_: RuntimeException) {
        AccessibilityDisclosureStatus.UNAVAILABLE
    }
}
