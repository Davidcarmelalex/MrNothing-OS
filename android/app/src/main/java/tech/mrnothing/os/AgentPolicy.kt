package tech.mrnothing.os

enum class Verdict { ALLOW, APPROVAL_REQUIRED, DENY }
data class AgentAction(val name: String, val authenticated: Boolean, val contactApproved: Boolean = false)

object AgentPolicy {
    private val lowRisk = setOf("open_app", "get_battery", "read_screen", "navigate", "scroll")
    private val communications = setOf("place_call", "send_message")
    private val sensitive = setOf("purchase", "transfer_money", "delete_data", "change_security")

    fun decide(action: AgentAction): Verdict = when {
        !action.authenticated -> Verdict.DENY
        action.name in lowRisk -> Verdict.ALLOW
        action.name in communications -> if (action.contactApproved) Verdict.ALLOW else Verdict.APPROVAL_REQUIRED
        action.name in sensitive -> Verdict.APPROVAL_REQUIRED
        else -> Verdict.DENY
    }
}
