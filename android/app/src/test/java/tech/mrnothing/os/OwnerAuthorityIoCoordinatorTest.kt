package tech.mrnothing.os

import java.util.Collections
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class OwnerAuthorityIoCoordinatorTest {
    @Test fun tasksRunOnDedicatedSingleThreadWithoutOverlap() {
        val firstStarted = CountDownLatch(1)
        val releaseFirst = CountDownLatch(1)
        val secondFinished = CountDownLatch(1)
        val workerNames = Collections.synchronizedList(mutableListOf<String>())
        val active = AtomicInteger(0)
        val maxActive = AtomicInteger(0)

        try {
            OwnerAuthorityIoCoordinator.execute {
                workerNames.add(Thread.currentThread().name)
                val running = active.incrementAndGet()
                maxActive.updateAndGet { previous -> maxOf(previous, running) }
                firstStarted.countDown()
                try {
                    releaseFirst.await(5, TimeUnit.SECONDS)
                } finally {
                    active.decrementAndGet()
                }
            }
            assertTrue("first worker did not start", firstStarted.await(5, TimeUnit.SECONDS))

            OwnerAuthorityIoCoordinator.execute {
                workerNames.add(Thread.currentThread().name)
                val running = active.incrementAndGet()
                maxActive.updateAndGet { previous -> maxOf(previous, running) }
                try {
                    // Completion is signaled only after the first task has released the worker.
                } finally {
                    active.decrementAndGet()
                    secondFinished.countDown()
                }
            }
            assertFalse(
                "second task ran while the first task held the single worker",
                secondFinished.await(100, TimeUnit.MILLISECONDS)
            )
        } finally {
            releaseFirst.countDown()
        }

        assertTrue("second task did not run after release", secondFinished.await(5, TimeUnit.SECONDS))
        assertEquals(0, active.get())
        assertEquals(1, maxActive.get())
        assertEquals(2, workerNames.size)
        assertTrue(workerNames.all { it == "mrnothing-owner-authority-io" })
        assertFalse(workerNames.any { it == Thread.currentThread().name })
    }
}
