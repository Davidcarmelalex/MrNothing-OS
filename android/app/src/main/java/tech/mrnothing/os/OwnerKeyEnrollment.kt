package tech.mrnothing.os

import android.content.Context
import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.io.IOException
import java.security.GeneralSecurityException
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.spec.ECGenParameterSpec
import java.security.cert.X509Certificate

/**
 * SEC-014H: local, opt-in enrollment of a non-exportable StrongBox P-256 key.
 * Does NOT sign anything, issue consent, enroll a remote principal or execute an agent.
 * Caller must first verify a fresh local system credential via OwnerEnrollmentState.
 */
internal enum class OwnerEnrollmentResult {
    ENROLLED_LOCAL_KEY_ONLY,
    EXISTING_ALIAS_NOT_OVERWRITTEN,
    BLOCKED_UNSAFE_DEVICE,
    BLOCKED_UNSUPPORTED_PLATFORM,
    BLOCKED_KEYSTORE
}

internal object OwnerKeyEnrollment {
    fun enrollAfterCredential(context: Context): OwnerEnrollmentResult {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            return OwnerEnrollmentResult.BLOCKED_UNSUPPORTED_PLATFORM
        }
        if (!OwnerCredentialSafetyGate.isSafe(context)) {
            return OwnerEnrollmentResult.BLOCKED_UNSAFE_DEVICE
        }
        return try {
            val store = KeyStore.getInstance("AndroidKeyStore")
            store.load(null)
            // Never replace, rotate or delete a pre-existing identity implicitly.
            if (store.containsAlias(OwnerKeystorePreflight.KEY_ALIAS)) {
                return OwnerEnrollmentResult.EXISTING_ALIAS_NOT_OVERWRITTEN
            }
            // Bind this single local key-generation attempt to an unpredictable
            // challenge. This is not remote attestation or owner identity proof.
            val challenge = OwnerAttestationChallenge.create()
            val generator = KeyPairGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_EC, "AndroidKeyStore"
            )
            val spec = KeyGenParameterSpec.Builder(
                OwnerKeystorePreflight.KEY_ALIAS,
                KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
            )
                .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
                .setDigests(KeyProperties.DIGEST_SHA256)
                .setUserAuthenticationRequired(true)
                .setUserAuthenticationParameters(
                    0, KeyProperties.AUTH_BIOMETRIC_STRONG or
                        KeyProperties.AUTH_DEVICE_CREDENTIAL
                )
                // No fallback to software-only or TEE-only keys if StrongBox is absent.
                .setIsStrongBoxBacked(true)
                .setAttestationChallenge(challenge)
                .build()
            generator.initialize(spec)
            generator.generateKeyPair()
            // A matching local extension is only a prerequisite. Certificate
            // chain trust, verified boot, owner binding and revocation remain
            // separate, unimplemented gates. Never issue consent from this.
            val certificate = store.getCertificate(
                OwnerKeystorePreflight.KEY_ALIAS
            ) as? X509Certificate
            if (!OwnerAttestationChallenge.matchesLocalEvidence(
                    certificate?.getExtensionValue(OwnerAttestationChallenge.EXTENSION_OID),
                    challenge
                )
            ) return OwnerEnrollmentResult.BLOCKED_KEYSTORE
            if (!OwnerCredentialSafetyGate.isSafe(context)) {
                return OwnerEnrollmentResult.BLOCKED_UNSAFE_DEVICE
            }
            if (OwnerKeystorePreflight.inspectExisting() ==
                OwnerKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH
            ) OwnerEnrollmentResult.ENROLLED_LOCAL_KEY_ONLY
            else OwnerEnrollmentResult.BLOCKED_KEYSTORE
        } catch (_: GeneralSecurityException) {
            OwnerEnrollmentResult.BLOCKED_KEYSTORE
        } catch (_: IOException) {
            OwnerEnrollmentResult.BLOCKED_KEYSTORE
        } catch (_: RuntimeException) {
            OwnerEnrollmentResult.BLOCKED_KEYSTORE
        }
    }
}
