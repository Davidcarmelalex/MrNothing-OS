package tech.mrnothing.os

/**
 * Offline, owner-visible rehearsal of a *sample* plan. Not a command executor,
 * transport verifier, consent ceremony, permission grant, or authorization token.
 * No Android APIs or device interfaces are reachable from this class.
 */
internal enum class RehearsalPhase {
    IDLE, REVIEW_REQUIRED, READY, PREVIEWING, COMPLETE, REFUSED, CANCELLED, TIMED_OUT
}

internal data class RehearsalSnapshot(
    val phase: RehearsalPhase,
    val displayedStep: String?,
    val reviewedSteps: Int,
    val totalSteps: Int,
    val explanation: String
) {
    // Computed invariants, deliberately excluded from data-class copy parameters.
    val authorized: Boolean get() = false
    val deviceActionsExecuted: Boolean get() = false
}

internal class AgentPlanRehearsal(private val elapsedRealtimeMillis: () -> Long) {
    private companion object {
        const val MAX_DURATION_MS = 30_000L
    }

    private var plan: AgentPlanPreviewSummary? = null
    private var startedAt = 0L
    private var reviewedSteps = 0
    private var displayedStep: String? = null
    private var phase = RehearsalPhase.IDLE

    /** Refuses to replace an active rehearsal; caller input is snapshotted. */
    fun begin(sampleActions: List<String>): RehearsalSnapshot {
        if (phase in setOf(RehearsalPhase.REVIEW_REQUIRED, RehearsalPhase.READY,
                           RehearsalPhase.PREVIEWING)) return snapshot()
        val now = readClock() ?: return refuse("Monotonic clock unavailable.")
        val candidate = AgentPlanPreviewPlan.inspect(sampleActions)
        if (candidate.risk == ActionRisk.DENY || candidate.steps.isEmpty()) {
            return refuse("Sample plan refused by offline policy.")
        }
        plan = candidate
        startedAt = now
        reviewedSteps = 0
        displayedStep = null
        phase = if (candidate.risk == ActionRisk.OWNER_APPROVAL_REQUIRED)
            RehearsalPhase.REVIEW_REQUIRED else RehearsalPhase.READY
        return snapshotWithoutClock()
    }

    /** Acknowledges *simulation instructions*, never real owner consent. */
    fun acknowledgeSampleReview(): RehearsalSnapshot {
        if (expireIfNeeded()) return snapshotWithoutClock()
        if (phase == RehearsalPhase.REVIEW_REQUIRED) phase = RehearsalPhase.READY
        return snapshotWithoutClock()
    }

    /** Advances a display-only cursor; no action is dispatched or invoked. */
    fun previewNext(): RehearsalSnapshot {
        if (expireIfNeeded()) return snapshotWithoutClock()
        if (phase !in setOf(RehearsalPhase.READY, RehearsalPhase.PREVIEWING))
            return snapshotWithoutClock()
        val current = plan ?: return refuse("Sample plan missing.")
        if (reviewedSteps >= current.steps.size) return refuse("Invalid rehearsal cursor.")
        displayedStep = current.steps[reviewedSteps].action
        reviewedSteps++
        phase = if (reviewedSteps == current.steps.size) RehearsalPhase.COMPLETE
            else RehearsalPhase.PREVIEWING
        return snapshotWithoutClock()
    }

    /** Cancellation clears the plan and cursor, including any displayed action. */
    fun cancel(): RehearsalSnapshot {
        clearInternal()
        phase = RehearsalPhase.CANCELLED
        return snapshotWithoutClock()
    }

    fun snapshot(): RehearsalSnapshot {
        expireIfNeeded()
        return snapshotWithoutClock()
    }

    private fun readClock(): Long? = try {
        elapsedRealtimeMillis().takeIf { it >= 0 }
    } catch (_: Exception) {
        null
    }

    private fun expireIfNeeded(): Boolean {
        if (phase !in setOf(RehearsalPhase.REVIEW_REQUIRED, RehearsalPhase.READY,
                           RehearsalPhase.PREVIEWING)) return false
        val now = readClock()
        if (now == null || now < startedAt || now - startedAt > MAX_DURATION_MS) {
            clearInternal()
            phase = RehearsalPhase.TIMED_OUT
            return true
        }
        return false
    }

    private fun clearInternal() {
        plan = null
        startedAt = 0L
        reviewedSteps = 0
        displayedStep = null
    }

    private fun refuse(reason: String): RehearsalSnapshot {
        clearInternal()
        phase = RehearsalPhase.REFUSED
        return snapshotWithoutClock(reason)
    }

    private fun snapshotWithoutClock(reason: String? = null): RehearsalSnapshot = RehearsalSnapshot(
        phase, displayedStep, reviewedSteps, plan?.steps?.size ?: 0,
        reason ?: when (phase) {
            RehearsalPhase.IDLE -> "Select a fixed sample to rehearse."
            RehearsalPhase.REVIEW_REQUIRED -> "Sensitive sample: acknowledge the simulation instructions, not consent."
            RehearsalPhase.READY -> "Ready to preview sample steps without execution."
            RehearsalPhase.PREVIEWING -> "Sample step displayed; continue or cancel."
            RehearsalPhase.COMPLETE -> "Sample rehearsal complete. No device action occurred."
            RehearsalPhase.REFUSED -> "Sample refused."
            RehearsalPhase.CANCELLED -> "Rehearsal cancelled and cleared."
            RehearsalPhase.TIMED_OUT -> "Rehearsal expired and cleared."
        }
    )
}
