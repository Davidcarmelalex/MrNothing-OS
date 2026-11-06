package tech.mrnothing.os

/** One-shot, monotonic, 30-second local credential enrollment intent. */
internal class OwnerEnrollmentState(private val clock: () -> Long) {
    private var started: Long? = null

    fun begin(): Boolean {
        if (started != null) return false
        val now = clock()
        if (now < 0L) return false
        started = now
        return true
    }

    fun finish(credentialApproved: Boolean): Boolean {
        val initial = started ?: return false
        started = null
        val now = clock()
        return credentialApproved && now >= initial && now - initial <= 30_000_000_000L
    }

    fun revoke() {
        started = null
    }
}
