package tech.mrnothing.os

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class OwnerAuthorityConfirmationStateTest {
    private var now = 10L
    private val state = OwnerAuthorityConfirmationState { now }

    @Test fun requiresNonBlankBindingAndNonNegativeClock() {
        assertFalse(state.begin(""))
        now = -1L
        assertFalse(state.begin("binding"))
    }

    @Test fun acceptsOnlyMatchingFreshCredentialResult() {
        assertTrue(state.begin("binding-a"))
        now += 1_000L
        assertTrue(state.finish("binding-a", credentialApproved = true))
    }

    @Test fun mismatchedBindingConsumesPendingRequest() {
        assertTrue(state.begin("binding-a"))
        assertFalse(state.finish("binding-b", credentialApproved = true))
        assertFalse(state.finish("binding-a", credentialApproved = true))
    }

    @Test fun deniedCredentialConsumesPendingRequest() {
        assertTrue(state.begin("binding-a"))
        assertFalse(state.finish("binding-a", credentialApproved = false))
        assertFalse(state.finish("binding-a", credentialApproved = true))
    }

    @Test fun expiredCredentialConsumesPendingRequest() {
        assertTrue(state.begin("binding-a"))
        now += OwnerAuthorityConfirmationState.MAX_AGE_NANOS + 1L
        assertFalse(state.finish("binding-a", credentialApproved = true))
    }

    @Test fun clockRollbackConsumesPendingRequest() {
        assertTrue(state.begin("binding-a"))
        now = 9L
        assertFalse(state.finish("binding-a", credentialApproved = true))
    }

    @Test fun onlyOneRequestMayBePending() {
        assertTrue(state.begin("binding-a"))
        assertFalse(state.begin("binding-b"))
        state.revoke()
        assertTrue(state.begin("binding-b"))
    }

    @Test fun explicitRevokePreventsLaterCompletion() {
        assertTrue(state.begin("binding-a"))
        state.revoke()
        assertFalse(state.finish("binding-a", credentialApproved = true))
    }
}
