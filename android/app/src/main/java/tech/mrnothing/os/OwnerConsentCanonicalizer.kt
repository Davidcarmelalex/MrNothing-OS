package tech.mrnothing.os

/**
 * AGENT-004A: canonical P-256 owner-consent payload encoding shared with Python.
 *
 * This class only serializes a host-issued challenge. It does not sign, issue
 * consent, grant Android permissions, or execute actions. Values are restricted
 * to a small ASCII identifier alphabet so JSON escaping is unambiguous.
 */
internal data class OwnerConsentFields(
    val version: Int,
    val deviceId: String,
    val ownerId: String,
    val sessionId: String,
    val action: String,
    val nonce: String,
    val issuedAtEpochMs: Long,
    val expiresAtEpochMs: Long
)

internal object OwnerConsentCanonicalizer {
    private val identifier = Regex("^[A-Za-z0-9._-]{1,128}$")
    private val actions = setOf("read_screen", "navigate", "scroll")
    private const val MAX_TTL_MS = 30_000L

    private fun validIdentifier(value: String, minimum: Int = 1): Boolean =
        value.length in minimum..128 && identifier.matches(value)

    /**
     * Returns the exact canonical JSON string or null when invalid.
     * Keys are lexicographically ordered to match Python json.dumps(sort_keys=True).
     */
    fun canonicalPayload(fields: OwnerConsentFields): String? {
        if (fields.version != 1 ||
            !validIdentifier(fields.deviceId) ||
            !validIdentifier(fields.ownerId) ||
            !validIdentifier(fields.sessionId) ||
            !validIdentifier(fields.nonce, minimum = 32) ||
            fields.action !in actions ||
            fields.issuedAtEpochMs < 0L ||
            fields.expiresAtEpochMs <= fields.issuedAtEpochMs ||
            fields.expiresAtEpochMs - fields.issuedAtEpochMs !in 1L..MAX_TTL_MS
        ) return null

        return buildString {
            append("{\"action\":\"").append(fields.action)
            append("\",\"device_id\":\"").append(fields.deviceId)
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
