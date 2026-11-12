package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

private fun safeSignals() = ScreenPreflightSignals(
    trustedOwnerSession = true,
    safeUnlockedDevice = true,
    ownAccessibilityServiceEnabled = true,
    activeProjectionSession = true,
    consentIndicatorVisible = true,
    restrictedSurface = false,
    emergencyStopEngaged = false,
    sessionRevoked = false
)

/** Pure-JVM composition tests; no Android permission or device action is performed. */
class ActionPreflightCoordinatorTest {
    private class MutableSafetyProvider(
        var signals: ScreenPreflightSignals? = safeSignals(),
        var failure: RuntimeException? = null
    ) : ScreenSafetySignalProvider {
        var reads = 0
        override fun currentSignals(): ScreenPreflightSignals? {
            reads++
            failure?.let { throw it }
            return signals
        }
    }

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

    private fun coordinator(
        provider: ScreenSafetySignalProvider,
        probe: FakeProbe
    ) = ActionPreflightCoordinator(ActionPermissionGate(probe), provider)

    private val ready = ActionPreflightDecision.ReadyForIndependentAuthorization

    @Test fun readinessRequiresSafetyAndActionSpecificPlatformPolicies() {
        val provider = MutableSafetyProvider()
        val probe = FakeProbe()
        val result = coordinator(provider, probe).evaluate(
            "read_screen", OwnerActionArguments.ReadScreen
        )
        assertEquals(ready, result)
        assertEquals(1, provider.reads)
        assertEquals(1, probe.projectionReads)
        assertEquals(0, probe.launchReads + probe.enabledReads + probe.connectedReads)
    }

    @Test fun safetyDenialShortCircuitsPlatformReads() {
        val provider = MutableSafetyProvider(
            safeSignals().copy(sessionRevoked = true)
        )
        val probe = FakeProbe()
        val result = coordinator(provider, probe).evaluate(
            "read_screen", OwnerActionArguments.ReadScreen
        )
        assertEquals(
            ActionPreflightDecision.Blocked(ActionPreflightBlockReason.SAFETY_POLICY_BLOCKED),
            result
        )
        assertEquals(1, provider.reads)
        assertEquals(0, probe.projectionReads + probe.launchReads +
            probe.enabledReads + probe.connectedReads)
    }

    @Test fun platformDenialBlocksAfterSafetyPolicyPasses() {
        val provider = MutableSafetyProvider()
        val probe = FakeProbe().apply { projectionActive = false }
        val result = coordinator(provider, probe).evaluate(
            "read_screen", OwnerActionArguments.ReadScreen
        )
        assertEquals(
            ActionPreflightDecision.Blocked(
                ActionPreflightBlockReason.PLATFORM_PREREQUISITES_BLOCKED,
                ActionPermissionBlockReason.USER_APPROVED_PROJECTION_SESSION_NOT_ACTIVE
            ),
            result
        )
    }

    @Test fun nullSafetySnapshotFailsClosed() {
        val provider = MutableSafetyProvider(signals = null)
        val probe = FakeProbe()
        val result = coordinator(provider, probe).evaluate(
            "read_screen", OwnerActionArguments.ReadScreen
        )
        assertEquals(
            ActionPreflightDecision.Blocked(ActionPreflightBlockReason.SAFETY_STATE_UNAVAILABLE),
            result
        )
        assertEquals(0, probe.projectionReads)
    }

    @Test fun safetyProviderExceptionFailsClosed() {
        val provider = MutableSafetyProvider(failure = SecurityException("state unavailable"))
        val probe = FakeProbe()
        val result = coordinator(provider, probe).evaluate(
            "read_screen", OwnerActionArguments.ReadScreen
        )
        assertEquals(
            ActionPreflightDecision.Blocked(ActionPreflightBlockReason.SAFETY_STATE_UNAVAILABLE),
            result
        )
        assertEquals(0, probe.projectionReads)
    }

    @Test fun defaultSafetyProviderDeniesWithoutAnAppOwnedProvider() {
        val probe = FakeProbe()
        val result = ActionPreflightCoordinator(ActionPermissionGate(probe)).evaluate(
            "read_screen", OwnerActionArguments.ReadScreen
        )
        assertEquals(
            ActionPreflightDecision.Blocked(ActionPreflightBlockReason.SAFETY_POLICY_BLOCKED),
            result
        )
        assertEquals(0, probe.projectionReads)
    }

    @Test fun invalidArgumentsAreRejectedBeforeAnyProviderOrPlatformRead() {
        val provider = MutableSafetyProvider()
        val probe = FakeProbe()
        val result = coordinator(provider, probe).evaluate(
            "navigate", OwnerActionArguments.Navigate("not a package")
        )
        assertEquals(
            ActionPreflightDecision.Blocked(ActionPreflightBlockReason.INVALID_ACTION_ARGUMENTS),
            result
        )
        assertEquals(0, provider.reads)
        assertEquals(0, probe.launchReads + probe.enabledReads +
            probe.connectedReads + probe.projectionReads)
    }

    @Test fun navigationRequiresSafetyPolicyAndExactLaunchTarget() {
        val provider = MutableSafetyProvider()
        val probe = FakeProbe()
        assertEquals(
            ready,
            coordinator(provider, probe).evaluate(
                "navigate", OwnerActionArguments.Navigate("com.example.notes")
            )
        )
        probe.launchable = false
        val denied = coordinator(provider, probe).evaluate(
            "navigate", OwnerActionArguments.Navigate("com.example.notes")
        )
        assertEquals(
            ActionPreflightDecision.Blocked(
                ActionPreflightBlockReason.PLATFORM_PREREQUISITES_BLOCKED,
                ActionPermissionBlockReason.LAUNCH_TARGET_NOT_VISIBLE_OR_LAUNCHABLE
            ),
            denied
        )
    }

    @Test fun navigationAndScreenReadDoNotRequireAccessibilityService() {
        val provider = MutableSafetyProvider(
            safeSignals().copy(ownAccessibilityServiceEnabled = false)
        )
        val probe = FakeProbe()
        val gate = coordinator(provider, probe)

        assertEquals(
            ready,
            gate.evaluate("navigate", OwnerActionArguments.Navigate("com.example.notes"))
        )
        assertEquals(
            ready,
            gate.evaluate("read_screen", OwnerActionArguments.ReadScreen)
        )
        assertEquals(1, probe.launchReads)
        assertEquals(1, probe.projectionReads)
        assertEquals(0, probe.enabledReads + probe.connectedReads)
    }

    @Test fun scrollRequiresEnabledAndConnectedAppOwnedService() {
        val provider = MutableSafetyProvider()
        val probe = FakeProbe().apply { accessibilityConnected = false }
        val result = coordinator(provider, probe).evaluate(
            "scroll", OwnerActionArguments.Scroll("down", 80)
        )
        assertEquals(
            ActionPreflightDecision.Blocked(
                ActionPreflightBlockReason.PLATFORM_PREREQUISITES_BLOCKED,
                ActionPermissionBlockReason.ACCESSIBILITY_SERVICE_NOT_CONNECTED
            ),
            result
        )
    }

    @Test fun eachEvaluationReadsFreshSafetyAndPlatformState() {
        val provider = MutableSafetyProvider()
        val probe = FakeProbe()
        val gate = coordinator(provider, probe)
        assertEquals(
            ready,
            gate.evaluate("read_screen", OwnerActionArguments.ReadScreen)
        )
        provider.signals = safeSignals().copy(emergencyStopEngaged = true)
        assertEquals(
            ActionPreflightDecision.Blocked(ActionPreflightBlockReason.SAFETY_POLICY_BLOCKED),
            gate.evaluate("read_screen", OwnerActionArguments.ReadScreen)
        )
        assertEquals(2, provider.reads)
        assertEquals(1, probe.projectionReads)
    }

    @Test fun platformProbeExceptionRemainsFailClosed() {
        val provider = MutableSafetyProvider()
        val probe = FakeProbe().apply { failure = SecurityException("permission unavailable") }
        val result = coordinator(provider, probe).evaluate(
            "read_screen", OwnerActionArguments.ReadScreen
        )
        assertEquals(
            ActionPreflightDecision.Blocked(
                ActionPreflightBlockReason.PLATFORM_PREREQUISITES_BLOCKED,
                ActionPermissionBlockReason.PLATFORM_STATE_UNAVAILABLE
            ),
            result
        )
    }

    @Test fun unsupportedActionsNeverBecomePreflightReady() {
        val provider = MutableSafetyProvider()
        val probe = FakeProbe()
        val result = coordinator(provider, probe).evaluate("delete_data", null)
        assertTrue(result is ActionPreflightDecision.Blocked)
        assertEquals(0, provider.reads)
        assertEquals(0, probe.launchReads + probe.enabledReads +
            probe.connectedReads + probe.projectionReads)
    }
}
