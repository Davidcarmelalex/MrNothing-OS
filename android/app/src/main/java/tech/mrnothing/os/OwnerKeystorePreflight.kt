package tech.mrnothing.os

import android.security.keystore.KeyInfo
import java.io.IOException
import java.math.BigInteger
import java.security.GeneralSecurityException
import java.security.KeyFactory
import java.security.KeyStore
import java.security.interfaces.ECPublicKey

/**
 * SEC-014G: READ-ONLY readiness inspection of a future AndroidKeyStore owner key.
 * This cannot create an identity, grant consent, sign commands, or authenticate
 * an owner. Absence of a trusted enrollment flow means the app always blocks.
 */
internal data class OwnerKeySignals(
    val keyPresent: Boolean,
    val ecAlgorithm: Boolean,
    val p256PublicKey: Boolean,
    val hardwareBacked: Boolean,
    val ownerAuthenticationRequired: Boolean,
    val perUseAuthentication: Boolean
)

internal enum class OwnerKeyReadiness {
    BLOCKED,
    EXISTING_KEY_REQUIRES_OWNER_AUTH
}

internal object OwnerKeystorePreflight {
    internal const val KEY_ALIAS = "mrnothing_owner_consent_p256_v1"
    private val p256Order = BigInteger(
        "ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551", 16
    )

    fun evaluate(signals: OwnerKeySignals): OwnerKeyReadiness =
        if (signals.keyPresent &&
            signals.ecAlgorithm &&
            signals.p256PublicKey &&
            signals.hardwareBacked &&
            signals.ownerAuthenticationRequired &&
            signals.perUseAuthentication
        ) OwnerKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH
        else OwnerKeyReadiness.BLOCKED

    /** Positive readiness is NOT proof of owner authentication or consent. */
    fun inspectExisting(): OwnerKeyReadiness {
        return try {
        val store = KeyStore.getInstance("AndroidKeyStore")
        store.load(null)
        val entry = store.getEntry(KEY_ALIAS, null) as? KeyStore.PrivateKeyEntry
            ?: return OwnerKeyReadiness.BLOCKED
        val privateKey = entry.privateKey
        val publicKey = entry.certificate?.publicKey as? ECPublicKey
            ?: return OwnerKeyReadiness.BLOCKED
        val factory = KeyFactory.getInstance(privateKey.algorithm, "AndroidKeyStore")
        val info = factory.getKeySpec(privateKey, KeyInfo::class.java)
        evaluate(
            OwnerKeySignals(
                keyPresent = true,
                ecAlgorithm = privateKey.algorithm.equals("EC", ignoreCase = true),
                p256PublicKey = publicKey.params.curve.field.fieldSize == 256 &&
                    publicKey.params.order == p256Order,
                hardwareBacked = info.isInsideSecureHardware,
                ownerAuthenticationRequired = info.isUserAuthenticationRequired,
                perUseAuthentication = info.userAuthenticationValidityDurationSeconds <= 0
            )
        )
    } catch (_: GeneralSecurityException) {
        OwnerKeyReadiness.BLOCKED
    } catch (_: IOException) {
        OwnerKeyReadiness.BLOCKED
        } catch (_: RuntimeException) {
            OwnerKeyReadiness.BLOCKED
        }
    }
}
