package tech.mrnothing.os

import android.os.Build
import android.security.keystore.KeyProperties
import android.test.InstrumentationTestCase

/**
 * SEC-023B1B1-QA: inspect the actual Android KeyGenParameterSpec on a disposable
 * emulator. No AndroidKeyStore provider is opened, and no key is generated.
 *
 * The positive input intentionally simulates StrongBox availability to inspect
 * the requested *specification*, not the emulator's hardware capabilities.
 * This does not prove physical Pixel 9 Pro StrongBox interoperability.
 */
class MemoryVaultKeySpecContractTest : InstrumentationTestCase() {
    private fun eligibleSignals() = MemoryVaultProvisioningSignals(
        apiLevel = Build.VERSION.SDK_INT,
        primaryOwnerProfile = true,
        trustedAppCaller = true,
        foregroundOwnerUi = true,
        deviceUnlocked = true,
        secureDeviceCredentialConfigured = true,
        explicitMemoryOptIn = true,
        strongBoxAdvertised = true,
        aliasAbsent = true
    )

    fun testRequestedKeystorePropertiesAreExactAndNonDowngraded() {
        assertTrue("QA-005 requires Android 12+ for this contract", Build.VERSION.SDK_INT >= 31)
        val spec = MemoryVaultKeySpecDraft.forSecurityReview(eligibleSignals())
        assertNotNull("eligible draft must produce a specification", spec)
        val actual = requireNotNull(spec)
        assertEquals(MemoryVaultKeySpecDraft.KEY_ALIAS, actual.keystoreAlias)
        assertEquals(
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
            actual.purposes
        )
        assertEquals(256, actual.keySize)
        assertEquals(listOf(KeyProperties.BLOCK_MODE_GCM), actual.blockModes.toList())
        assertEquals(
            listOf(KeyProperties.ENCRYPTION_PADDING_NONE),
            actual.encryptionPaddings.toList()
        )
        assertTrue(actual.isRandomizedEncryptionRequired)
        assertTrue(actual.isUnlockedDeviceRequired)
        assertTrue(actual.isUserAuthenticationRequired)
        assertEquals(0, actual.userAuthenticationValidityDurationSeconds)
        assertEquals(KeyProperties.AUTH_DEVICE_CREDENTIAL, actual.userAuthenticationType)
        assertTrue("StrongBox must not be downgraded", actual.isStrongBoxBacked)
    }

    fun testMissingExplicitOwnerConsentCannotProduceSpec() {
        assertNull(
            MemoryVaultKeySpecDraft.forSecurityReview(
                eligibleSignals().copy(explicitMemoryOptIn = false)
            )
        )
    }

    fun testMissingStrongBoxCannotProduceSpec() {
        assertNull(
            MemoryVaultKeySpecDraft.forSecurityReview(
                eligibleSignals().copy(strongBoxAdvertised = false)
            )
        )
    }

    fun testExistingAliasCannotProduceSpec() {
        assertNull(
            MemoryVaultKeySpecDraft.forSecurityReview(
                eligibleSignals().copy(aliasAbsent = false)
            )
        )
    }
}
