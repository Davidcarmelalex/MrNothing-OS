package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

class MemoryVaultKeyPolicyTest {
    private val valid = MemoryVaultKeySignals(
        keyPresent = true,
        aesAlgorithm = true,
        keySizeBits = 256,
        gcmOnly = true,
        noPaddingOnly = true,
        encryptDecryptOnly = true,
        generatedInKeystore = true,
        strongBoxBacked = true,
        credentialOnlyAuth = true,
        authenticationRequired = true,
        perUseAuthentication = true,
        unlockedDeviceRequired = true,
        randomizedEncryptionRequired = true
    )
    private fun blocked(s: MemoryVaultKeySignals) {
        assertEquals(MemoryVaultKeyReadiness.BLOCKED, MemoryVaultKeyPolicy.evaluate(35, s))
    }

    @Test fun validMetadataStillRequiresSeparateOwnerAuthentication() {
        assertEquals(
            MemoryVaultKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH,
            MemoryVaultKeyPolicy.evaluate(35, valid)
        )
    }

    @Test fun olderPlatformFailsClosed() {
        for (api in listOf(0, 29, 30)) {
            assertEquals(MemoryVaultKeyReadiness.BLOCKED, MemoryVaultKeyPolicy.evaluate(api, valid))
        }
        assertEquals(
            MemoryVaultKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH,
            MemoryVaultKeyPolicy.evaluate(31, valid)
        )
    }

    @Test fun missingOrNonAesKeyRejected() {
        blocked(valid.copy(keyPresent = false))
        blocked(valid.copy(aesAlgorithm = false))
    }

    @Test fun non256BitKeysRejected() {
        for (bits in listOf(0, 128, 192, 257, 512)) blocked(valid.copy(keySizeBits = bits))
    }

    @Test fun nonGcmOrAdditionalModesRejected() { blocked(valid.copy(gcmOnly = false)) }
    @Test fun nonCanonicalPaddingRejected() { blocked(valid.copy(noPaddingOnly = false)) }
    @Test fun extraOrMissingKeyPurposesRejected() { blocked(valid.copy(encryptDecryptOnly = false)) }
    @Test fun importedKeyRejected() { blocked(valid.copy(generatedInKeystore = false)) }
    @Test fun teeOrSoftwareKeyRejected() { blocked(valid.copy(strongBoxBacked = false)) }
    @Test fun biometricOrTimedCredentialAuthRejected() {
        blocked(valid.copy(credentialOnlyAuth = false))
        blocked(valid.copy(perUseAuthentication = false))
    }
    @Test fun noAuthenticationRequirementRejected() {
        blocked(valid.copy(authenticationRequired = false))
    }
    @Test fun unlockedDeviceRequirementCannotBeRelaxed() {
        blocked(valid.copy(unlockedDeviceRequired = false))
    }
    @Test fun callerControlledIvCapabilityRejected() {
        blocked(valid.copy(randomizedEncryptionRequired = false))
    }
    @Test fun everyRequiredSignalIndependentlyFailsClosed() {
        val mutations = listOf(
            valid.copy(keyPresent = false),
            valid.copy(aesAlgorithm = false),
            valid.copy(keySizeBits = 128),
            valid.copy(gcmOnly = false),
            valid.copy(noPaddingOnly = false),
            valid.copy(encryptDecryptOnly = false),
            valid.copy(generatedInKeystore = false),
            valid.copy(strongBoxBacked = false),
            valid.copy(credentialOnlyAuth = false),
            valid.copy(authenticationRequired = false),
            valid.copy(perUseAuthentication = false),
            valid.copy(unlockedDeviceRequired = false),
            valid.copy(randomizedEncryptionRequired = false)
        )
        assertEquals(13, mutations.size)
        mutations.forEach(::blocked)
    }
}
