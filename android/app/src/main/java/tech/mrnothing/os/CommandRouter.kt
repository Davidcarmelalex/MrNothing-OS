package tech.mrnothing.os

/**
 * Untrusted request data. It is deliberately not named "TrustedCommand":
 * action text and package names are not evidence of owner identity or consent.
 */
data class UntrustedCommandRequest(
    val action: String,
    val packageName: String? = null
)

sealed class CommandResult {
    data class Rejected(val reason: String) : CommandResult()
}

/**
 * M3 fail-closed dispatch boundary.
 *
 * The previous caller-supplied transport-authentication flag was not proof
 * of identity. No verifier-created Android session capability is integrated
 * yet, so this router refuses every request and performs no device action.
 */
class CommandRouter {
    fun execute(request: UntrustedCommandRequest): CommandResult {
        if (request.action.isBlank() || request.action.length > 128) {
            return CommandResult.Rejected("INVALID_ACTION")
        }
        return CommandResult.Rejected("VERIFIED_TRANSPORT_SESSION_REQUIRED")
    }
}
