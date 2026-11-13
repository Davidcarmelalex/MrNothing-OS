package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger

class MemoryVaultConsentCeremonyTest {

    // This verifies formatting and use of the shared local CSPRNG API, not entropy quality.
    @Test fun localFreshNonceIsCanonical256BitHex() {
        val nonce = MemoryVaultConsentNonce.freshHex()
        assertTrue(Regex("^[0-9a-f]{64}$").matches(nonce))
        assertNotEquals("0".repeat(64), nonce)
    }

    @Test fun localFreshNoncesAreDistinctAcrossBoundedSample() {
        val values = (1..32).map { MemoryVaultConsentNonce.freshHex() }
        assertEquals(32, values.toSet().size)
    }

    @Test fun freshNonceChangesConsentBindingWithoutGrantingAuthorization() {
        val first = valid.copy(requestNonceHex = MemoryVaultConsentNonce.freshHex())
        val second = valid.copy(requestNonceHex = MemoryVaultConsentNonce.freshHex())
        assertNotEquals(
            MemoryVaultConsentCeremony.bindingFor(first),
            MemoryVaultConsentCeremony.bindingFor(second)
        )
        val c = ceremony()
        assertNotNull(c.begin(first))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(second, true))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(first, true))
    }


    private var now = 10L
    private fun ceremony() = MemoryVaultConsentCeremony { now }
    private val valid = MemoryVaultConsentSnapshot(
        ownerUserId = 0,
        appSigningSha256 = "a".repeat(64),
        retentionDays = 30,
        requestNonceHex = "b".repeat(64),
        foregroundOwnerUi = true,
        deviceUnlocked = true,
        secureCredentialConfigured = true,
        explicitCheckboxChecked = true,
        strongBoxAdvertised = true,
        aliasAbsent = true
    )

    // Independent Python reference: SHA-256 of six US-ASCII fields, each prefixed
    // with its 4-byte unsigned big-endian length. These vectors freeze the
    // cross-language wire contract before any Android CryptoObject integration.
    @Test fun canonicalBindingGoldenVectorDefaultRetention() {
        assertEquals(
            "a813f8bf88f1a515d7e3b1a0e9964430f96a15de43929e8c63d5ecad2afd8ed4",
            MemoryVaultConsentCeremony.bindingFor(valid)
        )
    }

    @Test fun canonicalBindingGoldenVectorDifferentIdentityAndRetention() {
        val changed = valid.copy(
            appSigningSha256 = "c".repeat(64),
            retentionDays = 90,
            requestNonceHex = "d".repeat(64)
        )
        assertEquals(
            "159612156d4e2fd250882f3840ade57d9ccc0f4949b82840e3312637084547d3",
            MemoryVaultConsentCeremony.bindingFor(changed)
        )
    }

    @Test fun previewIsExplicitlyNotAuthorization() {
        val preview = ceremony().begin(valid)
        assertNotNull(preview)
        assertEquals(30, preview!!.retentionDays)
        assertTrue(preview.disclosure.contains("Nothing is enabled"))
        assertEquals(64, preview.bindingSha256.length)
    }

    @Test fun positiveReportedCredentialStillRequiresCryptographicProof() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.AWAITING_CRYPTOOBJECT_PROOF,
            c.finish(valid, true))
    }

    @Test fun noCheckboxDenied() = assertNull(ceremony().begin(
        valid.copy(explicitCheckboxChecked = false)))
    @Test fun secondaryProfileDenied() = assertNull(ceremony().begin(
        valid.copy(ownerUserId = 10)))
    @Test fun backgroundDenied() = assertNull(ceremony().begin(
        valid.copy(foregroundOwnerUi = false)))
    @Test fun lockedDeviceDenied() = assertNull(ceremony().begin(
        valid.copy(deviceUnlocked = false)))
    @Test fun missingCredentialDenied() = assertNull(ceremony().begin(
        valid.copy(secureCredentialConfigured = false)))
    @Test fun missingStrongBoxDenied() = assertNull(ceremony().begin(
        valid.copy(strongBoxAdvertised = false)))
    @Test fun existingAliasDenied() = assertNull(ceremony().begin(
        valid.copy(aliasAbsent = false)))
    @Test fun invalidRetentionDenied() {
        assertNull(ceremony().begin(valid.copy(retentionDays = 0)))
        assertNull(ceremony().begin(valid.copy(retentionDays = 91)))
    }
    @Test fun invalidSigningDigestDenied() {
        assertNull(ceremony().begin(valid.copy(appSigningSha256 = "A".repeat(64))))
        assertNull(ceremony().begin(valid.copy(appSigningSha256 = "a".repeat(63))))
    }
    @Test fun invalidNonceDenied() {
        assertNull(ceremony().begin(valid.copy(requestNonceHex = "")))
        assertNull(ceremony().begin(valid.copy(requestNonceHex = "B".repeat(64))))
    }

    @Test fun changedRetentionConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED,
            c.finish(valid.copy(retentionDays = 31), true))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
    }

    @Test fun changedSigningIdentityConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED,
            c.finish(valid.copy(appSigningSha256 = "c".repeat(64)), true))
    }

    @Test fun changedNonceConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED,
            c.finish(valid.copy(requestNonceHex = "c".repeat(64)), true))
    }

    @Test fun cancellationConsumesIntentAndCannotRestart() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, false))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
        assertNull(c.begin(valid))
    }

    @Test fun explicitRevocationConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        c.revoke()
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
        assertNull(c.begin(valid))
    }

    @Test fun timeoutAndClockRollbackDenied() {
        val expired = ceremony()
        assertNotNull(expired.begin(valid))
        now += OwnerAuthorityConfirmationState.MAX_AGE_NANOS + 1L
        assertEquals(MemoryVaultConsentProgress.BLOCKED, expired.finish(valid, true))
        now = 10L
        val rollback = ceremony()
        assertNotNull(rollback.begin(valid))
        now = 9L
        assertEquals(MemoryVaultConsentProgress.BLOCKED, rollback.finish(valid, true))
    }

    @Test fun bindingChangesWithEverySensitiveTerm() {
        val a = MemoryVaultConsentCeremony.bindingFor(valid)
        assertNotNull(a)
        assertNotEquals(a, MemoryVaultConsentCeremony.bindingFor(valid.copy(retentionDays = 29)))
        assertNotEquals(a, MemoryVaultConsentCeremony.bindingFor(valid.copy(
            appSigningSha256 = "c".repeat(64))))
        assertNotEquals(a, MemoryVaultConsentCeremony.bindingFor(valid.copy(
            requestNonceHex = "d".repeat(64))))
        assertEquals(a, MemoryVaultConsentCeremony.bindingFor(valid))
    }

    @Test fun concurrentFinishAtMostOnePositive() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        val start = CountDownLatch(1)
        val completed = CountDownLatch(2)
        val positive = AtomicInteger(0)
        repeat(2) {
            Thread {
                try {
                    start.await()
                    if (c.finish(valid, true) ==
                        MemoryVaultConsentProgress.AWAITING_CRYPTOOBJECT_PROOF
                    ) positive.incrementAndGet()
                } finally {
                    completed.countDown()
                }
            }.start()
        }
        start.countDown()
        assertTrue(completed.await(5, java.util.concurrent.TimeUnit.SECONDS))
        assertEquals(1, positive.get())
    }

    @Test fun revokeBeforeBeginCannotBeRestarted() {
        val c = ceremony()
        c.revoke()
        assertNull(c.begin(valid))
    }

    @Test fun invalidFirstAttemptCannotBeReused() {
        val c = ceremony()
        assertNull(c.begin(valid.copy(explicitCheckboxChecked = false)))
        assertNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
    }

    // QA-023B1B2A: all transient trust assertions are rechecked on completion.
    @Test fun foregroundLossAfterPreviewConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED,
            c.finish(valid.copy(foregroundOwnerUi = false), true))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
    }

    @Test fun deviceLockAfterPreviewConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED,
            c.finish(valid.copy(deviceUnlocked = false), true))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
    }

    @Test fun consentWithdrawalAfterPreviewConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED,
            c.finish(valid.copy(explicitCheckboxChecked = false), true))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
    }

    @Test fun credentialRemovalAfterPreviewConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED,
            c.finish(valid.copy(secureCredentialConfigured = false), true))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
    }

    @Test fun strongBoxLossAfterPreviewConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED,
            c.finish(valid.copy(strongBoxAdvertised = false), true))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
    }

    @Test fun keyAliasAppearsAfterPreviewConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED,
            c.finish(valid.copy(aliasAbsent = false), true))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
    }

    @Test fun ownerProfileChangesAfterPreviewConsumesIntent() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED,
            c.finish(valid.copy(ownerUserId = 10), true))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
    }

    @Test fun clockFailureDuringFinishConsumesIntent() {
        var throwClock = false
        val c = MemoryVaultConsentCeremony {
            if (throwClock) throw IllegalStateException("synthetic clock failure")
            10L
        }
        assertNotNull(c.begin(valid))
        throwClock = true
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
        throwClock = false
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
    }

    @Test fun invalidMonotonicStartCannotAuthorizeLater() {
        val c = MemoryVaultConsentCeremony { -1L }
        assertNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
        assertNull(c.begin(valid))
    }

    @Test fun successfulPreviewCompletionIsNotReplayable() {
        val c = ceremony()
        assertNotNull(c.begin(valid))
        assertEquals(MemoryVaultConsentProgress.AWAITING_CRYPTOOBJECT_PROOF,
            c.finish(valid, true))
        assertEquals(MemoryVaultConsentProgress.BLOCKED, c.finish(valid, true))
        assertNull(c.begin(valid))
    }
}
