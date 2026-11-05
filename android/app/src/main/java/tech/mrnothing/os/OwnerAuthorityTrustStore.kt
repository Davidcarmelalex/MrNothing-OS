package tech.mrnothing.os

import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.DataInputStream
import java.io.DataOutputStream
import java.nio.charset.StandardCharsets
import java.security.MessageDigest

internal sealed interface AuthorityRecordRead {
    object Missing : AuthorityRecordRead
    data class Present(val bytes: ByteArray) : AuthorityRecordRead
    object Failed : AuthorityRecordRead
}

internal interface AuthorityRecordPersistence {
    fun read(): AuthorityRecordRead

    /** Must replace the complete record atomically or leave the previous record intact. */
    fun writeAtomically(bytes: ByteArray): Boolean
}

internal interface AuthorityTrustCrypto {
    /** Null means the Keystore state could not be trusted or inspected. */
    fun highestObservedGeneration(): Long?

    /** Creates a new, non-exportable generation marker and returns its record-bound proof. */
    fun createGenerationMarker(record: AuthorityTrustRecord): ByteArray?

    fun verifyGenerationMarker(record: AuthorityTrustRecord, proof: ByteArray): Boolean

    /** Returns IV || AES-GCM ciphertext-and-tag, or null on any failure. */
    fun encrypt(plaintext: ByteArray, associatedData: ByteArray): ByteArray?

    fun decrypt(envelope: ByteArray, associatedData: ByteArray): ByteArray?
}

internal enum class AuthorityRecoveryReason {
    ACTIVE_RECORD_MISSING,
    ACTIVE_RECORD_UNREADABLE,
    GENERATION_MARKER_AHEAD,
    MARKER_PROOF_MISMATCH
}

internal enum class AuthorityStoreCorruption {
    INVALID_GENERATION_WATERMARK,
    RECORD_WITHOUT_MARKER,
    INVALID_RECORD_GENERATION
}

internal sealed interface AuthorityTrustStoreState {
    object Empty : AuthorityTrustStoreState
    data class Active(val record: AuthorityTrustRecord) : AuthorityTrustStoreState
    data class RecoveryRequired(
        val highestObservedGeneration: Long,
        val reason: AuthorityRecoveryReason
    ) : AuthorityTrustStoreState
    object Unavailable : AuthorityTrustStoreState
    data class Corrupt(val reason: AuthorityStoreCorruption) : AuthorityTrustStoreState
}

internal enum class AuthorityStoreRefusal {
    INVALID_PROPOSAL,
    TRANSITION_NOT_ALLOWED
}

internal enum class AuthorityStoreFailure {
    MARKER_CREATION_FAILED,
    MARKER_PROOF_INVALID,
    ENCRYPTION_FAILED,
    ENVELOPE_ENCODING_FAILED,
    ATOMIC_PERSISTENCE_FAILED,
    READ_BACK_VERIFICATION_FAILED
}

internal sealed interface AuthorityTrustStoreCommit {
    data class Committed(val record: AuthorityTrustRecord) : AuthorityTrustStoreCommit
    data class Refused(val reason: AuthorityStoreRefusal) : AuthorityTrustStoreCommit
    data class Failed(val reason: AuthorityStoreFailure) : AuthorityTrustStoreCommit
}

/**
 * SEC-020B1 transaction coordinator.
 *
 * The generation marker is created before encryption and persistence. A crash
 * after marker creation therefore leaves the marker ahead of the active record;
 * inspect() refuses to load the older record and exposes only a recovery state.
 * Old marker aliases are never deleted by this class.
 *
 * This class is deliberately not connected to enrollment, permission grants or
 * command execution. A Ready proposal must come from SEC-020A after an
 * owner-visible ceremony; this store does not manufacture owner confirmation.
 */
internal class OwnerAuthorityTrustStore(
    private val crypto: AuthorityTrustCrypto,
    private val persistence: AuthorityRecordPersistence
) {
    fun inspect(): AuthorityTrustStoreState = synchronized(PROCESS_LOCK) {
        inspectLocked()
    }

    fun commit(proposal: AuthorityTrustDecision.Ready): AuthorityTrustStoreCommit =
        synchronized(PROCESS_LOCK) {
            val record = copyRecord(proposal.record)
            if (!AuthorityTrustStoreCodec.isValidRecord(record)) {
                return@synchronized AuthorityTrustStoreCommit.Refused(
                    AuthorityStoreRefusal.INVALID_PROPOSAL
                )
            }

            val before = inspectLocked()
            if (!transitionAllowed(proposal.mode, record, before)) {
                return@synchronized AuthorityTrustStoreCommit.Refused(
                    AuthorityStoreRefusal.TRANSITION_NOT_ALLOWED
                )
            }

            // This is intentionally the first durable mutation. If anything
            // below fails, the new generation remains visible as a watermark.
            val markerProof = crypto.createGenerationMarker(record)
                ?: return@synchronized AuthorityTrustStoreCommit.Failed(
                    AuthorityStoreFailure.MARKER_CREATION_FAILED
                )
            if (markerProof.size != AuthorityTrustStoreLimits.MARKER_PROOF_BYTES) {
                return@synchronized AuthorityTrustStoreCommit.Failed(
                    AuthorityStoreFailure.MARKER_PROOF_INVALID
                )
            }

            val plaintext = AuthorityTrustStoreCodec.encodeRecord(record, markerProof)
                ?: return@synchronized AuthorityTrustStoreCommit.Failed(
                    AuthorityStoreFailure.ENVELOPE_ENCODING_FAILED
                )
            val encrypted = crypto.encrypt(
                plaintext,
                AuthorityTrustStoreCodec.associatedData(record.generation)
            ) ?: return@synchronized AuthorityTrustStoreCommit.Failed(
                AuthorityStoreFailure.ENCRYPTION_FAILED
            )
            val envelope = AuthorityTrustStoreCodec.encodeEnvelope(
                record.generation,
                encrypted
            ) ?: return@synchronized AuthorityTrustStoreCommit.Failed(
                AuthorityStoreFailure.ENVELOPE_ENCODING_FAILED
            )
            if (!persistence.writeAtomically(envelope)) {
                return@synchronized AuthorityTrustStoreCommit.Failed(
                    AuthorityStoreFailure.ATOMIC_PERSISTENCE_FAILED
                )
            }

            // Never report success solely because write() returned. Re-open,
            // decrypt, validate and verify the marker from persisted bytes.
            val after = inspectLocked()
            if (after is AuthorityTrustStoreState.Active &&
                sameRecord(after.record, record)
            ) {
                AuthorityTrustStoreCommit.Committed(copyRecord(after.record))
            } else {
                AuthorityTrustStoreCommit.Failed(
                    AuthorityStoreFailure.READ_BACK_VERIFICATION_FAILED
                )
            }
        }

    private fun inspectLocked(): AuthorityTrustStoreState {
        val highest = crypto.highestObservedGeneration()
            ?: return AuthorityTrustStoreState.Unavailable
        if (highest < 0L) {
            return AuthorityTrustStoreState.Corrupt(
                AuthorityStoreCorruption.INVALID_GENERATION_WATERMARK
            )
        }

        return when (val stored = persistence.read()) {
            AuthorityRecordRead.Missing -> {
                if (highest == 0L) AuthorityTrustStoreState.Empty
                else AuthorityTrustStoreState.RecoveryRequired(
                    highest,
                    AuthorityRecoveryReason.ACTIVE_RECORD_MISSING
                )
            }
            AuthorityRecordRead.Failed -> AuthorityTrustStoreState.Unavailable
            is AuthorityRecordRead.Present -> {
                if (highest == 0L) {
                    return AuthorityTrustStoreState.Corrupt(
                        AuthorityStoreCorruption.RECORD_WITHOUT_MARKER
                    )
                }
                val envelope = AuthorityTrustStoreCodec.decodeEnvelope(stored.bytes)
                    ?: return AuthorityTrustStoreState.RecoveryRequired(
                        highest,
                        AuthorityRecoveryReason.ACTIVE_RECORD_UNREADABLE
                    )
                if (envelope.generation > highest) {
                    return AuthorityTrustStoreState.RecoveryRequired(
                        highest,
                        AuthorityRecoveryReason.ACTIVE_RECORD_UNREADABLE
                    )
                }
                if (envelope.generation < highest) {
                    return AuthorityTrustStoreState.RecoveryRequired(
                        highest,
                        AuthorityRecoveryReason.GENERATION_MARKER_AHEAD
                    )
                }
                val plaintext = crypto.decrypt(
                    envelope.encrypted,
                    AuthorityTrustStoreCodec.associatedData(envelope.generation)
                ) ?: return AuthorityTrustStoreState.RecoveryRequired(
                    highest,
                    AuthorityRecoveryReason.ACTIVE_RECORD_UNREADABLE
                )
                val decoded = AuthorityTrustStoreCodec.decodeRecord(plaintext)
                    ?: return AuthorityTrustStoreState.RecoveryRequired(
                        highest,
                        AuthorityRecoveryReason.ACTIVE_RECORD_UNREADABLE
                    )
                if (decoded.record.generation != envelope.generation) {
                    return AuthorityTrustStoreState.Corrupt(
                        AuthorityStoreCorruption.INVALID_RECORD_GENERATION
                    )
                }
                if (!crypto.verifyGenerationMarker(decoded.record, decoded.markerProof)) {
                    return AuthorityTrustStoreState.RecoveryRequired(
                        highest,
                        AuthorityRecoveryReason.MARKER_PROOF_MISMATCH
                    )
                }
                AuthorityTrustStoreState.Active(copyRecord(decoded.record))
            }
        }
    }

    private fun transitionAllowed(
        mode: AuthorityTrustMode,
        candidate: AuthorityTrustRecord,
        state: AuthorityTrustStoreState
    ): Boolean = when (mode) {
        AuthorityTrustMode.FIRST_INSTALL ->
            state === AuthorityTrustStoreState.Empty && candidate.generation == 1L
        AuthorityTrustMode.ROTATION ->
            state is AuthorityTrustStoreState.Active &&
                state.record.generation < Long.MAX_VALUE &&
                candidate.generation == state.record.generation + 1L
        AuthorityTrustMode.RECOVERY ->
            state is AuthorityTrustStoreState.RecoveryRequired &&
                state.highestObservedGeneration in 1 until Long.MAX_VALUE &&
                candidate.generation == state.highestObservedGeneration + 1L
    }

    private fun sameRecord(left: AuthorityTrustRecord, right: AuthorityTrustRecord): Boolean =
        left.keyId == right.keyId &&
            left.generation == right.generation &&
            left.fingerprint == right.fingerprint &&
            MessageDigest.isEqual(left.publicKeySpkiDer, right.publicKeySpkiDer)

    private fun copyRecord(record: AuthorityTrustRecord) = AuthorityTrustRecord(
        record.keyId,
        record.generation,
        record.publicKeySpkiDer.copyOf(),
        record.fingerprint
    )

    private companion object {
        // All instances in this app process serialize trust transitions.
        // The Android adapter is not exported and is intended for one process.
        val PROCESS_LOCK = Any()
    }
}

internal object AuthorityTrustStoreLimits {
    const val MAX_ENVELOPE_BYTES = 4096
    const val MARKER_PROOF_BYTES = 32
}

private object AuthorityTrustStoreCodec {
    private val envelopeMagic = "MRAENV01".toByteArray(StandardCharsets.US_ASCII)
    private val recordMagic = "MRAREC01".toByteArray(StandardCharsets.US_ASCII)
    private val aadDomain =
        "MRNOTHING-AUTHORITY-STORE-V1\u0000".toByteArray(StandardCharsets.US_ASCII)
    private val keyIdPattern = Regex("^[A-Za-z0-9._-]{1,64}$")
    private val fingerprintPattern = Regex("^SHA256:[0-9A-F]{64}$")
    private const val MAX_RECORD_BYTES = 512
    private const val MAX_ENCRYPTED_BYTES = AuthorityTrustStoreLimits.MAX_ENVELOPE_BYTES - 20

    data class DecodedRecord(
        val record: AuthorityTrustRecord,
        val markerProof: ByteArray
    )

    data class DecodedEnvelope(
        val generation: Long,
        val encrypted: ByteArray
    )

    fun isValidRecord(record: AuthorityTrustRecord): Boolean {
        if (!keyIdPattern.matches(record.keyId) || record.generation <= 0L) return false
        if (record.publicKeySpkiDer.isEmpty() || record.publicKeySpkiDer.size > 128) return false
        if (!fingerprintPattern.matches(record.fingerprint)) return false
        return OwnerAuthorityTrustCeremony.fingerprintForOwner(record.publicKeySpkiDer) ==
            record.fingerprint
    }

    fun encodeRecord(record: AuthorityTrustRecord, markerProof: ByteArray): ByteArray? {
        if (!isValidRecord(record) ||
            markerProof.size != AuthorityTrustStoreLimits.MARKER_PROOF_BYTES
        ) return null
        return try {
            val bytes = ByteArrayOutputStream()
            DataOutputStream(bytes).use { output ->
                output.write(recordMagic)
                output.writeLong(record.generation)
                writeField(output, record.keyId.toByteArray(StandardCharsets.US_ASCII))
                writeField(output, record.publicKeySpkiDer)
                writeField(output, record.fingerprint.toByteArray(StandardCharsets.US_ASCII))
                writeField(output, markerProof)
            }
            val result = bytes.toByteArray()
            if (result.size > MAX_RECORD_BYTES) null else result
        } catch (_: RuntimeException) {
            null
        }
    }

    fun decodeRecord(bytes: ByteArray): DecodedRecord? {
        if (bytes.isEmpty() || bytes.size > MAX_RECORD_BYTES) return null
        return try {
            DataInputStream(ByteArrayInputStream(bytes)).use { input ->
                val magic = ByteArray(recordMagic.size)
                input.readFully(magic)
                if (!MessageDigest.isEqual(magic, recordMagic)) return null
                val generation = input.readLong()
                val keyIdBytes = readField(input, 64) ?: return null
                val spki = readField(input, 128) ?: return null
                val fingerprintBytes = readField(input, 71) ?: return null
                val proof = readField(input, AuthorityTrustStoreLimits.MARKER_PROOF_BYTES)
                    ?: return null
                if (proof.size != AuthorityTrustStoreLimits.MARKER_PROOF_BYTES ||
                    input.available() != 0
                ) return null
                val keyId = strictAscii(keyIdBytes) ?: return null
                val fingerprint = strictAscii(fingerprintBytes) ?: return null
                val record = AuthorityTrustRecord(keyId, generation, spki, fingerprint)
                if (!isValidRecord(record)) return null
                DecodedRecord(record, proof)
            }
        } catch (_: Exception) {
            null
        }
    }

    fun encodeEnvelope(generation: Long, encrypted: ByteArray): ByteArray? {
        if (generation <= 0L || encrypted.size !in 28..MAX_ENCRYPTED_BYTES) return null
        return try {
            val bytes = ByteArrayOutputStream()
            DataOutputStream(bytes).use { output ->
                output.write(envelopeMagic)
                output.writeLong(generation)
                output.writeInt(encrypted.size)
                output.write(encrypted)
            }
            val result = bytes.toByteArray()
            if (result.size > AuthorityTrustStoreLimits.MAX_ENVELOPE_BYTES) null else result
        } catch (_: RuntimeException) {
            null
        }
    }

    fun decodeEnvelope(bytes: ByteArray): DecodedEnvelope? {
        if (bytes.size !in 20..AuthorityTrustStoreLimits.MAX_ENVELOPE_BYTES) return null
        return try {
            DataInputStream(ByteArrayInputStream(bytes)).use { input ->
                val magic = ByteArray(envelopeMagic.size)
                input.readFully(magic)
                if (!MessageDigest.isEqual(magic, envelopeMagic)) return null
                val generation = input.readLong()
                val length = input.readInt()
                if (generation <= 0L || length !in 28..MAX_ENCRYPTED_BYTES ||
                    length != input.available()
                ) return null
                val encrypted = ByteArray(length)
                input.readFully(encrypted)
                DecodedEnvelope(generation, encrypted)
            }
        } catch (_: Exception) {
            null
        }
    }

    fun associatedData(generation: Long): ByteArray {
        val bytes = ByteArrayOutputStream()
        DataOutputStream(bytes).use { output ->
            output.write(aadDomain)
            output.writeLong(generation)
        }
        return bytes.toByteArray()
    }

    private fun writeField(output: DataOutputStream, value: ByteArray) {
        output.writeInt(value.size)
        output.write(value)
    }

    private fun readField(input: DataInputStream, maximum: Int): ByteArray? {
        val length = input.readInt()
        if (length !in 1..maximum || length > input.available()) return null
        return ByteArray(length).also(input::readFully)
    }

    private fun strictAscii(bytes: ByteArray): String? {
        val value = String(bytes, StandardCharsets.US_ASCII)
        return if (value.toByteArray(StandardCharsets.US_ASCII).contentEquals(bytes)) value else null
    }
}
