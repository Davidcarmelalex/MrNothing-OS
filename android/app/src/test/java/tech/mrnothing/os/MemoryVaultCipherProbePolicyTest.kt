package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

/** Pure JVM only: not actual owner credential or hardware testing. */
class MemoryVaultCipherProbePolicyTest {
    private val callback = MemoryVaultCryptoCallbackProgress.AWAITING_AUTHENTICATED_CIPHER_OPERATION
    private val key = MemoryVaultKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH
    private val blocked = MemoryVaultCipherProbeOutcome.BLOCKED

    @Test fun positiveResultStillDoesNotAuthorizePersistence() {
        assertEquals(MemoryVaultCipherProbeOutcome.CRYPTO_OPERATION_EXECUTED_NOT_AUTHORIZED,
            MemoryVaultCipherProbePolicy.evaluate(callback, key, 16))
    }
    @Test fun callbackMismatchBlocks() {
        assertEquals(blocked, MemoryVaultCipherProbePolicy.evaluate(
            MemoryVaultCryptoCallbackProgress.BLOCKED, key, 16))
    }
    @Test fun missingKeyBlocks() {
        assertEquals(blocked, MemoryVaultCipherProbePolicy.evaluate(
            callback, MemoryVaultKeyReadiness.BLOCKED, 16))
    }
    @Test fun shortTagBlocks() {
        assertEquals(blocked, MemoryVaultCipherProbePolicy.evaluate(callback, key, 12))
    }
    @Test fun longTagBlocks() {
        assertEquals(blocked, MemoryVaultCipherProbePolicy.evaluate(callback, key, 32))
    }
    @Test fun emptyTagBlocks() {
        assertEquals(blocked, MemoryVaultCipherProbePolicy.evaluate(callback, key, 0))
    }
    @Test fun negativeTagLengthBlocks() {
        assertEquals(blocked, MemoryVaultCipherProbePolicy.evaluate(callback, key, -1))
    }
}
