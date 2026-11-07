package tech.mrnothing.os

/**
 * AGENT-004A: cross-platform P-256 owner-consent canonicalization.
 *
 * Version 1 signs action/session metadata only and is kept for the bounded
 * read_screen/empty-arguments path. Version 2 additionally binds a strict,
 * typed action-argument digest; the exact canonical JSON is shown by the
 * system-authenticated signer before it emits a signature.
 */
internal data class OwnerConsentFields(
    val version: Int,
    val deviceId: String,
    val ownerId: String,
    val sessionId: String,
    val action: String,
    val nonce: String,
    val issuedAtEpochMs: Long,
    val expiresAtEpochMs: Long,
    val arguments: OwnerActionArguments? = null,
    val argumentsSha256: String? = null
)

internal object OwnerConsentCanonicalizer {
    private val identifier = Regex("^[A-Za-z0-9._-]{1,128}$")
    private val actions = setOf("read_screen", "navigate", "scroll")
    private val sha256 = Regex("^[0-9a-f]{64}$")
    private const val MAX_TTL_MS = 30_000L

    private fun validIdentifier(value: String, minimum: Int = 1): Boolean =
        value.length in minimum..128 && identifier.matches(value)

    /** Returns exact sorted-key canonical JSON, or null when any field is invalid. */
    fun canonicalPayload(fields: OwnerConsentFields): String? {
        if (!validIdentifier(fields.deviceId) ||
            !validIdentifier(fields.ownerId) ||
            !validIdentifier(fields.sessionId) ||
            !validIdentifier(fields.nonce, minimum = 32) ||
            fields.action !in actions ||
            fields.issuedAtEpochMs < 0L ||
            fields.expiresAtEpochMs <= fields.issuedAtEpochMs ||
            fields.expiresAtEpochMs - fields.issuedAtEpochMs !in 1L..MAX_TTL_MS
        ) return null

        val argumentsDigest = when (fields.version) {
            1 -> {
                if (fields.arguments != null || fields.argumentsSha256 != null) return null
                null
            }
            2 -> {
                val computed = OwnerActionArgumentsCanonicalizer.sha256(
                    fields.action, fields.arguments
                ) ?: return null
                if (fields.argumentsSha256 == null ||
                    !sha256.matches(fields.argumentsSha256) ||
                    fields.argumentsSha256 != computed
                ) return null
                computed
            }
            else -> return null
        }

        return buildString {
            append("{\"action\":\"").append(fields.action).append('"')
            if (fields.version == 2) {
                append(",\"arguments_sha256\":\"").append(argumentsDigest).append('"')
            }
            append(",\"device_id\":\"").append(fields.deviceId)
            append("\",\"expires_at_epoch_ms\":").append(fields.expiresAtEpochMs)
            append(",\"issued_at_epoch_ms\":").append(fields.issuedAtEpochMs)
            append(",\"nonce\":\"").append(fields.nonce)
            append("\",\"owner_id\":\"").append(fields.ownerId)
            append("\",\"session_id\":\"").append(fields.sessionId)
            append("\",\"version\":").append(fields.version)
            append("}")
        }
    }
}
