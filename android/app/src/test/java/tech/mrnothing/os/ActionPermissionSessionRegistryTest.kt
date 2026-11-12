package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ActionPermissionSessionRegistryTest {
    private val ownerPackage = "tech.mrnothing.os"

    @Test fun initialStateAndProbesFailClosed() {
        val registry = ActionPermissionSessionRegistry(ownerPackage)
        assertFalse(registry.isActive(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage))
        assertFalse(registry.isActive(ActionPermissionSessionKind.PROJECTION, ownerPackage))
        assertFalse(registry.accessibilityConnectionProbe().isConnected(ownerPackage))
        assertFalse(registry.projectionSessionProbe().isActive(ownerPackage))
    }

    @Test fun beginRequiresExactExpectedPackage() {
        val registry = ActionPermissionSessionRegistry(ownerPackage)
        assertNull(registry.begin(ActionPermissionSessionKind.ACCESSIBILITY, "tech.mrnothing.other"))
        assertFalse(registry.isActive(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage))
    }

    @Test fun onlyExpectedPackageCanObserveAnActiveSession() {
        val registry = ActionPermissionSessionRegistry(ownerPackage)
        registry.begin(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage)!!
        assertTrue(registry.isActive(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage))
        assertFalse(registry.isActive(ActionPermissionSessionKind.ACCESSIBILITY, "tech.mrnothing.other"))
    }

    @Test fun endingCurrentLeaseRevokesTheSession() {
        val registry = ActionPermissionSessionRegistry(ownerPackage)
        val lease = registry.begin(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage)!!
        assertTrue(registry.end(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage, lease))
        assertFalse(registry.isActive(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage))
        assertFalse(registry.end(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage, lease))
    }

    @Test fun staleDisconnectCannotRevokeReplacementSession() {
        val registry = ActionPermissionSessionRegistry(ownerPackage)
        val oldLease = registry.begin(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage)!!
        val currentLease = registry.begin(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage)!!
        assertTrue(currentLease.generation > oldLease.generation)
        assertFalse(registry.end(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage, oldLease))
        assertTrue(registry.isActive(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage))
        assertTrue(registry.end(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage, currentLease))
    }

    @Test fun accessibilityAndProjectionSessionsAreIndependent() {
        val registry = ActionPermissionSessionRegistry(ownerPackage)
        val accessibility = registry.begin(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage)!!
        val projection = registry.begin(ActionPermissionSessionKind.PROJECTION, ownerPackage)!!
        assertTrue(registry.isActive(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage))
        assertTrue(registry.isActive(ActionPermissionSessionKind.PROJECTION, ownerPackage))
        assertFalse(registry.end(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage, projection))
        assertTrue(registry.isActive(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage))
        assertTrue(registry.end(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage, accessibility))
        assertTrue(registry.isActive(ActionPermissionSessionKind.PROJECTION, ownerPackage))
    }

    @Test fun wrongPackageOrKindCannotEndLease() {
        val registry = ActionPermissionSessionRegistry(ownerPackage)
        val lease = registry.begin(ActionPermissionSessionKind.PROJECTION, ownerPackage)!!
        assertFalse(registry.end(ActionPermissionSessionKind.PROJECTION, "tech.mrnothing.other", lease))
        assertFalse(registry.end(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage, lease))
        assertTrue(registry.isActive(ActionPermissionSessionKind.PROJECTION, ownerPackage))
    }

    @Test fun probeAdaptersReflectCurrentLifecycleState() {
        val registry = ActionPermissionSessionRegistry(ownerPackage)
        val accessibilityProbe = registry.accessibilityConnectionProbe()
        val projectionProbe = registry.projectionSessionProbe()
        assertFalse(accessibilityProbe.isConnected(ownerPackage))
        assertFalse(projectionProbe.isActive(ownerPackage))
        val accessibility = registry.begin(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage)!!
        assertTrue(accessibilityProbe.isConnected(ownerPackage))
        assertFalse(projectionProbe.isActive(ownerPackage))
        registry.end(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage, accessibility)
        assertFalse(accessibilityProbe.isConnected(ownerPackage))
        val projection = registry.begin(ActionPermissionSessionKind.PROJECTION, ownerPackage)!!
        assertTrue(projectionProbe.isActive(ownerPackage))
        registry.end(ActionPermissionSessionKind.PROJECTION, ownerPackage, projection)
        assertFalse(projectionProbe.isActive(ownerPackage))
    }

    @Test fun generationIsMonotonicAcrossSessionKinds() {
        val registry = ActionPermissionSessionRegistry(ownerPackage)
        val first = registry.begin(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage)!!
        val second = registry.begin(ActionPermissionSessionKind.PROJECTION, ownerPackage)!!
        val third = registry.begin(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage)!!
        assertEquals(1L, first.generation)
        assertEquals(2L, second.generation)
        assertEquals(3L, third.generation)
    }

    @Test fun processRecreationStartsWithNoRestoredSessions() {
        val original = ActionPermissionSessionRegistry(ownerPackage)
        original.begin(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage)!!
        original.begin(ActionPermissionSessionKind.PROJECTION, ownerPackage)!!
        val restarted = ActionPermissionSessionRegistry(ownerPackage)
        assertFalse(restarted.isActive(ActionPermissionSessionKind.ACCESSIBILITY, ownerPackage))
        assertFalse(restarted.isActive(ActionPermissionSessionKind.PROJECTION, ownerPackage))
    }

    @Test fun invalidExpectedPackageIsRejected() {
        val result = runCatching { ActionPermissionSessionRegistry("bad package") }
        assertTrue(result.isFailure)
    }
}
