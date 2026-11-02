package tech.mrnothing.os

/** Transient credential preview only: never authorizes a command or creates consent. */
class ConsentPreviewState(private val clock: () -> Long) {
    private val actions = setOf("read_screen", "navigate", "scroll")
    private var pending: String? = null
    private var started = 0L
    fun begin(action: String): Boolean {
        if (pending != null || action !in actions) return false
        val now = clock()
        if (now < 0) return false
        pending = action
        started = now
        return true
    }
    /** True is only a preview result, never an authorization capability. */
    fun finish(credentialApproved: Boolean): Boolean {
        val action = pending ?: return false
        val initial = started
        revoke()
        val now = clock()
        return credentialApproved && action in actions && now >= initial &&
            now - initial <= 30_000_000_000L
    }
    fun revoke() {
        pending = null
        started = 0L
    }
}
