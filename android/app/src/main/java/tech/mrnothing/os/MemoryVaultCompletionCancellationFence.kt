package tech.mrnothing.os

/**
 * SEC-023B1B2D3: one-shot cancellation fence for a dormant cryptographic probe.
 *
 * begin() precedes any potentially blocking cryptographic work. A revoke that
 * linearizes before finish() makes the result BLOCKED. A successful finish()
 * is only permission to report a synthetic probe result, never to persist
 * data or authorize an agent. The fence cannot survive process recreation.
 */
internal class MemoryVaultCompletionCancellationFence {
    private enum class State { NEW, RUNNING, FINISHED, REVOKED }
    private var state = State.NEW

    @Synchronized
    fun begin(): Boolean {
        if (state != State.NEW) return false
        state = State.RUNNING
        return true
    }

    @Synchronized
    fun finish(): Boolean {
        if (state != State.RUNNING) return false
        state = State.FINISHED
        return true
    }

    @Synchronized
    fun revoke() {
        state = State.REVOKED
    }
}
