package tech.mrnothing.os

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Pure state tests; no Android credential, StrongBox or Pixel runtime is claimed. */
class OwnerEnrollmentStateTest {
    private var now = 100L
    private fun state() = OwnerEnrollmentState { now }

    @Test fun noPendingIntentCannotEnroll() = assertFalse(state().finish(true))
    @Test fun approvedFreshIntentCanProceedOnce() {
        val s = state()
        assertTrue(s.begin())
        assertTrue(s.finish(true))
        assertFalse(s.finish(true))
    }
    @Test fun canceledCredentialIsDenied() {
        val s = state()
        assertTrue(s.begin())
        assertFalse(s.finish(false))
        assertFalse(s.finish(true))
    }
    @Test fun duplicateBeginIsDenied() {
        val s = state()
        assertTrue(s.begin())
        assertFalse(s.begin())
    }
    @Test fun expirationIsDenied() {
        val s = state()
        assertTrue(s.begin())
        now += 30_000_000_001L
        assertFalse(s.finish(true))
    }
    @Test fun boundaryIsAccepted() {
        val s = state()
        assertTrue(s.begin())
        now += 30_000_000_000L
        assertTrue(s.finish(true))
    }
    @Test fun clockRollbackIsDenied() {
        val s = state()
        assertTrue(s.begin())
        now--
        assertFalse(s.finish(true))
    }
    @Test fun revocationIsDenied() {
        val s = state()
        assertTrue(s.begin())
        s.revoke()
        assertFalse(s.finish(true))
    }
    @Test fun negativeStartClockIsDenied() {
        now = -1L
        assertFalse(state().begin())
    }
    @Test fun retryAfterCancellationRequiresNewIntent() {
        val s = state()
        assertTrue(s.begin())
        s.revoke()
        assertTrue(s.begin())
        assertTrue(s.finish(true))
    }
}
