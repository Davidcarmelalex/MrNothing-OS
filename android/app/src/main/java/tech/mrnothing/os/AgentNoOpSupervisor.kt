package tech.mrnothing.os

/**
 * Display-only admission boundary for the offline launcher rehearsal.
 *
 * This deliberately has no verified transport, enrolled identity, owner
 * consent, Android permission check, reservation, or execution capability.
 * It MUST NOT be reused as an execution-authorizing supervisor.
 */
internal enum class NoOpSupervisorVerdict {
    BLOCKED_NO_ACTIVE_STEP,
    BLOCKED_TERMINAL_REHEARSAL,
    BLOCKED_UNSUPPORTED_STEP,
    BLOCKED_NO_VERIFIED_SESSION
}

internal data class NoOpSupervisorDecision(
    val verdict: NoOpSupervisorVerdict,
    val explanation: String
) {
    // Neither data-class copy() nor caller-controlled snapshots can grant authority.
    val authorized: Boolean get() = false
    val deviceActionsExecuted: Boolean get() = false
}

internal object AgentNoOpSupervisor {
    fun inspect(snapshot: RehearsalSnapshot): NoOpSupervisorDecision {
        if (snapshot.phase in setOf(
                RehearsalPhase.COMPLETE, RehearsalPhase.CANCELLED,
                RehearsalPhase.TIMED_OUT, RehearsalPhase.REFUSED
            )
        ) {
            return NoOpSupervisorDecision(
                NoOpSupervisorVerdict.BLOCKED_TERMINAL_REHEARSAL,
                "Completed, cancelled, expired or refused rehearsal; nothing may execute."
            )
        }
        if (snapshot.phase != RehearsalPhase.PREVIEWING ||
            snapshot.displayedStep == null
        ) {
            return NoOpSupervisorDecision(
                NoOpSupervisorVerdict.BLOCKED_NO_ACTIVE_STEP,
                "No active sample step; this preview cannot authorize execution."
            )
        }
        if (AgentPolicy.classify(AgentAction(snapshot.displayedStep)) == ActionRisk.DENY) {
            return NoOpSupervisorDecision(
                NoOpSupervisorVerdict.BLOCKED_UNSUPPORTED_STEP,
                "Unsupported sample step; execution is forbidden."
            )
        }
        return NoOpSupervisorDecision(
            NoOpSupervisorVerdict.BLOCKED_NO_VERIFIED_SESSION,
            "Risk classification and simulation acknowledgement are not authenticated " +
                "transport, owner consent or Android permission. No executor is connected."
        )
    }
}
