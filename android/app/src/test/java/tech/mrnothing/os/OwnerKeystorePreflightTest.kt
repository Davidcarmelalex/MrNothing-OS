package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

/** Pure policy tests; AndroidKeyStore runtime remains untested. */
class OwnerKeystorePreflightTest {
    private fun valid() = OwnerKeySignals(
        keyPresent = true,
        ecAlgorithm = true,
        p256PublicKey = true,
        hardwareBacked = true,
        strongBoxBacked = true,
        credentialAuthAllowed = true,
        ownerAuthenticationRequired = true,
        perUseAuthentication = true
    )

    @Test fun existingValidKeyIsStillNotConsent() {
        assertEquals(
            OwnerKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH,
            OwnerKeystorePreflight.evaluate(valid())
        )
    }

    @Test fun missingKeyBlocks() = assertBlocked(valid().copy(keyPresent = false))
    @Test fun wrongAlgorithmBlocks() = assertBlocked(valid().copy(ecAlgorithm = false))
    @Test fun wrongCurveBlocks() = assertBlocked(valid().copy(p256PublicKey = false))
    @Test fun softwareKeyBlocks() = assertBlocked(valid().copy(hardwareBacked = false))
    @Test fun teeOnlyKeyBlocksEvenWhenHardwareBacked() =
        assertBlocked(valid().copy(strongBoxBacked = false))
    @Test fun biometricOnlyKeyBlocksWithoutDeviceCredential() =
        assertBlocked(valid().copy(credentialAuthAllowed = false))
    @Test fun noOwnerAuthenticationBlocks() =
        assertBlocked(valid().copy(ownerAuthenticationRequired = false))
    @Test fun reusableAuthenticationBlocks() =
        assertBlocked(valid().copy(perUseAuthentication = false))

    @Test fun everySingleMissingRequirementBlocks() {
        listOf(
            valid().copy(keyPresent = false),
            valid().copy(ecAlgorithm = false),
            valid().copy(p256PublicKey = false),
            valid().copy(hardwareBacked = false),
            valid().copy(strongBoxBacked = false),
            valid().copy(credentialAuthAllowed = false),
            valid().copy(ownerAuthenticationRequired = false),
            valid().copy(perUseAuthentication = false)
        ).forEach(::assertBlocked)
    }

    private fun assertBlocked(signals: OwnerKeySignals) {
        assertEquals(OwnerKeyReadiness.BLOCKED, OwnerKeystorePreflight.evaluate(signals))
    }
}
