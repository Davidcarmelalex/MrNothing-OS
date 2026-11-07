package tech.mrnothing.os

import java.io.IOException
import java.security.GeneralSecurityException
import java.security.KeyStore

/**
 * SEC-014J: read-only alias collision preflight before any credential prompt.
 * A malformed or weaker existing key must never be treated as an empty slot.
 * No key creation, deletion, authentication, signing or consent occurs here.
 */
internal enum class OwnerEnrollmentAliasState {
    ABSENT,
    VERIFIED_EXISTING,
    UNTRUSTED_EXISTING,
    INSPECTION_FAILED
}

internal object OwnerEnrollmentAliasGate {
    fun evaluate(
        aliasPresent: Boolean,
        readiness: OwnerKeyReadiness
    ): OwnerEnrollmentAliasState = when {
        aliasPresent && readiness == OwnerKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH ->
            OwnerEnrollmentAliasState.VERIFIED_EXISTING
        aliasPresent -> OwnerEnrollmentAliasState.UNTRUSTED_EXISTING
        readiness != OwnerKeyReadiness.BLOCKED -> OwnerEnrollmentAliasState.INSPECTION_FAILED
        else -> OwnerEnrollmentAliasState.ABSENT
    }

    /** Any Keystore inspection error blocks enrollment rather than assuming absence. */
    fun inspect(): OwnerEnrollmentAliasState = try {
        val store = KeyStore.getInstance("AndroidKeyStore")
        store.load(null)
        val present = store.containsAlias(OwnerKeystorePreflight.KEY_ALIAS)
        val readiness = if (present) OwnerKeystorePreflight.inspectExisting()
            else OwnerKeyReadiness.BLOCKED
        evaluate(present, readiness)
    } catch (_: GeneralSecurityException) {
        OwnerEnrollmentAliasState.INSPECTION_FAILED
    } catch (_: IOException) {
        OwnerEnrollmentAliasState.INSPECTION_FAILED
    } catch (_: RuntimeException) {
        OwnerEnrollmentAliasState.INSPECTION_FAILED
    }
}
