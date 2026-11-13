package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * SEC-023B1B2D2: pure-JVM negative gates for a dormant CryptoObject callback.
 * These are NOT AndroidKeyStore, hardware, IPC or owner-credential tests.
 */
class MemoryVaultCryptoCallbackNegativeGateTest {
    private val digest = "a".repeat(64)
    private val credential = 1
    private val blocked = MemoryVaultCryptoCallbackProgress.BLOCKED
    private val pending =
        MemoryVaultCryptoCallbackProgress.AWAITING_AUTHENTICATED_CIPHER_OPERATION

    @Test fun processRecreationCannotRestoreInMemoryPromptAuthority() {
        var now = 42L
        val originalPrompt = Any()
        val originalCipher = Any()
        val oldProcess = MemoryVaultCryptoObjectBindingState { now }
        assertTrue(oldProcess.arm(digest, originalPrompt, originalCipher))

        // A new process must not deserialize/reconstruct pending authorization.
        val newProcess = MemoryVaultCryptoObjectBindingState { now }
        assertEquals(blocked, newProcess.consume(
            digest, originalPrompt, originalCipher, credential, credential))
        oldProcess.revoke()
        assertEquals(blocked, oldProcess.consume(
            digest, originalPrompt, originalCipher, credential, credential))
    }

    @Test fun ownerCancellationBeforeCallbackIsTerminal() {
        val prompt = Any()
        val cipher = Any()
        val gate = MemoryVaultCryptoObjectBindingState { 10L }
        assertTrue(gate.arm(digest, prompt, cipher))
        gate.revoke()
        assertEquals(blocked, gate.consume(digest, prompt, cipher, credential, credential))
        assertFalse(gate.arm(digest, prompt, cipher))
    }

    @Test fun cancellationBeforeArmingPreventsLaterAttempt() {
        val gate = MemoryVaultCryptoObjectBindingState { 10L }
        gate.revoke()
        assertFalse(gate.arm(digest, Any(), Any()))
    }

    @Test fun callbackUsesReferenceIdentityNotForgedValueEquality() {
        class AlwaysEqual {
            override fun equals(other: Any?) = true
            override fun hashCode() = 1
        }
        val prompt = AlwaysEqual()
        val cipher = AlwaysEqual()
        val gate = MemoryVaultCryptoObjectBindingState { 10L }
        assertTrue(gate.arm(digest, prompt, cipher))
        assertEquals(blocked, gate.consume(
            digest, AlwaysEqual(), cipher, credential, credential))
        assertEquals(blocked, gate.consume(
            digest, prompt, cipher, credential, credential))
    }

    @Test fun exactExpiryBoundaryAllowsOnlyPendingCryptoNotAuthorization() {
        var now = 100L
        val prompt = Any()
        val cipher = Any()
        val gate = MemoryVaultCryptoObjectBindingState { now }
        assertTrue(gate.arm(digest, prompt, cipher))
        now += MemoryVaultCryptoObjectBindingState.MAX_AGE_NANOS
        assertEquals(pending, gate.consume(
            digest, prompt, cipher, credential, credential))
        assertEquals(blocked, gate.consume(
            digest, prompt, cipher, credential, credential))
    }

    @Test fun oneNanosecondAfterExpiryFailsClosed() {
        var now = 100L
        val prompt = Any()
        val cipher = Any()
        val gate = MemoryVaultCryptoObjectBindingState { now }
        assertTrue(gate.arm(digest, prompt, cipher))
        now += MemoryVaultCryptoObjectBindingState.MAX_AGE_NANOS + 1L
        assertEquals(blocked, gate.consume(
            digest, prompt, cipher, credential, credential))
        assertFalse(gate.arm(digest, prompt, cipher))
    }

    @Test fun nearLongMaxClockDoesNotWrapIntoFalseFreshness() {
        var now = Long.MAX_VALUE - MemoryVaultCryptoObjectBindingState.MAX_AGE_NANOS - 1L
        val prompt = Any()
        val cipher = Any()
        val gate = MemoryVaultCryptoObjectBindingState { now }
        assertTrue(gate.arm(digest, prompt, cipher))
        now = Long.MAX_VALUE
        assertEquals(blocked, gate.consume(
            digest, prompt, cipher, credential, credential))
    }

    @Test fun wrongCredentialTypeConsumesPendingRequest() {
        val prompt = Any()
        val cipher = Any()
        val gate = MemoryVaultCryptoObjectBindingState { 10L }
        assertTrue(gate.arm(digest, prompt, cipher))
        assertEquals(blocked, gate.consume(digest, prompt, cipher, 2, credential))
        assertEquals(blocked, gate.consume(digest, prompt, cipher, credential, credential))
    }
}
