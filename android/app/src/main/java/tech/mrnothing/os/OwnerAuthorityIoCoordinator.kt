package tech.mrnothing.os

import java.util.concurrent.Executors

/**
 * Process-wide single-thread executor for Android Keystore and AtomicFile operations.
 * Tasks capture immutable inputs and post UI updates back to the main thread.
 */
internal object OwnerAuthorityIoCoordinator {
    private val executor = Executors.newSingleThreadExecutor { task ->
        Thread(task, "mrnothing-owner-authority-io").apply { isDaemon = true }
    }

    fun execute(task: () -> Unit) {
        executor.execute(task)
    }
}

/**
 * Lifecycle gate for a trust-store operation.
 *
 * Cancellation/destruction invalidates queued work until claimCommit(). Claiming
 * is the transaction boundary after fresh credential and safety revalidation:
 * once claimed, the atomic store operation is allowed to finish, but UI delivery
 * is suppressed if the Activity is destroyed.
 */
internal class OwnerAuthorityOperationGate {
    private val lock = Any()
    private var sequence = 0L
    private var activeToken: Long? = null
    private var committingToken: Long? = null
    private var destroyed = false

    fun begin(): Long? = synchronized(lock) {
        if (destroyed || activeToken != null || committingToken != null ||
            sequence == Long.MAX_VALUE
        ) {
            null
        } else {
            sequence += 1L
            activeToken = sequence
            sequence
        }
    }

    fun isActive(token: Long): Boolean = synchronized(lock) {
        !destroyed && activeToken == token
    }

    fun claimCommit(token: Long): Boolean = synchronized(lock) {
        if (destroyed || activeToken != token) {
            false
        } else {
            activeToken = null
            committingToken = token
            true
        }
    }

    fun isCommitClaimed(token: Long): Boolean = synchronized(lock) {
        committingToken == token
    }

    fun isDeliverable(token: Long): Boolean = synchronized(lock) {
        !destroyed && (activeToken == token || committingToken == token)
    }

    fun cancel(token: Long): Boolean = synchronized(lock) {
        if (activeToken != token) {
            false
        } else {
            activeToken = null
            true
        }
    }

    fun finish(token: Long) {
        synchronized(lock) {
            if (activeToken == token) activeToken = null
            if (committingToken == token) committingToken = null
        }
    }

    fun destroy() {
        synchronized(lock) {
            destroyed = true
            activeToken = null
        }
    }
}
