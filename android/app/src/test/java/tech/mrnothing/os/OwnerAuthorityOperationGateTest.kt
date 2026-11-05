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
        assertTrue(gate.begin() != null)
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

    @Test fun cancellationAndCommitClaimHaveExactlyOneWinner() {
        val gate = OwnerAuthorityOperationGate()
        val token = gate.begin() ?: throw AssertionError("operation was not granted")
        val ready = CountDownLatch(2)
        val start = CountDownLatch(1)
        val pool = Executors.newFixedThreadPool(2)
        try {
            val cancel = pool.submit<Boolean> {
                ready.countDown()
                if (!start.await(5, TimeUnit.SECONDS)) {
                    throw AssertionError("cancel worker did not start")
                }
                gate.cancel(token)
            }
            val claim = pool.submit<Boolean> {
                ready.countDown()
                if (!start.await(5, TimeUnit.SECONDS)) {
                    throw AssertionError("commit worker did not start")
                }
                gate.claimCommit(token)
            }
            assertTrue(ready.await(5, TimeUnit.SECONDS))
            start.countDown()
            val canceled = cancel.get(5, TimeUnit.SECONDS)
            val claimed = claim.get(5, TimeUnit.SECONDS)

            // The synchronized gate must linearize the race: exactly one side wins.
            assertTrue("cancel and claim must have one winner", canceled != claimed)
            assertEquals(claimed, gate.isCommitClaimed(token))
            assertFalse(gate.isActive(token))

            val next = gate.begin()
            assertEquals(!claimed, next != null)
            if (next != null) gate.finish(next)
            if (claimed) gate.finish(token)
        } finally {
            start.countDown()
            pool.shutdownNow()
        }
    }

    @Test fun staleCompletionCannotAffectNewOperation() {
        val gate = OwnerAuthorityOperationGate()
        val stale = gate.begin() ?: throw AssertionError("first operation was not granted")
        assertTrue(gate.cancel(stale))

        val current = gate.begin() ?: throw AssertionError("second operation was not granted")
        assertFalse(gate.cancel(stale))
        gate.finish(stale)
        assertTrue(gate.isActive(current))
        assertFalse(gate.claimCommit(stale))
        assertTrue(gate.claimCommit(current))
        gate.finish(current)
    }
}
