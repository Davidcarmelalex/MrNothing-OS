package tech.mrnothing.os

/**
 * A display-only inspection of a fixed example action.
 *
 * Neither risk classification nor this preview is authentication, owner
 * consent, Android permission, a tool capability, or execution.
 */
internal data class AgentPlanPreviewDecision(
    val action: String,
    val risk: ActionRisk,
    val description: String,
    val authorized: Boolean = false,
    val deviceActionsExecuted: Boolean = false
)

internal object AgentPlanPreview {
    fun inspect(action: String): AgentPlanPreviewDecision {
        val risk = AgentPolicy.classify(AgentAction(action))
        val description = when (risk) {
            ActionRisk.LOW_RISK ->
                "Low-risk classification only. An authenticated session and independent " +
                    "authorization would still be required."
            ActionRisk.OWNER_APPROVAL_REQUIRED ->
                "Sensitive action. Explicit owner approval and independent " +
                    "authorization would be required."
            ActionRisk.DENY ->
                "Unknown or unsupported action. Refused."
        }
        return AgentPlanPreviewDecision(action, risk, description)
    }
}
