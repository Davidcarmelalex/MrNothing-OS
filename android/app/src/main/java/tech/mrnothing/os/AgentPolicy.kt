package tech.mrnothing.os

/**
 * Classifies action risk only. This policy does not authenticate a caller,
 * establish owner consent, check Android permissions, or authorize execution.
 */
enum class ActionRisk { LOW_RISK, OWNER_APPROVAL_REQUIRED, DENY }

data class AgentAction(val name: String)

object AgentPolicy {
    private val lowRisk = setOf("open_app", "get_battery")
    private val screenActions = setOf("read_screen", "navigate", "scroll")
    private val communications = setOf("place_call", "send_message")
    private val sensitive = setOf("purchase", "transfer_money", "delete_data", "change_security")

    fun classify(action: AgentAction): ActionRisk = when {
        action.name in lowRisk -> ActionRisk.LOW_RISK
        action.name in screenActions -> ActionRisk.OWNER_APPROVAL_REQUIRED
        action.name in communications -> ActionRisk.OWNER_APPROVAL_REQUIRED
        action.name in sensitive -> ActionRisk.OWNER_APPROVAL_REQUIRED
        else -> ActionRisk.DENY
    }
}
