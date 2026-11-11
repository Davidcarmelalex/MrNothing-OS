package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Test

class AgentPlanRehearsalTest {
    @Test fun sensitiveSampleNeedsInstructionAcknowledgementAndNeverAuthorizes() {
        var now = 100L
        val rehearsal = AgentPlanRehearsal { now }
        val first = rehearsal.begin(listOf("get_battery", "send_message"))
        assertEquals(RehearsalPhase.REVIEW_REQUIRED, first.phase)
        assertEquals(RehearsalPhase.REVIEW_REQUIRED, rehearsal.previewNext().phase)
        assertEquals(0, rehearsal.snapshot().reviewedSteps)
        assertEquals(RehearsalPhase.READY, rehearsal.acknowledgeSampleReview().phase)
        val step = rehearsal.previewNext()
        assertEquals(RehearsalPhase.PREVIEWING, step.phase)
        assertEquals("get_battery", step.displayedStep)
        assertFalse(step.authorized)
        assertFalse(step.deviceActionsExecuted)
        now++
        val complete = rehearsal.previewNext()
        assertEquals(RehearsalPhase.COMPLETE, complete.phase)
        assertEquals("send_message", complete.displayedStep)
        assertFalse(complete.authorized)
        assertFalse(complete.deviceActionsExecuted)
        assertEquals(RehearsalPhase.COMPLETE, rehearsal.previewNext().phase)
    }

    @Test fun lowRiskSampleRequiresNoSimulatedAcknowledgementButCannotExecute() {
        val rehearsal = AgentPlanRehearsal { 0L }
        assertEquals(RehearsalPhase.READY, rehearsal.begin(listOf("get_battery")).phase)
        val result = rehearsal.previewNext()
        assertEquals(RehearsalPhase.COMPLETE, result.phase)
        assertFalse(result.authorized)
        assertFalse(result.deviceActionsExecuted)
    }

    @Test fun deniedPlanNeverProgresses() {
        val rehearsal = AgentPlanRehearsal { 100L }
        assertEquals(RehearsalPhase.REFUSED,
            rehearsal.begin(listOf("get_battery", "root_shell")).phase)
        assertEquals(RehearsalPhase.REFUSED, rehearsal.acknowledgeSampleReview().phase)
        assertEquals(RehearsalPhase.REFUSED, rehearsal.previewNext().phase)
    }

    @Test fun cancellationClearsAndCannotResumeStalePlan() {
        val rehearsal = AgentPlanRehearsal { 10L }
        rehearsal.begin(listOf("get_battery"))
        val cleared = rehearsal.cancel()
        assertEquals(RehearsalPhase.CANCELLED, cleared.phase)
        assertNull(cleared.displayedStep)
        assertEquals(0, cleared.totalSteps)
        assertEquals(RehearsalPhase.CANCELLED, rehearsal.previewNext().phase)
    }

    @Test fun timeoutAndClockRollbackFailClosed() {
        var now = 100L
        val rehearsal = AgentPlanRehearsal { now }
        rehearsal.begin(listOf("get_battery"))
        now += 30_001L
        assertEquals(RehearsalPhase.TIMED_OUT, rehearsal.previewNext().phase)
        now = 500L
        rehearsal.begin(listOf("get_battery"))
        now = 499L
        assertEquals(RehearsalPhase.TIMED_OUT, rehearsal.snapshot().phase)
    }

    @Test fun staleActiveBeginRequiresSeparateRestartAndClearsPriorPlan() {
        var now = 100L
        val rehearsal = AgentPlanRehearsal { now }
        rehearsal.begin(listOf("get_battery", "open_app"))
        now += 30_001L
        val expired = rehearsal.begin(listOf("send_message"))
        assertEquals(RehearsalPhase.TIMED_OUT, expired.phase)
        assertNull(expired.displayedStep)
        assertEquals(0, expired.totalSteps)
        assertEquals(0, expired.reviewedSteps)
        assertEquals(RehearsalPhase.TIMED_OUT, rehearsal.previewNext().phase)
        val restarted = rehearsal.begin(listOf("get_battery"))
        assertEquals(RehearsalPhase.READY, restarted.phase)
        assertEquals(1, restarted.totalSteps)
    }

    @Test fun clockFailureDuringActiveBeginCannotKeepStalePlan() {
        var clockFails = false
        val rehearsal = AgentPlanRehearsal {
            if (clockFails) throw IllegalStateException("clock unavailable")
            100L
        }
        rehearsal.begin(listOf("get_battery", "open_app"))
        clockFails = true
        val expired = rehearsal.begin(listOf("send_message"))
        assertEquals(RehearsalPhase.TIMED_OUT, expired.phase)
        assertNull(expired.displayedStep)
        assertEquals(0, expired.totalSteps)
        assertFalse(expired.authorized)
        clockFails = false
        assertEquals(RehearsalPhase.READY, rehearsal.begin(listOf("get_battery")).phase)
    }

    @Test fun clockExceptionAndNegativeTimeRefuse() {
        val bad = AgentPlanRehearsal { throw IllegalStateException("clock") }
        assertEquals(RehearsalPhase.REFUSED, bad.begin(listOf("get_battery")).phase)
        val negative = AgentPlanRehearsal { -1L }
        assertEquals(RehearsalPhase.REFUSED, negative.begin(listOf("get_battery")).phase)
    }

    @Test fun callerMutationAndActiveReplacementCannotChangePlan() {
        val actions = mutableListOf("get_battery", "open_app")
        val rehearsal = AgentPlanRehearsal { 100L }
        rehearsal.begin(actions)
        actions[0] = "root_shell"
        assertEquals(RehearsalPhase.READY, rehearsal.begin(listOf("send_message")).phase)
        assertEquals("get_battery", rehearsal.previewNext().displayedStep)
    }

    @Test fun snapshotsCannotBeCopiedIntoAuthorization() {
        val rehearsal = AgentPlanRehearsal { 0L }
        val original = rehearsal.begin(listOf("get_battery"))
        val copy = original.copy(phase = RehearsalPhase.COMPLETE)
        assertFalse(copy.authorized)
        assertFalse(copy.deviceActionsExecuted)
    }
}
