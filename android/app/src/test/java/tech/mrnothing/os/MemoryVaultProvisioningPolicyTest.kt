package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

class MemoryVaultProvisioningPolicyTest {
    private val ready = MemoryVaultProvisioningSignals(
        apiLevel = 35,
        primaryOwnerProfile = true,
        trustedAppCaller = true,
        foregroundOwnerUi = true,
        deviceUnlocked = true,
        secureDeviceCredentialConfigured = true,
        explicitMemoryOptIn = true,
        strongBoxAdvertised = true,
        aliasAbsent = true
    )

    private fun blocked(s: MemoryVaultProvisioningSignals) {
        assertEquals(MemoryVaultProvisioningReadiness.BLOCKED,
            MemoryVaultProvisioningPolicy.evaluate(s))
    }

    @Test fun completePreflightStillRequiresOwnerCeremony() {
        assertEquals(MemoryVaultProvisioningReadiness.REQUIRES_OWNER_CEREMONY,
            MemoryVaultProvisioningPolicy.evaluate(ready))
    }

    @Test fun api30Denied() = blocked(ready.copy(apiLevel = 30))
    @Test fun api29Denied() = blocked(ready.copy(apiLevel = 29))
    @Test fun secondaryProfileDenied() = blocked(ready.copy(primaryOwnerProfile = false))
    @Test fun untrustedCallerDenied() = blocked(ready.copy(trustedAppCaller = false))
    @Test fun backgroundUiDenied() = blocked(ready.copy(foregroundOwnerUi = false))
    @Test fun lockedDeviceDenied() = blocked(ready.copy(deviceUnlocked = false))
    @Test fun noCredentialDenied() =
        blocked(ready.copy(secureDeviceCredentialConfigured = false))
    @Test fun noConsentDenied() = blocked(ready.copy(explicitMemoryOptIn = false))
    @Test fun noStrongBoxDenied() = blocked(ready.copy(strongBoxAdvertised = false))
    @Test fun existingAliasDenied() = blocked(ready.copy(aliasAbsent = false))
    @Test fun multipleMissingSignalsDenied() = blocked(ready.copy(
        foregroundOwnerUi = false,
        explicitMemoryOptIn = false,
        aliasAbsent = false
    ))
}
