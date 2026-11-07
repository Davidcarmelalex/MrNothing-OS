package tech.mrnothing.os

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.nio.charset.StandardCharsets
import java.security.GeneralSecurityException
import java.security.KeyFactory
import java.security.MessageDigest
import java.security.PublicKey
import java.security.Signature
import java.security.spec.X509EncodedKeySpec
import org.bouncycastle.jce.provider.BouncyCastleProvider

/**
 * SEC-020A: offline owner-authority trust ceremony policy.
 *
 * This class validates a proposed trust transition only. It does not persist an
 * anchor, create Keystore aliases, open a network connection, grant permissions,
 * issue consent or execute commands. A future caller must obtain the generation
 * watermark from a device-backed, rollback-resistant store and must present the
 * displayed fingerprint for comparison with an independently authenticated
 * out-of-band value.
 */
internal data class AuthorityTrustCandidate(
    val keyId: String,
    val generation: Long,
    val publicKeySpkiDer: ByteArray
)

internal data class AuthorityTrustRecord(
    val keyId: String,
    val generation: Long,
    val publicKeySpkiDer: ByteArray,
    val fingerprint: String
)

internal enum class AuthorityTrustMode {
    FIRST_INSTALL,
    ROTATION,
    RECOVERY
}

internal enum class AuthorityTrustBlockReason {
    INVALID_CANDIDATE,
    INVALID_ACTIVE_RECORD,
    INITIAL_STATE_ALREADY_EXISTS,
    INITIAL_GENERATION_MUST_BE_ONE,
    OWNER_CONFIRMATION_REQUIRED,
    OUT_OF_BAND_FINGERPRINT_MISMATCH,
    GENERATION_MARKER_MISMATCH,
    NEXT_GENERATION_REQUIRED,
    ROTATION_SIGNATURE_INVALID,
    AUTHORITY_KEY_MUST_CHANGE,
    RECOVERY_NOT_ELIGIBLE,
    GENERATION_EXHAUSTED
}

internal sealed interface AuthorityTrustDecision {
    data class Ready(
        val mode: AuthorityTrustMode,
        val record: AuthorityTrustRecord
    ) : AuthorityTrustDecision

    data class Blocked(
        val reason: AuthorityTrustBlockReason
    ) : AuthorityTrustDecision
}

/**
 * Deterministic policy for first-install, signed-rotation and recovery
 * ceremonies. The boolean ownerConfirmation is a UI assertion, not a credential
 * primitive; production callers must derive it only from a foreground,
 * owner-visible confirmation flow and a fresh Android system-credential result.
 */
internal object OwnerAuthorityTrustCeremony {
    private const val MAX_SPKI_BYTES = 128
    private const val SIGNATURE_BYTES = 64
    private val keyIdPattern = Regex("^[A-Za-z0-9._-]{1,64}$")
    private val fingerprintPattern = Regex("^SHA256:[0-9A-F]{64}$")
    private val hex = "0123456789ABCDEF"
    // Explicit software provider: AndroidKeyStore cannot import arbitrary owner SPKI keys.
    // Keep this instance local to the ceremony; never mutate the process-wide provider registry.
    private val ed25519Provider = BouncyCastleProvider()
    private val rotationDomain =
        "MRNOTHING-OWNER-AUTHORITY-ROTATION-V1\u0000".toByteArray(StandardCharsets.US_ASCII)

    private data class ValidatedCandidate(
        val publicKey: PublicKey,
        val fingerprint: String,
        val digest: ByteArray
    )

    /** Fingerprint of the exact canonical Ed25519 SubjectPublicKeyInfo DER bytes. */
    fun fingerprintForOwner(publicKeySpkiDer: ByteArray): String? {
        val candidate = validateKey(publicKeySpkiDer) ?: return null
        return candidate.fingerprint
    }

    /**
     * First install is eligible only when the trusted generation watermark is
     * exactly zero, the candidate generation is exactly one, the key is valid,
     * the out-of-band fingerprint matches in constant time, and owner
     * confirmation is present. An existing watermark is never treated as empty.
     */
    fun prepareFirstInstall(
        candidate: AuthorityTrustCandidate,
        independentlyObservedFingerprint: String,
        ownerConfirmation: Boolean,
        highestObservedGeneration: Long
    ): AuthorityTrustDecision {
        if (highestObservedGeneration != 0L) {
            return blocked(AuthorityTrustBlockReason.INITIAL_STATE_ALREADY_EXISTS)
        }
        if (candidate.generation != 1L) {
            return blocked(AuthorityTrustBlockReason.INITIAL_GENERATION_MUST_BE_ONE)
        }
        val validated = validateCandidate(candidate)
            ?: return blocked(AuthorityTrustBlockReason.INVALID_CANDIDATE)
        if (!fingerprintMatches(validated.digest, independentlyObservedFingerprint)) {
            return blocked(AuthorityTrustBlockReason.OUT_OF_BAND_FINGERPRINT_MISMATCH)
        }
        if (!ownerConfirmation) {
            return blocked(AuthorityTrustBlockReason.OWNER_CONFIRMATION_REQUIRED)
        }
        return ready(AuthorityTrustMode.FIRST_INSTALL, candidate, validated.fingerprint)
    }

    /**
     * Rotation requires the current authority to sign a domain-separated,
     * length-prefixed statement for exactly the next generation. The owner also
     * compares the candidate fingerprint out of band before the transition is
     * eligible. The caller must commit the result atomically with its watermark.
     */
    fun prepareRotation(
        current: AuthorityTrustRecord,
        candidate: AuthorityTrustCandidate,
        rotationSignature: ByteArray,
        independentlyObservedFingerprint: String,
        ownerConfirmation: Boolean,
        highestObservedGeneration: Long
    ): AuthorityTrustDecision {
        val currentCandidate = AuthorityTrustCandidate(
            current.keyId, current.generation, current.publicKeySpkiDer
        )
        val currentValidated = validateCandidate(currentCandidate)
            ?: return blocked(AuthorityTrustBlockReason.INVALID_ACTIVE_RECORD)
        if (!fingerprintMatches(currentValidated.digest, current.fingerprint)) {
            return blocked(AuthorityTrustBlockReason.INVALID_ACTIVE_RECORD)
        }
        if (highestObservedGeneration != current.generation) {
            return blocked(AuthorityTrustBlockReason.GENERATION_MARKER_MISMATCH)
        }
        if (current.generation == Long.MAX_VALUE) {
            return blocked(AuthorityTrustBlockReason.GENERATION_EXHAUSTED)
        }
        if (candidate.generation != current.generation + 1L) {
            return blocked(AuthorityTrustBlockReason.NEXT_GENERATION_REQUIRED)
        }
        val next = validateCandidate(candidate)
            ?: return blocked(AuthorityTrustBlockReason.INVALID_CANDIDATE)
        if (candidate.keyId == current.keyId ||
            MessageDigest.isEqual(candidate.publicKeySpkiDer, current.publicKeySpkiDer)
        ) {
            return blocked(AuthorityTrustBlockReason.AUTHORITY_KEY_MUST_CHANGE)
        }
        if (!fingerprintMatches(next.digest, independentlyObservedFingerprint)) {
            return blocked(AuthorityTrustBlockReason.OUT_OF_BAND_FINGERPRINT_MISMATCH)
        }
        if (!verifyRotation(currentValidated.publicKey, candidate, rotationSignature)) {
            return blocked(AuthorityTrustBlockReason.ROTATION_SIGNATURE_INVALID)
        }
        if (!ownerConfirmation) {
            return blocked(AuthorityTrustBlockReason.OWNER_CONFIRMATION_REQUIRED)
        }
        return ready(AuthorityTrustMode.ROTATION, candidate, next.fingerprint)
    }

    /**
     * Recovery is not a reset. It is eligible only when the active record is
     * absent/unreadable while a non-zero trusted generation watermark still
     * exists. The candidate must be exactly one generation newer than that
     * watermark and requires out-of-band fingerprint plus owner confirmation.
     */
    fun prepareRecovery(
        candidate: AuthorityTrustCandidate,
        independentlyObservedFingerprint: String,
        ownerConfirmation: Boolean,
        highestObservedGeneration: Long,
        activeRecordPresent: Boolean
    ): AuthorityTrustDecision {
        if (activeRecordPresent || highestObservedGeneration <= 0L) {
            return blocked(AuthorityTrustBlockReason.RECOVERY_NOT_ELIGIBLE)
        }
        if (highestObservedGeneration == Long.MAX_VALUE) {
            return blocked(AuthorityTrustBlockReason.GENERATION_EXHAUSTED)
        }
        if (candidate.generation != highestObservedGeneration + 1L) {
            return blocked(AuthorityTrustBlockReason.NEXT_GENERATION_REQUIRED)
        }
        val validated = validateCandidate(candidate)
            ?: return blocked(AuthorityTrustBlockReason.INVALID_CANDIDATE)
        if (!fingerprintMatches(validated.digest, independentlyObservedFingerprint)) {
            return blocked(AuthorityTrustBlockReason.OUT_OF_BAND_FINGERPRINT_MISMATCH)
        }
        if (!ownerConfirmation) {
            return blocked(AuthorityTrustBlockReason.OWNER_CONFIRMATION_REQUIRED)
        }
        return ready(AuthorityTrustMode.RECOVERY, candidate, validated.fingerprint)
    }

    /** Canonical rotation bytes for an offline authority signer. */
    fun rotationPayload(candidate: AuthorityTrustCandidate): ByteArray? {
        val validated = validateCandidate(candidate) ?: return null
        return try {
            val bytes = ByteArrayOutputStream()
            bytes.write(rotationDomain)
            DataOutputStream(bytes).use { output ->
                output.writeLong(candidate.generation)
                writeField(output, candidate.keyId.toByteArray(StandardCharsets.US_ASCII))
                writeField(output, candidate.publicKeySpkiDer)
                writeField(output, validated.fingerprint.toByteArray(StandardCharsets.US_ASCII))
                output.flush()
            }
            bytes.toByteArray()
        } catch (_: RuntimeException) {
            null
        }
    }

    private fun writeField(output: DataOutputStream, value: ByteArray) {
        output.writeInt(value.size)
        output.write(value)
    }

    private fun verifyRotation(
        currentPublicKey: PublicKey,
        candidate: AuthorityTrustCandidate,
        signatureBytes: ByteArray
    ): Boolean {
        if (signatureBytes.size != SIGNATURE_BYTES) return false
        val payload = rotationPayload(candidate) ?: return false
        return try {
            val verifier = Signature.getInstance("Ed25519", ed25519Provider)
            verifier.initVerify(currentPublicKey)
            verifier.update(payload)
            verifier.verify(signatureBytes)
        } catch (_: GeneralSecurityException) {
            false
        } catch (_: RuntimeException) {
            false
        }
    }

    private fun validateCandidate(candidate: AuthorityTrustCandidate): ValidatedCandidate? {
        if (!keyIdPattern.matches(candidate.keyId) || candidate.generation <= 0L) return null
        return validateKey(candidate.publicKeySpkiDer)
    }

    private fun validateKey(spkiDer: ByteArray): ValidatedCandidate? {
        if (spkiDer.isEmpty() || spkiDer.size > MAX_SPKI_BYTES) return null
        return try {
            val key = KeyFactory.getInstance("Ed25519", ed25519Provider)
                .generatePublic(X509EncodedKeySpec(spkiDer))
            val canonical = key.encoded ?: return null
            if (!MessageDigest.isEqual(canonical, spkiDer)) return null
            val digest = MessageDigest.getInstance("SHA-256").digest(spkiDer)
            ValidatedCandidate(key, formatFingerprint(digest), digest)
        } catch (_: GeneralSecurityException) {
            null
        } catch (_: IllegalArgumentException) {
            null
        } catch (_: RuntimeException) {
            null
        }
    }

    private fun formatFingerprint(digest: ByteArray): String {
        if (digest.size != 32) return ""
        val output = StringBuilder("SHA256:")
        for (byte in digest) {
            val value = byte.toInt() and 0xff
            output.append(hex[value ushr 4])
            output.append(hex[value and 0x0f])
        }
        return output.toString()
    }

    private fun fingerprintMatches(digest: ByteArray, supplied: String): Boolean {
        if (!fingerprintPattern.matches(supplied)) return false
        val suppliedDigest = ByteArray(32)
        for (index in suppliedDigest.indices) {
            val offset = 7 + index * 2
            val high = supplied[offset].digitToIntOrNull(16) ?: return false
            val low = supplied[offset + 1].digitToIntOrNull(16) ?: return false
            suppliedDigest[index] = ((high shl 4) or low).toByte()
        }
        return MessageDigest.isEqual(digest, suppliedDigest)
    }

    private fun ready(
        mode: AuthorityTrustMode,
        candidate: AuthorityTrustCandidate,
        fingerprint: String
    ) = AuthorityTrustDecision.Ready(
        mode,
        AuthorityTrustRecord(
            candidate.keyId,
            candidate.generation,
            candidate.publicKeySpkiDer.copyOf(),
            fingerprint
        )
    )

    private fun blocked(reason: AuthorityTrustBlockReason) =
        AuthorityTrustDecision.Blocked(reason)
}
