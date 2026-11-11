package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AgentPlanPreviewTest {
    @Test fun lowRiskClassificationNeverAuthorizes() {
        for (action in listOf("get_battery", "open_app")) {
            val result = AgentPlanPreview.inspect(action)
            assertEquals(ActionRisk.LOW_RISK, result.risk)
            assertFalse(result.authorized)
            assertFalse(result.deviceActionsExecuted)
        }
    }

    @Test fun sensitiveActionsRequireOwnerApprovalButRemainDisabled() {
        for (action in listOf("send_message", "place_call", "read_screen", "navigate",
                              "purchase", "transfer_money", "delete_data")) {
            val result = AgentPlanPreview.inspect(action)
            assertEquals(ActionRisk.OWNER_APPROVAL_REQUIRED, result.risk)
            assertTrue(result.description.contains("Explicit owner approval"))
            assertFalse(result.authorized)
            assertFalse(result.deviceActionsExecuted)
        }
    }

    @Test fun unknownAndEmptyActionsDeny() {
        for (action in listOf("root_shell", "", "unlisted_action")) {
            val result = AgentPlanPreview.inspect(action)
            assertEquals(ActionRisk.DENY, result.risk)
            assertFalse(result.authorized)
            assertFalse(result.deviceActionsExecuted)
        }
    }

    @Test fun riskClassificationIsNotAnExecutor() {
        val result = AgentPlanPreview.inspect("get_battery")
        assertTrue(result.description.contains("independent authorization"))
        assertFalse(result.deviceActionsExecuted)
    }

    @Test fun boundedWholePlanRejectsEmptyAndOversizedInput() {
        for (actions in listOf(emptyList(), List(21) { "get_battery" },
                               listOf("x".repeat(65)))) {
            val plan = AgentPlanPreviewPlan.inspect(actions)
            assertEquals(ActionRisk.DENY, plan.risk)
            assertTrue(plan.steps.isEmpty())
            assertFalse(plan.authorized)
            assertFalse(plan.deviceActionsExecuted)
        }
    }

    @Test fun unknownStepRejectsEntirePlan() {
        val plan = AgentPlanPreviewPlan.inspect(
            listOf("get_battery", "root_shell", "send_message")
        )
        assertEquals(ActionRisk.DENY, plan.risk)
        assertEquals(3, plan.steps.size)
        assertTrue(plan.description.contains("Entire sample plan refused"))
        assertFalse(plan.authorized)
        assertFalse(plan.deviceActionsExecuted)
    }

    @Test fun sensitiveStepEscalatesWholePlanWithoutGrantingPermission() {
        val plan = AgentPlanPreviewPlan.inspect(
            listOf("get_battery", "open_app", "send_message")
        )
        assertEquals(ActionRisk.OWNER_APPROVAL_REQUIRED, plan.risk)
        assertEquals(3, plan.steps.size)
        assertFalse(plan.authorized)
        assertFalse(plan.deviceActionsExecuted)
    }

    @Test fun lowRiskPlanNeverBecomesAuthorized() {
        val plan = AgentPlanPreviewPlan.inspect(List(20) { "get_battery" })
        assertEquals(ActionRisk.LOW_RISK, plan.risk)
        assertEquals(20, plan.steps.size)
        assertFalse(plan.authorized)
        assertFalse(plan.deviceActionsExecuted)
    }

    @Test fun previewSnapshotDoesNotFollowCallerMutations() {
        val input = mutableListOf("get_battery")
        val plan = AgentPlanPreviewPlan.inspect(input)
        input[0] = "root_shell"
        assertEquals("get_battery", plan.steps.single().action)
        assertEquals(ActionRisk.LOW_RISK, plan.risk)
        assertFalse(plan.authorized)
        try {
            (plan.steps as MutableList<AgentPlanPreviewDecision>).clear()
            org.junit.Assert.fail("Plan snapshot must be immutable")
        } catch (_: UnsupportedOperationException) {
            assertEquals(1, plan.steps.size)
        }
    }
}
