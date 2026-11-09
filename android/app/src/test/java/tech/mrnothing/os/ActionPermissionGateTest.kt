package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

class ActionPermissionGateTest {
    private class FakeProbe : ActionPermissionProbe {
        var launchable = true
        var accessibilityEnabled = true
        var accessibilityConnected = true
        var projectionActive = true
        var failure: RuntimeException? = null
        var launchReads = 0
        var enabledReads = 0
        var connectedReads = 0
        var projectionReads = 0

        private fun failIfRequested() { failure?.let { throw it } }
        override fun isLaunchTargetVisibleAndLaunchable(packageName: String): Boolean {
            launchReads++
            failIfRequested()
            return launchable
        }
        override fun isOwnAccessibilityServiceEnabled(): Boolean {
            enabledReads++
            failIfRequested()
            return accessibilityEnabled
        }
        override fun isOwnAccessibilityServiceConnected(): Boolean {
            connectedReads++
            failIfRequested()
            return accessibilityConnected
        }
        override fun hasActiveUserApprovedProjectionSession(): Boolean {
            projectionReads++
            failIfRequested()
            return projectionActive
        }
    }

    private val ready = ActionPermissionDecision.PlatformPrerequisitesPresent
    private fun blocked(reason: ActionPermissionBlockReason) = ActionPermissionDecision.Blocked(reason)

    @Test fun navigateRequiresExactVisibleLaunchablePackage() {
        val probe = FakeProbe()
        val gate = ActionPermissionGate(probe)
        assertEquals(ready, gate.evaluate("navigate", OwnerActionArguments.Navigate("com.example.notes")))
        probe.launchable = false
        assertEquals(blocked(ActionPermissionBlockReason.LAUNCH_TARGET_NOT_VISIBLE_OR_LAUNCHABLE),
            gate.evaluate("navigate", OwnerActionArguments.Navigate("com.example.notes")))
        assertEquals(2, probe.launchReads)
        assertEquals(0, probe.enabledReads + probe.connectedReads + probe.projectionReads)
    }

    @Test fun malformedNavigationArgumentsAreRejectedBeforePlatformRead() {
        val probe = FakeProbe()
        val result = ActionPermissionGate(probe).evaluate(
            "navigate", OwnerActionArguments.Navigate("com.example notes")
        )
        assertEquals(blocked(ActionPermissionBlockReason.INVALID_ACTION_ARGUMENTS), result)
        assertEquals(0, probe.launchReads)
    }

    @Test fun scrollRequiresEnabledAndConnectedAppOwnedAccessibilityService() {
        val probe = FakeProbe()
        val gate = ActionPermissionGate(probe)
        val args = OwnerActionArguments.Scroll("down", 80)
        assertEquals(ready, gate.evaluate("scroll", args))
        probe.accessibilityEnabled = false
        assertEquals(blocked(ActionPermissionBlockReason.ACCESSIBILITY_SERVICE_DISABLED),
            gate.evaluate("scroll", args))
        probe.accessibilityEnabled = true
        probe.accessibilityConnected = false
        assertEquals(blocked(ActionPermissionBlockReason.ACCESSIBILITY_SERVICE_NOT_CONNECTED),
            gate.evaluate("scroll", args))
        assertEquals(0, probe.launchReads + probe.projectionReads)
    }

    @Test fun readScreenRequiresActiveUserApprovedProjectionSession() {
        val probe = FakeProbe()
        val gate = ActionPermissionGate(probe)
        probe.projectionActive = false
        assertEquals(blocked(ActionPermissionBlockReason.USER_APPROVED_PROJECTION_SESSION_NOT_ACTIVE),
            gate.evaluate("read_screen", OwnerActionArguments.ReadScreen))
        probe.projectionActive = true
        assertEquals(ready, gate.evaluate("read_screen", OwnerActionArguments.ReadScreen))
        assertEquals(2, probe.projectionReads)
        assertEquals(0, probe.launchReads + probe.enabledReads + probe.connectedReads)
    }

    @Test fun everyEvaluationReadsCurrentStateRatherThanCaching() {
        val probe = FakeProbe()
        val gate = ActionPermissionGate(probe)
        val args = OwnerActionArguments.Scroll("up", 120)
        assertEquals(ready, gate.evaluate("scroll", args))
        probe.accessibilityConnected = false
        assertEquals(blocked(ActionPermissionBlockReason.ACCESSIBILITY_SERVICE_NOT_CONNECTED),
            gate.evaluate("scroll", args))
        assertEquals(2, probe.enabledReads)
        assertEquals(2, probe.connectedReads)
    }

    @Test fun platformExceptionsFailClosed() {
        val probe = FakeProbe()
        val gate = ActionPermissionGate(probe)
        probe.failure = SecurityException("permission state unavailable")
        assertEquals(blocked(ActionPermissionBlockReason.PLATFORM_STATE_UNAVAILABLE),
            gate.evaluate("navigate", OwnerActionArguments.Navigate("com.example.notes")))
    }

    @Test fun invalidScrollAndUnknownActionsNeverReachPlatformProbe() {
        val probe = FakeProbe()
        val gate = ActionPermissionGate(probe)
        assertEquals(blocked(ActionPermissionBlockReason.INVALID_ACTION_ARGUMENTS),
            gate.evaluate("scroll", OwnerActionArguments.Scroll("sideways", 50)))
        assertEquals(blocked(ActionPermissionBlockReason.INVALID_ACTION_ARGUMENTS),
            gate.evaluate("scroll", OwnerActionArguments.Scroll("down", 0)))
        assertEquals(blocked(ActionPermissionBlockReason.INVALID_ACTION_ARGUMENTS),
            gate.evaluate("open_app", OwnerActionArguments.Navigate("com.example.notes")))
        assertEquals(0, probe.launchReads + probe.enabledReads + probe.connectedReads + probe.projectionReads)
    }
}
