package tech.mrnothing.os

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ConsentPreviewStateTest {
    private var now = 1_000_000_000_000L
    private fun state() = ConsentPreviewState { now }
    @Test fun unsupportedActionsDenied() {
        val s = state()
        assertFalse(s.begin("transfer_money"))
        assertFalse(s.begin("open_app"))
        assertFalse(s.finish(true))
    }
    @Test fun oneTimePreview() {
        val s = state()
        assertTrue(s.begin("read_screen"))
        assertTrue(s.finish(true))
        assertFalse(s.finish(true))
    }
    @Test fun cancellationDenied() {
        val s = state()
        assertTrue(s.begin("navigate"))
        assertFalse(s.finish(false))
        assertFalse(s.finish(true))
    }
    @Test fun revocationDenied() {
        val s = state()
        assertTrue(s.begin("scroll"))
        s.revoke()
        assertFalse(s.finish(true))
    }
    @Test fun expiryDenied() {
        val s = state()
        assertTrue(s.begin("navigate"))
        now += 30_000_000_001L
        assertFalse(s.finish(true))
    }
    @Test fun rollbackDenied() {
        val s = state()
        assertTrue(s.begin("navigate"))
        now--
        assertFalse(s.finish(true))
    }
    @Test fun overlappingPreviewDenied() {
        val s = state()
        assertTrue(s.begin("read_screen"))
        assertFalse(s.begin("scroll"))
        s.revoke()
        assertTrue(s.begin("scroll"))
    }
    @Test fun exactExpiryBoundaryAcceptedForPreviewOnly() {
        val s = state()
        assertTrue(s.begin("scroll"))
        now += 30_000_000_000L
        assertTrue(s.finish(true))
        assertFalse(s.finish(true))
    }
    @Test fun negativeClockDenied() {
        now = -1L
        val s = state()
        assertFalse(s.begin("navigate"))
    }
    @Test fun freshInstanceCannotResume() {
        val old = state()
        assertTrue(old.begin("read_screen"))
        assertFalse(state().finish(true))
    }
}
