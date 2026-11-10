package tech.mrnothing.os

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Pure JVM tests; not AndroidKeyStore, hardware, or owner authentication. */
class MemoryVaultCompletionCancellationFenceTest {
    @Test fun cannotFinishWithoutBeginning() {
        assertFalse(MemoryVaultCompletionCancellationFence().finish())
    }

    @Test fun exactlyOneBeginAndFinish() {
        val gate = MemoryVaultCompletionCancellationFence()
        assertTrue(gate.begin())
        assertFalse(gate.begin())
        assertTrue(gate.finish())
        assertFalse(gate.finish())
        assertFalse(gate.begin())
    }

    @Test fun cancellationBeforeBeginIsTerminal() {
        val gate = MemoryVaultCompletionCancellationFence()
        gate.revoke()
        assertFalse(gate.begin())
        assertFalse(gate.finish())
    }

    @Test fun cancellationDuringCryptoWorkBlocksCompletion() {
        val gate = MemoryVaultCompletionCancellationFence()
        assertTrue(gate.begin())
        gate.revoke()
        assertFalse(gate.finish())
        assertFalse(gate.begin())
    }

    @Test fun repeatedCancellationCannotRearm() {
        val gate = MemoryVaultCompletionCancellationFence()
        assertTrue(gate.begin())
        gate.revoke()
        gate.revoke()
        assertFalse(gate.finish())
        assertFalse(gate.begin())
    }

    @Test fun aNewProcessCannotInheritPriorInFlightWork() {
        val prior = MemoryVaultCompletionCancellationFence()
        assertTrue(prior.begin())
        val recreated = MemoryVaultCompletionCancellationFence()
        assertFalse(recreated.finish())
        prior.revoke()
        assertFalse(prior.finish())
    }

    @Test fun cancellationCanWinWhileCryptoWorkerIsBlocked() {
        val gate = MemoryVaultCompletionCancellationFence()
        val workerEntered = CountDownLatch(1)
        val workerResume = CountDownLatch(1)
        val outcome = AtomicBoolean(true)
        val worker = Thread {
            if (!gate.begin()) { outcome.set(false); workerEntered.countDown(); return@Thread }
            workerEntered.countDown()
            if (!workerResume.await(5, TimeUnit.SECONDS)) { outcome.set(false); return@Thread }
            outcome.set(gate.finish())
        }
        worker.start()
        try {
            assertTrue("worker failed to begin", workerEntered.await(5, TimeUnit.SECONDS))
            gate.revoke()
        } finally {
            workerResume.countDown()
            worker.join(5000)
        }
        assertFalse("worker must terminate", worker.isAlive)
        assertFalse("revocation must win before finish", outcome.get())
    }

    @Test fun finishFirstCannotBeRetroactivelyReclassified() {
        val gate = MemoryVaultCompletionCancellationFence()
        assertTrue(gate.begin())
        assertTrue(gate.finish())
        gate.revoke()
        assertFalse(gate.finish())
    }
}
