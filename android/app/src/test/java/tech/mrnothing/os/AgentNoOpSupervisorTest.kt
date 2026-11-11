package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class AgentNoOpSupervisorTest {
    @Test fun lowRiskSampleIsNeverAuthorized() {
        val rehearsal = AgentPlanRehearsal { 100L }
        rehearsal.begin(listOf("get_battery", "open_app"))
        val decision = AgentNoOpSupervisor.inspect(rehearsal.previewNext())
        assertEquals(NoOpSupervisorVerdict.BLOCKED_NO_VERIFIED_SESSION, decision.verdict)
        assertFalse(decision.authorized)
        assertFalse(decision.deviceActionsExecuted)
    }

    @Test fun sensitiveSampleAcknowledgementIsNotOwnerConsent() {
        val rehearsal = AgentPlanRehearsal { 100L }
        rehearsal.begin(listOf("send_message", "get_battery"))
        rehearsal.acknowledgeSampleReview()
        val decision = AgentNoOpSupervisor.inspect(rehearsal.previewNext())
        assertEquals(NoOpSupervisorVerdict.BLOCKED_NO_VERIFIED_SESSION, decision.verdict)
        assertFalse(decision.authorized)
    }

    @Test fun idleAndReviewRequiredStatesHaveNoActiveStep() {
        val rehearsal = AgentPlanRehearsal { 100L }
        assertEquals(NoOpSupervisorVerdict.BLOCKED_NO_ACTIVE_STEP,
            AgentNoOpSupervisor.inspect(rehearsal.snapshot()).verdict)
        assertEquals(NoOpSupervisorVerdict.BLOCKED_NO_ACTIVE_STEP,
            AgentNoOpSupervisor.inspect(rehearsal.begin(listOf("send_message"))).verdict)
    }

    @Test fun cancellationTimeoutAndRefusalAreTerminal() {
        val rehearsal = AgentPlanRehearsal { 100L }
        rehearsal.begin(listOf("get_battery"))
        assertEquals(NoOpSupervisorVerdict.BLOCKED_TERMINAL_REHEARSAL,
            AgentNoOpSupervisor.inspect(rehearsal.cancel()).verdict)
        assertEquals(NoOpSupervisorVerdict.BLOCKED_TERMINAL_REHEARSAL,
            AgentNoOpSupervisor.inspect(
                RehearsalSnapshot(RehearsalPhase.TIMED_OUT, null, 0, 0, "expired")
            ).verdict)
        assertEquals(NoOpSupervisorVerdict.BLOCKED_TERMINAL_REHEARSAL,
            AgentNoOpSupervisor.inspect(
                RehearsalSnapshot(RehearsalPhase.REFUSED, null, 0, 0, "refused")
            ).verdict)
    }

    @Test fun forgedCompletedSnapshotCannotAuthorize() {
        val forged = RehearsalSnapshot(
            RehearsalPhase.COMPLETE, "open_app", 1, 1, "caller supplied"
        )
        val decision = AgentNoOpSupervisor.inspect(forged)
        assertEquals(NoOpSupervisorVerdict.BLOCKED_TERMINAL_REHEARSAL, decision.verdict)
        assertFalse(decision.copy(verdict = NoOpSupervisorVerdict.BLOCKED_NO_ACTIVE_STEP).authorized)
        assertFalse(decision.copy(explanation = "allowed").deviceActionsExecuted)
    }

    @Test fun completedRealPlanIsTerminalEvenWithDisplayedStep() {
        val rehearsal = AgentPlanRehearsal { 100L }
        rehearsal.begin(listOf("get_battery"))
        val completed = rehearsal.previewNext()
        assertEquals(RehearsalPhase.COMPLETE, completed.phase)
        assertEquals("get_battery", completed.displayedStep)
        val decision = AgentNoOpSupervisor.inspect(completed)
        assertEquals(NoOpSupervisorVerdict.BLOCKED_TERMINAL_REHEARSAL, decision.verdict)
        assertFalse(decision.authorized)
        assertFalse(decision.deviceActionsExecuted)
    }

    @Test fun unsupportedForgedStepIsBlocked() {
        val forged = RehearsalSnapshot(
            RehearsalPhase.PREVIEWING, "root_shell", 1, 2, "caller supplied"
        )
        assertEquals(NoOpSupervisorVerdict.BLOCKED_UNSUPPORTED_STEP,
            AgentNoOpSupervisor.inspect(forged).verdict)
    }
}
