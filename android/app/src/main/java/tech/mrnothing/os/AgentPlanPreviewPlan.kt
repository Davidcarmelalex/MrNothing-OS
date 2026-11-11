package tech.mrnothing.os

import java.util.Collections

/**
 * A bounded, offline *display-only* plan classification. No result can be
 * used as an execution grant, even when every step is classified low risk.
 * The full plan is refused if any step is unknown or malformed.
 */
internal data class AgentPlanPreviewSummary(
    val steps: List<AgentPlanPreviewDecision>,
    val risk: ActionRisk,
    val description: String
) {
    val authorized: Boolean get() = false
    val deviceActionsExecuted: Boolean get() = false
}

internal object AgentPlanPreviewPlan {
    private const val MAX_STEPS = 20
    private const val MAX_ACTION_LENGTH = 64

    fun inspect(actions: List<String>): AgentPlanPreviewSummary {
        if (actions.isEmpty() || actions.size > MAX_STEPS ||
            actions.any { it.length > MAX_ACTION_LENGTH }
        ) {
            return AgentPlanPreviewSummary(
                emptyList(), ActionRisk.DENY,
                "Plan refused: invalid step count or action length."
            )
        }
        // Materialize a snapshot: changing the caller's list later cannot
        // alter the displayed classification.
        val steps = Collections.unmodifiableList(actions.map { AgentPlanPreview.inspect(it) })
        val risk = when {
            steps.any { it.risk == ActionRisk.DENY } -> ActionRisk.DENY
            steps.any { it.risk == ActionRisk.OWNER_APPROVAL_REQUIRED } ->
                ActionRisk.OWNER_APPROVAL_REQUIRED
            else -> ActionRisk.LOW_RISK
        }
        val description = when (risk) {
            ActionRisk.DENY -> "Entire sample plan refused: unsupported step."
            ActionRisk.OWNER_APPROVAL_REQUIRED ->
                "Sensitive sample plan: owner approval and independent authorization would be required."
            ActionRisk.LOW_RISK ->
                "Low-risk sample plan only: independent authorization would still be required."
        }
        return AgentPlanPreviewSummary(steps, risk, description)
    }
}
