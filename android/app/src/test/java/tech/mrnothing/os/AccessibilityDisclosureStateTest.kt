package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AccessibilityDisclosureStateTest {
    private class FakeProbe(
        private val declared: Boolean,
        private val enabled: Boolean,
        private val declarationFailure: RuntimeException? = null,
        private val enabledFailure: RuntimeException? = null
    ) : AccessibilityDisclosureProbe {
        var enabledReads = 0
        override fun isDeclared(): Boolean {
            declarationFailure?.let { throw it }
            return declared
        }
        override fun isEnabled(): Boolean {
            enabledReads += 1
            enabledFailure?.let { throw it }
            return enabled
        }
    }

    @Test fun unregisteredServiceIsReportedWithoutQueryingEnabledState() {
        val probe = FakeProbe(false, true)
        assertEquals(AccessibilityDisclosureStatus.NOT_REGISTERED, AccessibilityDisclosureReader(probe).read())
        assertEquals(0, probe.enabledReads)
    }

    @Test fun registeredButDisabledServiceIsReportedAsDisabled() {
        assertEquals(AccessibilityDisclosureStatus.REGISTERED_DISABLED, AccessibilityDisclosureReader(FakeProbe(true, false)).read())
    }

    @Test fun enabledStatusDoesNotCreateAuthorization() {
        assertEquals(AccessibilityDisclosureStatus.ENABLED_IN_SETTINGS, AccessibilityDisclosureReader(FakeProbe(true, true)).read())
    }

    @Test fun securityFailureFailsClosed() {
        assertEquals(
            AccessibilityDisclosureStatus.UNAVAILABLE,
            AccessibilityDisclosureReader(FakeProbe(true, false, enabledFailure = SecurityException("denied"))).read()
        )
    }

    @Test fun runtimeFailureDuringDeclarationFailsClosed() {
        assertEquals(
            AccessibilityDisclosureStatus.UNAVAILABLE,
            AccessibilityDisclosureReader(FakeProbe(false, false, declarationFailure = IllegalStateException("unavailable"))).read()
        )
    }

    @Test fun enabledProbeIsReadFreshForEveryEvaluation() {
        val probe = FakeProbe(true, true)
        val reader = AccessibilityDisclosureReader(probe)
        assertEquals(AccessibilityDisclosureStatus.ENABLED_IN_SETTINGS, reader.read())
        assertEquals(AccessibilityDisclosureStatus.ENABLED_IN_SETTINGS, reader.read())
        assertEquals(2, probe.enabledReads)
        assertTrue(probe.enabledReads > 0)
    }
}
