package tech.mrnothing.os

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Pure state tests; these do NOT prove emulator lock-state transitions. */
class OwnerCredentialSafetyGateTest {
    private fun valid() = CredentialSafetySignals(
        secureLockConfigured = true,
        deviceLocked = false,
        keyguardLocked = false,
        userUnlocked = true,
        screenInteractive = true
    )

    @Test fun acceptsOnlySafeLocalDeviceState() {
        assertTrue(OwnerCredentialSafetyGate.eligible(valid()))
    }

    @Test fun deniesWithoutSecureDeviceCredential() {
        assertFalse(OwnerCredentialSafetyGate.eligible(valid().copy(secureLockConfigured = false)))
    }

    @Test fun deniesLockedDevice() {
        assertFalse(OwnerCredentialSafetyGate.eligible(valid().copy(deviceLocked = true)))
    }

    @Test fun deniesVisibleKeyguard() {
        assertFalse(OwnerCredentialSafetyGate.eligible(valid().copy(keyguardLocked = true)))
    }

    @Test fun deniesLockedAndroidUser() {
        assertFalse(OwnerCredentialSafetyGate.eligible(valid().copy(userUnlocked = false)))
    }

    @Test fun deniesNoninteractiveDisplay() {
        assertFalse(OwnerCredentialSafetyGate.eligible(valid().copy(screenInteractive = false)))
    }

    @Test fun deniesEverySingleUnsafeSignalIndependently() {
        val unsafe = listOf(
            valid().copy(secureLockConfigured = false),
            valid().copy(deviceLocked = true),
            valid().copy(keyguardLocked = true),
            valid().copy(userUnlocked = false),
            valid().copy(screenInteractive = false)
        )
        unsafe.forEach { assertFalse(OwnerCredentialSafetyGate.eligible(it)) }
    }
}
