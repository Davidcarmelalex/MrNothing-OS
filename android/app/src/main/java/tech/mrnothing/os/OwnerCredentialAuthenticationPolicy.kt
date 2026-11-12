package tech.mrnothing.os

/**
 * Fail-closed policy for the platform BiometricPrompt credential-only path.
 *
 * Android 11/API 30 introduced setAllowedAuthenticators(DEVICE_CREDENTIAL).
 * Older versions are intentionally unsupported rather than falling back to a
 * deprecated confirmation Intent, biometric authentication, or software prompt.
 */
internal object OwnerCredentialAuthenticationPolicy {
    const val MIN_CREDENTIAL_ONLY_API = 30

    fun supportsCredentialOnlyPrompt(apiLevel: Int): Boolean =
        apiLevel >= MIN_CREDENTIAL_ONLY_API

    fun acceptsDeviceCredential(
        apiLevel: Int,
        authenticationType: Int,
        deviceCredentialType: Int
    ): Boolean =
        supportsCredentialOnlyPrompt(apiLevel) &&
            authenticationType == deviceCredentialType
}
