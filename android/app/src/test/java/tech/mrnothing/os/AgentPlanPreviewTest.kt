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
}
