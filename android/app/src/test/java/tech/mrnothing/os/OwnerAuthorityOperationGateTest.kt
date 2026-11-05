package tech.mrnothing.os

import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class OwnerAuthorityOperationGateTest {
    @Test fun onlyOneOperationCanBeActive() {
        val gate = OwnerAuthorityOperationGate()
        val token = gate.begin() ?: throw AssertionError("operation was not granted")
        assertNull(gate.begin())
        assertTrue(gate.isActive(token))
        gate.finish(token)
        assertTrue(gate.begin() != null)
    }

    @Test fun cancellationBeforeCommitPreventsCommitClaim() {
        val gate = OwnerAuthorityOperationGate()
        val token = gate.begin() ?: throw AssertionError("operation was not granted")
        assertTrue(gate.cancel(token))
        assertFalse(gate.isActive(token))
        assertFalse(gate.claimCommit(token))
        assertFalse(gate.isDeliverable(token))
    }

    @Test fun destructionBeforeCommitPreventsCommitClaim() {
        val gate = OwnerAuthorityOperationGate()
        val token = gate.begin() ?: throw AssertionError("operation was not granted")
        gate.destroy()
        assertFalse(gate.isActive(token))
        assertFalse(gate.claimCommit(token))
        assertFalse(gate.isDeliverable(token))
        assertNull(gate.begin())
    }

    @Test fun claimedCommitCannotBeCanceled() {
        val gate = OwnerAuthorityOperationGate()
        val token = gate.begin() ?: throw AssertionError("operation was not granted")
        assertTrue(gate.claimCommit(token))
        assertTrue(gate.isCommitClaimed(token))
        assertFalse(gate.cancel(token))
        assertTrue(gate.isDeliverable(token))
        gate.finish(token)
        assertFalse(gate.isCommitClaimed(token))
        assertNull(gate.begin())
    }

    @Test fun destructionSuppressesCallbackButDoesNotPretendToRollbackClaimedCommit() {
        val gate = OwnerAuthorityOperationGate()
        val token = gate.begin() ?: throw AssertionError("operation was not granted")
        assertTrue(gate.claimCommit(token))
        gate.destroy()
        assertTrue(gate.isCommitClaimed(token))
        assertFalse(gate.isDeliverable(token))
        gate.finish(token)
        assertFalse(gate.isCommitClaimed(token))
    }

    @Test fun concurrentBeginGrantsExactlyOneToken() {
        val gate = OwnerAuthorityOperationGate()
        val workers = 16
        val ready = CountDownLatch(workers)
        val start = CountDownLatch(1)
        val pool = Executors.newFixedThreadPool(workers)
        try {
            val futures = (0 until workers).map {
                pool.submit<Long?> {
                    ready.countDown()
                    start.await()
                    gate.begin()
                }
            }
            assertTrue(ready.await(5, TimeUnit.SECONDS))
            start.countDown()
            val granted = futures.map { it.get(5, TimeUnit.SECONDS) }.filterNotNull()
            assertEquals(1, granted.size)
        } finally {
            pool.shutdownNow()
        }
    }
}
