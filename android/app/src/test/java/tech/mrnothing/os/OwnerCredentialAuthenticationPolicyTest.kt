package tech.mrnothing.os

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class OwnerCredentialAuthenticationPolicyTest {
    @Test fun api29FailsClosedWithoutLegacyFallback() {
        assertFalse(OwnerCredentialAuthenticationPolicy.supportsCredentialOnlyPrompt(29))
        assertFalse(
            OwnerCredentialAuthenticationPolicy.acceptsDeviceCredential(
                29, DEVICE_CREDENTIAL, DEVICE_CREDENTIAL
            )
        )
    }

    @Test fun api30AndLaterSupportCredentialOnlyPrompt() {
        assertTrue(OwnerCredentialAuthenticationPolicy.supportsCredentialOnlyPrompt(30))
        assertTrue(OwnerCredentialAuthenticationPolicy.supportsCredentialOnlyPrompt(35))
    }

    @Test fun acceptsOnlyExplicitDeviceCredentialResult() {
        assertTrue(
            OwnerCredentialAuthenticationPolicy.acceptsDeviceCredential(
                35, DEVICE_CREDENTIAL, DEVICE_CREDENTIAL
            )
        )
    }

    @Test fun biometricResultIsRejected() {
        assertFalse(
            OwnerCredentialAuthenticationPolicy.acceptsDeviceCredential(
                35, BIOMETRIC, DEVICE_CREDENTIAL
            )
        )
    }

    @Test fun unknownResultIsRejected() {
        assertFalse(
            OwnerCredentialAuthenticationPolicy.acceptsDeviceCredential(
                35, UNKNOWN, DEVICE_CREDENTIAL
            )
        )
    }

    @Test fun futureOrUnexpectedResultIsRejected() {
        assertFalse(
            OwnerCredentialAuthenticationPolicy.acceptsDeviceCredential(
                35, 99, DEVICE_CREDENTIAL
            )
        )
    }

    private companion object {
        const val DEVICE_CREDENTIAL = 1
        const val BIOMETRIC = 2
        const val UNKNOWN = -1
    }
}
