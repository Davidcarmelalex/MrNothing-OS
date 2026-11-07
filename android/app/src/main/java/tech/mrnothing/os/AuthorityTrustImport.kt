package tech.mrnothing.os

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.util.Base64

internal data class ParsedAuthorityTrustImport(
    val candidate: AuthorityTrustCandidate,
    val rotationSignature: ByteArray,
    val independentlyObservedFingerprint: String,
    val computedFingerprint: String,
    val inputBinding: String
)

internal enum class AuthorityTrustImportError {
    INVALID_KEY_ID,
    INVALID_GENERATION,
    INVALID_PUBLIC_KEY_BASE64,
    INVALID_PUBLIC_KEY,
    INVALID_ROTATION_SIGNATURE,
    INVALID_FINGERPRINT,
    FINGERPRINT_MISMATCH
}

internal sealed interface AuthorityTrustImportParseResult {
    data class Valid(val value: ParsedAuthorityTrustImport) : AuthorityTrustImportParseResult
    data class Invalid(val reason: AuthorityTrustImportError) : AuthorityTrustImportParseResult
}

/** Strict parser for manually supplied offline authority material; no file or network access. */
internal object AuthorityTrustImportParser {
    private val keyIdPattern = Regex("^[A-Za-z0-9._-]{1,64}$")
    private val generationPattern = Regex("^[1-9][0-9]{0,18}$")
    private val fingerprintPattern = Regex("^SHA256:[0-9A-F]{64}$")

    fun fingerprintPreview(
        keyId: String,
        generationText: String,
        publicKeySpkiBase64: String
    ): String? {
        val candidate = parseCandidate(keyId, generationText, publicKeySpkiBase64).first
            ?: return null
        return OwnerAuthorityTrustCeremony.fingerprintForOwner(candidate.publicKeySpkiDer)
    }

    fun parse(
        keyId: String,
        generationText: String,
        publicKeySpkiBase64: String,
        rotationSignatureBase64: String,
        independentlyObservedFingerprint: String
    ): AuthorityTrustImportParseResult {
        val parsedCandidate = parseCandidate(keyId, generationText, publicKeySpkiBase64)
        val candidate = parsedCandidate.first
            ?: return AuthorityTrustImportParseResult.Invalid(
                parsedCandidate.second ?: AuthorityTrustImportError.INVALID_PUBLIC_KEY
            )

        val signature = if (rotationSignatureBase64.isEmpty()) {
            ByteArray(0)
        } else {
            val decoded = decodeCanonical(rotationSignatureBase64, 64)
                ?: return AuthorityTrustImportParseResult.Invalid(
                    AuthorityTrustImportError.INVALID_ROTATION_SIGNATURE
                )
            if (decoded.size != 64) {
                return AuthorityTrustImportParseResult.Invalid(
                    AuthorityTrustImportError.INVALID_ROTATION_SIGNATURE
                )
            }
            decoded
        }

        if (!fingerprintPattern.matches(independentlyObservedFingerprint)) {
            return AuthorityTrustImportParseResult.Invalid(
                AuthorityTrustImportError.INVALID_FINGERPRINT
            )
        }
        val computed = OwnerAuthorityTrustCeremony.fingerprintForOwner(
            candidate.publicKeySpkiDer
        ) ?: return AuthorityTrustImportParseResult.Invalid(
            AuthorityTrustImportError.INVALID_PUBLIC_KEY
        )
        if (!MessageDigest.isEqual(
                computed.toByteArray(StandardCharsets.US_ASCII),
                independentlyObservedFingerprint.toByteArray(StandardCharsets.US_ASCII)
            )
        ) {
            return AuthorityTrustImportParseResult.Invalid(
                AuthorityTrustImportError.FINGERPRINT_MISMATCH
            )
        }

        val binding = inputBinding(
            candidate,
            signature,
            independentlyObservedFingerprint
        )
        return AuthorityTrustImportParseResult.Valid(
            ParsedAuthorityTrustImport(
                candidate.copy(publicKeySpkiDer = candidate.publicKeySpkiDer.copyOf()),
                signature.copyOf(),
                independentlyObservedFingerprint,
                computed,
                binding
            )
        )
    }

    fun confirmationBinding(
        mode: AuthorityTrustMode,
        storeSnapshot: String,
        inputBinding: String
    ): String {
        val bytes = ByteArrayOutputStream()
        DataOutputStream(bytes).use { output ->
            output.write(
                "MRNOTHING-AUTHORITY-UI-CONFIRM-V1\u0000"
                    .toByteArray(StandardCharsets.US_ASCII)
            )
            writeField(output, mode.name.toByteArray(StandardCharsets.US_ASCII))
            writeField(output, storeSnapshot.toByteArray(StandardCharsets.UTF_8))
            writeField(output, inputBinding.toByteArray(StandardCharsets.US_ASCII))
        }
        return sha256Hex(bytes.toByteArray())
    }

    fun sha256Hex(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") {
            "%02x".format(it.toInt() and 0xff)
        }

    private fun parseCandidate(
        keyId: String,
        generationText: String,
        publicKeySpkiBase64: String
    ): Pair<AuthorityTrustCandidate?, AuthorityTrustImportError?> {
        if (!keyIdPattern.matches(keyId)) {
            return Pair(null, AuthorityTrustImportError.INVALID_KEY_ID)
        }
        if (!generationPattern.matches(generationText)) {
            return Pair(null, AuthorityTrustImportError.INVALID_GENERATION)
        }
        val generation = generationText.toLongOrNull()
            ?: return Pair(null, AuthorityTrustImportError.INVALID_GENERATION)
        if (generation <= 0L) {
            return Pair(null, AuthorityTrustImportError.INVALID_GENERATION)
        }
        val spki = decodeCanonical(publicKeySpkiBase64, 128)
            ?: return Pair(null, AuthorityTrustImportError.INVALID_PUBLIC_KEY_BASE64)
        val fingerprint = OwnerAuthorityTrustCeremony.fingerprintForOwner(spki)
            ?: return Pair(null, AuthorityTrustImportError.INVALID_PUBLIC_KEY)
        if (fingerprint.isEmpty()) {
            return Pair(null, AuthorityTrustImportError.INVALID_PUBLIC_KEY)
        }
        return Pair(
            AuthorityTrustCandidate(keyId, generation, spki),
            null
        )
    }

    private fun decodeCanonical(value: String, maximumBytes: Int): ByteArray? {
        if (value.isEmpty() || value.length > 512 || value.any { it.isWhitespace() }) {
            return null
        }
        return try {
            val decoded = Base64.getDecoder().decode(value)
            if (decoded.isEmpty() || decoded.size > maximumBytes ||
                Base64.getEncoder().encodeToString(decoded) != value
            ) null else decoded
        } catch (_: IllegalArgumentException) {
            null
        } catch (_: RuntimeException) {
            null
        }
    }

    private fun inputBinding(
        candidate: AuthorityTrustCandidate,
        signature: ByteArray,
        fingerprint: String
    ): String {
        val bytes = ByteArrayOutputStream()
        DataOutputStream(bytes).use { output ->
            output.write(
                "MRNOTHING-AUTHORITY-IMPORT-V1\u0000"
                    .toByteArray(StandardCharsets.US_ASCII)
            )
            output.writeLong(candidate.generation)
            writeField(output, candidate.keyId.toByteArray(StandardCharsets.US_ASCII))
            writeField(output, candidate.publicKeySpkiDer)
            writeField(output, signature)
            writeField(output, fingerprint.toByteArray(StandardCharsets.US_ASCII))
        }
        return sha256Hex(bytes.toByteArray())
    }

    private fun writeField(output: DataOutputStream, value: ByteArray) {
        output.writeInt(value.size)
        output.write(value)
    }
}
