package tech.mrnothing.os

import android.view.MotionEvent

/** SEC-014E: fail closed on fully or partially obscured touch events. */
internal object OwnerConsentTouchGate {
    fun isUnobscured(flags: Int): Boolean =
        (flags and (MotionEvent.FLAG_WINDOW_IS_OBSCURED or
            MotionEvent.FLAG_WINDOW_IS_PARTIALLY_OBSCURED)) == 0
}
