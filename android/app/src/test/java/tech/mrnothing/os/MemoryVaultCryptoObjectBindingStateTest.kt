package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger

class MemoryVaultCryptoObjectBindingStateTest {
    private var now = 10L
    private val digest = "a".repeat(64)
    private val prompt = Any()
    private val cipher = Any()
    private fun gate() = MemoryVaultCryptoObjectBindingState { now }
    private val credential = 1

    private fun accepted() =
        MemoryVaultCryptoCallbackProgress.AWAITING_AUTHENTICATED_CIPHER_OPERATION
    private fun blocked() = MemoryVaultCryptoCallbackProgress.BLOCKED

    @Test fun successIsOnlyPendingCipherOperationNotAuthorization() {
        val g = gate()
        assertTrue(g.arm(digest, prompt, cipher))
        assertEquals(accepted(), g.consume(digest, prompt, cipher, credential, credential))
        assertEquals(blocked(), g.consume(digest, prompt, cipher, credential, credential))
    }

    @Test fun unarmedAndNullCallbackBlocked() {
        assertEquals(blocked(), gate().consume(digest, prompt, cipher, credential, credential))
        val g = gate()
        assertTrue(g.arm(digest, prompt, cipher))
        assertEquals(blocked(), g.consume(digest, null, null, credential, credential))
    }

    @Test fun wrongPromptIdentityConsumesRequest() {
        val g = gate()
        assertTrue(g.arm(digest, prompt, cipher))
        assertEquals(blocked(), g.consume(digest, Any(), cipher, credential, credential))
        assertEquals(blocked(), g.consume(digest, prompt, cipher, credential, credential))
    }

    @Test fun wrongCipherIdentityConsumesRequest() {
        val g = gate()
        assertTrue(g.arm(digest, prompt, cipher))
        assertEquals(blocked(), g.consume(digest, prompt, Any(), credential, credential))
    }

    @Test fun wrongCredentialTypeConsumesRequest() {
        val g = gate()
        assertTrue(g.arm(digest, prompt, cipher))
        assertEquals(blocked(), g.consume(digest, prompt, cipher, 2, credential))
    }

    @Test fun mismatchedDigestConsumesRequest() {
        val g = gate()
        assertTrue(g.arm(digest, prompt, cipher))
        assertEquals(blocked(), g.consume("b".repeat(64), prompt, cipher, credential, credential))
    }

    @Test fun expiredAndRollbackClocksAreDenied() {
        val expired = gate()
        assertTrue(expired.arm(digest, prompt, cipher))
        now += MemoryVaultCryptoObjectBindingState.MAX_AGE_NANOS + 1L
        assertEquals(blocked(), expired.consume(digest, prompt, cipher, credential, credential))
        now = 10L
        val rollback = gate()
        assertTrue(rollback.arm(digest, prompt, cipher))
        now = 9L
        assertEquals(blocked(), rollback.consume(digest, prompt, cipher, credential, credential))
    }

    @Test fun clockExceptionFailsClosed() {
        val g = MemoryVaultCryptoObjectBindingState { throw IllegalStateException("clock") }
        assertFalse(g.arm(digest, prompt, cipher))
        assertFalse(g.arm(digest, prompt, cipher))
        val after = MemoryVaultCryptoObjectBindingState { if (now == 10L) 10L else throw IllegalStateException("clock") }
        assertTrue(after.arm(digest, prompt, cipher))
        now = 11L
        assertEquals(blocked(), after.consume(digest, prompt, cipher, credential, credential))
    }

    @Test fun malformedDigestAndNullObjectsAreRejectedWithoutRearm() {
        for (invalid in listOf("", "A".repeat(64), "a".repeat(63))) {
            val g = gate()
            assertFalse(g.arm(invalid, prompt, cipher))
            assertFalse(g.arm(digest, prompt, cipher))
        }
        assertFalse(gate().arm(digest, null, cipher))
        assertFalse(gate().arm(digest, prompt, null))
    }

    @Test fun revokeAndDoubleArmDenied() {
        val g = gate()
        assertTrue(g.arm(digest, prompt, cipher))
        assertFalse(g.arm(digest, prompt, cipher))
        g.revoke()
        assertEquals(blocked(), g.consume(digest, prompt, cipher, credential, credential))
        assertFalse(g.arm(digest, prompt, cipher))
    }

    @Test fun revokeBeforeArmIsTerminal() {
        val g = gate()
        g.revoke()
        assertFalse(g.arm(digest, prompt, cipher))
    }

    @Test fun negativeTimeDenied() {
        now = -1L
        assertFalse(gate().arm(digest, prompt, cipher))
    }

    @Test fun concurrentCallbackAtMostOneCanAdvance() {
        val g = gate()
        assertTrue(g.arm(digest, prompt, cipher))
        val ready = CountDownLatch(2)
        val start = CountDownLatch(1)
        val acceptedCount = AtomicInteger(0)
        val threads = (1..2).map {
            Thread {
                ready.countDown()
                start.await()
                if (g.consume(digest, prompt, cipher, credential, credential) == accepted()) {
                    acceptedCount.incrementAndGet()
                }
            }.also { it.start() }
        }
        ready.await()
        start.countDown()
        threads.forEach { it.join() }
        assertEquals(1, acceptedCount.get())
    }
}
