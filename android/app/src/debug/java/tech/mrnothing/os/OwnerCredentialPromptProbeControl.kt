package tech.mrnothing.os

import android.os.CancellationSignal

/** Debug-only single-prompt cancellation control for QA-020B3. */
internal object OwnerCredentialPromptProbeControl {
    private val lock = Any()
    private var activeSignal: CancellationSignal? = null

    fun attach(signal: CancellationSignal): Boolean = synchronized(lock) {
        if (activeSignal != null) false else {
            activeSignal = signal
            true
        }
    }

    fun detach(signal: CancellationSignal) {
        synchronized(lock) {
            if (activeSignal === signal) activeSignal = null
        }
    }

    fun cancelActive(): Boolean = synchronized(lock) {
        val signal = activeSignal ?: return@synchronized false
        signal.cancel()
        true
    }
}
