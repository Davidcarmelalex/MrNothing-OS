package tech.mrnothing.os

import android.view.MotionEvent
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Pure touch-flag tests; these do not prove overlay behavior on a real Pixel. */
class OwnerConsentTouchGateTest {
    @Test fun acceptsUnobscuredTouches() {
        assertTrue(OwnerConsentTouchGate.isUnobscured(0))
    }

    @Test fun rejectsFullyObscuredTouches() {
        assertFalse(OwnerConsentTouchGate.isUnobscured(MotionEvent.FLAG_WINDOW_IS_OBSCURED))
    }

    @Test fun rejectsPartiallyObscuredTouches() {
        assertFalse(OwnerConsentTouchGate.isUnobscured(MotionEvent.FLAG_WINDOW_IS_PARTIALLY_OBSCURED))
    }

    @Test fun rejectsCombinedObscuration() {
        assertFalse(OwnerConsentTouchGate.isUnobscured(
            MotionEvent.FLAG_WINDOW_IS_OBSCURED or MotionEvent.FLAG_WINDOW_IS_PARTIALLY_OBSCURED
        ))
    }

    @Test fun ignoresUnrelatedMotionFlags() {
        assertTrue(OwnerConsentTouchGate.isUnobscured(0x100))
    }
}
