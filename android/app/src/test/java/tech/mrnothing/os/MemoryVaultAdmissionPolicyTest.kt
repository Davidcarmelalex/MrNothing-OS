package tech.mrnothing.os

import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/** Synthetic JVM-only tests; no Android Keystore, Binder, or Pixel hardware. */
class MemoryVaultAdmissionPolicyTest {
    private val digest = "ab".repeat(32)
    private fun trusted(authenticated: Boolean = true) = MemoryVaultTrustedSnapshot(
        callingUid = 10042,
        applicationUid = 10042,
        callingUserId = 0,
        ownerUserId = 0,
        callingSigningSha256 = digest,
        applicationSigningSha256 = digest,
        foregroundOwnerUi = true,
        deviceUnlocked = true,
        explicitMemoryConsent = true,
        authenticatedKeyUse = authenticated
    )

    @Test fun exactTrustedPreflightAndKeyUse() {
        assertTrue(MemoryVaultAdmissionPolicy.canRequestAuthentication(trusted(false)))
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(trusted(false)))
        assertTrue(MemoryVaultAdmissionPolicy.canUseKey(trusted()))
    }

    @Test fun rejectsUidAndUserProfileMismatch() {
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(trusted().copy(callingUid = 10043)))
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(trusted().copy(callingUid = 0)))
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(trusted().copy(callingUserId = 10)))
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(trusted().copy(ownerUserId = -1)))
    }

    @Test fun rejectsSigningIdentityChangesAndMalformedDigests() {
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(
            trusted().copy(callingSigningSha256 = "cd".repeat(32))))
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(
            trusted().copy(applicationSigningSha256 = "AB".repeat(32))))
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(
            trusted().copy(callingSigningSha256 = "")))
    }

    @Test fun rejectsMissingOwnerForegroundUnlockAndConsent() {
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(
            trusted().copy(foregroundOwnerUi = false)))
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(
            trusted().copy(deviceUnlocked = false)))
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(
            trusted().copy(explicitMemoryConsent = false)))
    }

    @Test fun oneTimeClaimRejectsReplay() {
        var clock = 1000L
        val registry = MemoryVaultOwnerIntentRegistry { clock }
        val token = registry.begin(MemoryVaultOperation.READ, trusted(false))
        assertNotNull(token)
        assertTrue(registry.claim(token!!, MemoryVaultOperation.READ, trusted()))
        assertFalse(registry.claim(token, MemoryVaultOperation.READ, trusted()))
        clock += 1
    }

    @Test fun expiredIntentFailsAtExactBoundary() {
        var clock = 1000L
        val registry = MemoryVaultOwnerIntentRegistry { clock }
        val token = registry.begin(MemoryVaultOperation.EXPORT, trusted(false))!!
        clock += 30_000L
        assertFalse(registry.claim(token, MemoryVaultOperation.EXPORT, trusted()))
    }

    @Test fun wrongOperationOrCallerBurnsExactIntent() {
        val registry = MemoryVaultOwnerIntentRegistry { 1000L }
        val token = registry.begin(MemoryVaultOperation.DELETE, trusted(false))!!
        assertFalse(registry.claim(token, MemoryVaultOperation.WRITE, trusted()))
        assertFalse(registry.claim(token, MemoryVaultOperation.DELETE, trusted()))
        val next = registry.begin(MemoryVaultOperation.DELETE, trusted(false))!!
        assertFalse(registry.claim(next, MemoryVaultOperation.DELETE,
            trusted().copy(callingUid = 10043)))
        assertFalse(registry.claim(next, MemoryVaultOperation.DELETE, trusted()))
    }

    @Test fun absentCryptoAuthenticationBurnsIntent() {
        val registry = MemoryVaultOwnerIntentRegistry { 1000L }
        val token = registry.begin(MemoryVaultOperation.READ, trusted(false))!!
        assertFalse(registry.claim(token, MemoryVaultOperation.READ, trusted(false)))
        assertFalse(registry.claim(token, MemoryVaultOperation.READ, trusted()))
    }

    @Test fun cancellationReplacementAndCloseFailClosed() {
        val registry = MemoryVaultOwnerIntentRegistry { 1000L }
        val first = registry.begin(MemoryVaultOperation.READ, trusted(false))!!
        val second = registry.begin(MemoryVaultOperation.WRITE, trusted(false))!!
        assertFalse(registry.claim(first, MemoryVaultOperation.READ, trusted()))
        registry.cancel()
        assertFalse(registry.claim(second, MemoryVaultOperation.WRITE, trusted()))
        registry.close()
        assertNull(registry.begin(MemoryVaultOperation.READ, trusted(false)))
    }

    @Test fun clockRollbackInvalidatesIntent() {
        var clock = 2000L
        val registry = MemoryVaultOwnerIntentRegistry { clock }
        val token = registry.begin(MemoryVaultOperation.READ, trusted(false))!!
        clock = 1999L
        assertFalse(registry.claim(token, MemoryVaultOperation.READ, trusted()))
        clock = 2001L
        assertFalse(registry.claim(token, MemoryVaultOperation.READ, trusted()))
    }

    @Test fun clockFailureInvalidatesIntent() {
        var fail = false
        val registry = MemoryVaultOwnerIntentRegistry {
            if (fail) throw IllegalStateException("clock unavailable")
            1000L
        }
        val token = registry.begin(MemoryVaultOperation.READ, trusted(false))!!
        fail = true
        assertFalse(registry.claim(token, MemoryVaultOperation.READ, trusted()))
    }

    @Test fun beginDeniesWithoutForegroundConsent() {
        val registry = MemoryVaultOwnerIntentRegistry { 1000L }
        assertNull(registry.begin(MemoryVaultOperation.READ,
            trusted(false).copy(foregroundOwnerUi = false)))
        assertNull(registry.begin(MemoryVaultOperation.READ,
            trusted(false).copy(explicitMemoryConsent = false)))
    }

    @Test fun deniesSecondaryProfileEvenIfCallerMatchesIt() {
        assertFalse(MemoryVaultAdmissionPolicy.canUseKey(
            trusted().copy(callingUserId = 10, ownerUserId = 10)))
    }

    @Test fun claimCannotSwitchOwnerOrSigningIdentityAfterBegin() {
        val registry = MemoryVaultOwnerIntentRegistry { 1000L }
        val token = registry.begin(MemoryVaultOperation.READ, trusted(false))!!
        assertFalse(registry.claim(token, MemoryVaultOperation.READ,
            trusted().copy(callingUserId = 10, ownerUserId = 10)))
        assertFalse(registry.claim(token, MemoryVaultOperation.READ, trusted()))
    }

    @Test fun invalidBeginRevokesPreviouslyIssuedIntent() {
        val registry = MemoryVaultOwnerIntentRegistry { 1000L }
        val token = registry.begin(MemoryVaultOperation.READ, trusted(false))!!
        assertNull(registry.begin(MemoryVaultOperation.READ,
            trusted(false).copy(explicitMemoryConsent = false)))
        assertFalse(registry.claim(token, MemoryVaultOperation.READ, trusted()))
    }

    @Test fun concurrentClaimsAllowExactlyOneWinner() {
        val registry = MemoryVaultOwnerIntentRegistry { 1000L }
        val token = registry.begin(MemoryVaultOperation.READ, trusted(false))!!
        val start = CountDownLatch(1)
        val pool = Executors.newFixedThreadPool(8)
        val winners = AtomicInteger(0)
        try {
            val futures = (1..16).map {
                pool.submit {
                    start.await()
                    if (registry.claim(token, MemoryVaultOperation.READ, trusted())) {
                        winners.incrementAndGet()
                    }
                }
            }
            start.countDown()
            futures.forEach { it.get(10, TimeUnit.SECONDS) }
            assertTrue(winners.get() == 1)
        } finally {
            pool.shutdownNow()
        }
    }
}
