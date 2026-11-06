package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

/** Pure policy tests only; no Android permission or real screen action tested. */
class ScreenActionPreflightTest {
    private val blocked = ScreenPreflightResult.BLOCKED
    private val ready = ScreenPreflightResult.PRECONDITIONS_PRESENT

    private fun safe() = ScreenPreflightSignals(
        trustedOwnerSession = true,
        safeUnlockedDevice = true,
        ownAccessibilityServiceEnabled = true,
        activeProjectionSession = true,
        consentIndicatorVisible = true,
        restrictedSurface = false,
        emergencyStopEngaged = false,
        sessionRevoked = false
    )

    @Test fun requiresAllPrerequisitesForScreenRead() {
        assertEquals(ready, ScreenActionPreflight.evaluate("read_screen", safe()))
    }

    @Test fun screenReadRequiresProjection() {
        assertEquals(blocked, ScreenActionPreflight.evaluate(
            "read_screen", safe().copy(activeProjectionSession = false)))
    }

    @Test fun navigationRequiresOwnEnabledAccessibilityService() {
        assertEquals(blocked, ScreenActionPreflight.evaluate(
            "navigate", safe().copy(ownAccessibilityServiceEnabled = false)))
    }

    @Test fun scrollRequiresOwnEnabledAccessibilityService() {
        assertEquals(blocked, ScreenActionPreflight.evaluate(
            "scroll", safe().copy(ownAccessibilityServiceEnabled = false)))
    }

    @Test fun navigationDoesNotTreatProjectionAsAccessibilityPermission() {
        assertEquals(ready, ScreenActionPreflight.evaluate(
            "navigate", safe().copy(activeProjectionSession = false)))
    }

    @Test fun everyUnsafeCommonSignalBlocksAllScreenActions() {
        val unsafe = listOf(
            safe().copy(trustedOwnerSession = false),
            safe().copy(safeUnlockedDevice = false),
            safe().copy(ownAccessibilityServiceEnabled = false),
            safe().copy(consentIndicatorVisible = false),
            safe().copy(restrictedSurface = true),
            safe().copy(emergencyStopEngaged = true),
            safe().copy(sessionRevoked = true)
        )
        for (signal in unsafe) for (action in listOf("read_screen", "navigate", "scroll")) {
            assertEquals("$action must fail closed", blocked,
                ScreenActionPreflight.evaluate(action, signal))
        }
    }

    @Test fun unknownAndNonScreenActionsNeverPass() {
        for (action in listOf("", "READ_SCREEN", "open_app", "place_call", "delete_data")) {
            assertEquals(blocked, ScreenActionPreflight.evaluate(action, safe()))
        }
    }

    @Test fun ownerSessionMustBeTrustedNotMerelyDeviceUnlocked() {
        assertEquals(blocked, ScreenActionPreflight.evaluate(
            "navigate", safe().copy(trustedOwnerSession = false)))
    }

    @Test fun revocationBlocksEvenWhenPermissionsRemainEnabled() {
        assertEquals(blocked, ScreenActionPreflight.evaluate(
            "read_screen", safe().copy(sessionRevoked = true)))
    }

    @Test fun restrictedSurfaceBlocksEvenWithProjection() {
        assertEquals(blocked, ScreenActionPreflight.evaluate(
            "read_screen", safe().copy(restrictedSurface = true)))
    }
}
