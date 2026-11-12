package tech.mrnothing.os

import android.app.Activity
import android.hardware.biometrics.BiometricManager
import android.hardware.biometrics.BiometricPrompt

/**
 * Single source of truth for the owner credential-only system prompt.
 *
 * Callers must perform the API-level and canAuthenticate preflights first.
 * No biometric authenticator or negative-button fallback is configured.
 */
internal object OwnerCredentialPromptFactory {
    fun create(
        activity: Activity,
        title: String,
        subtitle: String,
        description: String
    ): BiometricPrompt =
        BiometricPrompt.Builder(activity)
            .setTitle(title)
            .setSubtitle(subtitle)
            .setDescription(description)
            .setAllowedAuthenticators(
                BiometricManager.Authenticators.DEVICE_CREDENTIAL
            )
            .build()
}
