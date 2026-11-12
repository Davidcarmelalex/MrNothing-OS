package tech.mrnothing.os

/** One-shot, input-bound owner confirmation; credential success is supplied only by the Activity. */
internal class OwnerAuthorityConfirmationState(
    private val clock: () -> Long
) {
    private data class Pending(val binding: String, val startedAtNanos: Long)
    private var pending: Pending? = null

    fun begin(binding: String): Boolean {
        if (pending != null || binding.isBlank()) return false
        val now = try {
            clock()
        } catch (_: RuntimeException) {
            return false
        }
        if (now < 0L) return false
        pending = Pending(binding, now)
        return true
    }

    /** Always consumes the pending request, including cancellation and mismatched input. */
    fun finish(binding: String, credentialApproved: Boolean): Boolean {
        val active = pending ?: return false
        pending = null
        val now = try {
            clock()
        } catch (_: RuntimeException) {
            return false
        }
        return credentialApproved &&
            binding == active.binding &&
            now >= active.startedAtNanos &&
            now - active.startedAtNanos <= MAX_AGE_NANOS
    }

    fun revoke() {
        pending = null
    }

    companion object {
        const val MAX_AGE_NANOS = 30_000_000_000L
    }
}
