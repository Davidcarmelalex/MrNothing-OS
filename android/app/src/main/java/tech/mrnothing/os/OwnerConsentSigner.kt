package tech.mrnothing.os

import android.annotation.TargetApi
import android.app.Activity
import android.hardware.biometrics.BiometricManager
import android.hardware.biometrics.BiometricPrompt
import android.os.Build
import android.os.CancellationSignal
import android.os.Looper
import java.io.IOException
import java.nio.charset.StandardCharsets
import java.security.GeneralSecurityException
import java.security.KeyStore
import java.security.Signature
import java.util.Base64
import java.util.concurrent.atomic.AtomicBoolean

/**
 * AGENT-004B: isolated per-use signer for a host-issued owner-consent challenge.
 *
 * This does not issue challenges, establish transport/device identity, grant Android
 * permissions, or execute actions. Call only with a challenge supplied by a trusted
 * host coordinator, never with model/tool-authored fields.
 */
internal sealed class OwnerConsentSigningOutcome {
    data class Signed(val envelopeJson: String) : OwnerConsentSigningOutcome()
    data class Refused(val reason: String) : OwnerConsentSigningOutcome()
}

internal object OwnerConsentSigner {
    private const val MIN_SIGNATURE_DER_BYTES = 8
    private const val MAX_SIGNATURE_DER_BYTES = 72
    private val signingInFlight = AtomicBoolean(false)

    /**
     * Starts one system-authenticated signing operation on the foreground Activity.
     * The returned signal lets the caller cancel; null means refusal happened before
     * a prompt was started. The callback is completed at most once.
     */
    @TargetApi(Build.VERSION_CODES.R)
    fun sign(
        activity: Activity,
        fields: OwnerConsentFields,
        callback: (OwnerConsentSigningOutcome) -> Unit
    ): CancellationSignal? {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            return refuse(callback, "UNSUPPORTED_PLATFORM")
        }
        if (Looper.myLooper() != Looper.getMainLooper()) {
            return refuse(callback, "MAIN_THREAD_REQUIRED")
        }
        if (activity.isFinishing || activity.isDestroyed ||
            !OwnerCredentialSafetyGate.isSafe(activity)
        ) {
            return refuse(callback, "UNSAFE_ACTIVITY_OR_DEVICE")
        }
        val canonical = OwnerConsentCanonicalizer.canonicalPayload(fields)
            ?: return refuse(callback, "INVALID_CHALLENGE_FIELDS")
        if (!signingInFlight.compareAndSet(false, true)) {
            return refuse(callback, "SIGNING_IN_PROGRESS")
        }

        val completed = AtomicBoolean(false)
        fun complete(outcome: OwnerConsentSigningOutcome) {
            if (completed.compareAndSet(false, true)) {
                signingInFlight.set(false)
                callback(outcome)
            }
        }

        val payloadBytes = canonical.toByteArray(StandardCharsets.US_ASCII)
        val signingMaterial = try {
            if (OwnerKeystorePreflight.inspectExisting() !=
                OwnerKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH
            ) {
                complete(OwnerConsentSigningOutcome.Refused("STRONGBOX_KEY_NOT_READY"))
                return null
            }
            val store = KeyStore.getInstance("AndroidKeyStore")
            store.load(null)
            val entry = store.getEntry(
                OwnerKeystorePreflight.KEY_ALIAS, null
            ) as? KeyStore.PrivateKeyEntry
                ?: run {
                    complete(OwnerConsentSigningOutcome.Refused("OWNER_KEY_MISSING"))
                    return null
                }
            val publicKey = entry.certificate?.publicKey
                ?: run {
                    complete(OwnerConsentSigningOutcome.Refused("OWNER_CERTIFICATE_MISSING"))
                    return null
                }
            val signature = Signature.getInstance("SHA256withECDSA")
            signature.initSign(entry.privateKey)
            signature.update(payloadBytes)
            signature to publicKey
        } catch (_: GeneralSecurityException) {
            complete(OwnerConsentSigningOutcome.Refused("KEYSTORE_OPERATION_FAILED"))
            return null
        } catch (_: IOException) {
            complete(OwnerConsentSigningOutcome.Refused("KEYSTORE_UNAVAILABLE"))
            return null
        } catch (_: RuntimeException) {
            complete(OwnerConsentSigningOutcome.Refused("KEYSTORE_UNAVAILABLE"))
            return null
        }

        val signature = signingMaterial.first
        val publicKey = signingMaterial.second
        val cancellation = CancellationSignal()
        cancellation.setOnCancelListener {
            activity.mainExecutor.execute {
                complete(OwnerConsentSigningOutcome.Refused("CANCELLED"))
            }
        }

        try {
            val authenticators =
                BiometricManager.Authenticators.BIOMETRIC_STRONG or
                    BiometricManager.Authenticators.DEVICE_CREDENTIAL
            val prompt = BiometricPrompt.Builder(activity)
                .setTitle("Authorize Mr. Nothing action")
                .setSubtitle("Action: ${fields.action} · Device: ${fields.deviceId}")
                .setDescription(
                    "Session: ${fields.sessionId}. One-use signature only; " +
                        "no device action executes in this step."
                )
                .setAllowedAuthenticators(authenticators)
                .setConfirmationRequired(true)
                .build()

            prompt.authenticate(
                BiometricPrompt.CryptoObject(signature),
                cancellation,
                activity.mainExecutor,
                object : BiometricPrompt.AuthenticationCallback() {
                    override fun onAuthenticationError(
                        errorCode: Int,
                        errString: CharSequence
                    ) {
                        complete(
                            OwnerConsentSigningOutcome.Refused("AUTHENTICATION_FAILED")
                        )
                    }

                    override fun onAuthenticationSucceeded(
                        result: BiometricPrompt.AuthenticationResult
                    ) {
                        if (activity.isFinishing || activity.isDestroyed ||
                            !OwnerCredentialSafetyGate.isSafe(activity)
                        ) {
                            complete(
                                OwnerConsentSigningOutcome.Refused("DEVICE_STATE_CHANGED")
                            )
                            return
                        }
                        val authenticatedSignature = result.cryptoObject?.signature
                        if (authenticatedSignature == null) {
                            complete(
                                OwnerConsentSigningOutcome.Refused("CRYPTO_OBJECT_MISSING")
                            )
                            return
                        }
                        try {
                            val der = authenticatedSignature.sign()
                            if (der.size !in MIN_SIGNATURE_DER_BYTES..MAX_SIGNATURE_DER_BYTES) {
                                complete(
                                    OwnerConsentSigningOutcome.Refused("INVALID_SIGNATURE_SIZE")
                                )
                                return
                            }
                            val verifier = Signature.getInstance("SHA256withECDSA")
                            verifier.initVerify(publicKey)
                            verifier.update(payloadBytes)
                            if (!verifier.verify(der)) {
                                complete(
                                    OwnerConsentSigningOutcome.Refused(
                                        "LOCAL_SIGNATURE_CHECK_FAILED"
                                    )
                                )
                                return
                            }
                            val envelope = encodeEnvelope(fields, der)
                            if (envelope == null) {
                                complete(
                                    OwnerConsentSigningOutcome.Refused("ENVELOPE_ENCODING_FAILED")
                                )
                            } else {
                                complete(OwnerConsentSigningOutcome.Signed(envelope))
                            }
                        } catch (_: GeneralSecurityException) {
                            complete(
                                OwnerConsentSigningOutcome.Refused("SIGNATURE_FAILED")
                            )
                        } catch (_: RuntimeException) {
                            complete(
                                OwnerConsentSigningOutcome.Refused("SIGNATURE_FAILED")
                            )
                        }
                    }

                    // A failed biometric attempt leaves the system prompt active so
                    // the user may retry or cancel. No signature is emitted here.
                    override fun onAuthenticationFailed() = Unit
                }
            )
        } catch (_: RuntimeException) {
            complete(OwnerConsentSigningOutcome.Refused("PROMPT_UNAVAILABLE"))
            return null
        }
        return cancellation
    }

    /** Pure encoder shared by the signer and JVM tests; never accepts a public key. */
    internal fun encodeEnvelope(
        fields: OwnerConsentFields,
        signatureDer: ByteArray
    ): String? {
        val canonical = OwnerConsentCanonicalizer.canonicalPayload(fields) ?: return null
        if (signatureDer.size !in MIN_SIGNATURE_DER_BYTES..MAX_SIGNATURE_DER_BYTES) {
            return null
        }
        val encodedSignature = Base64.getUrlEncoder()
            .withoutPadding()
            .encodeToString(signatureDer)
        return "{\"payload\":$canonical,\"signature\":\"$encodedSignature\"}"
    }

    private fun refuse(
        callback: (OwnerConsentSigningOutcome) -> Unit,
        reason: String
    ): CancellationSignal? {
        callback(OwnerConsentSigningOutcome.Refused(reason))
        return null
    }
}
