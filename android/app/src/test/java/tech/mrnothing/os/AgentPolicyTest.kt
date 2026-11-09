package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

class AgentPolicyTest {
    @Test fun lowRiskActionsAreClassifiedButNotAuthorizedForExecution() {
        assertEquals(ActionRisk.LOW_RISK, AgentPolicy.classify(AgentAction("open_app")))
        assertEquals(ActionRisk.LOW_RISK, AgentPolicy.classify(AgentAction("get_battery")))
    }

    @Test fun unknownActionIsDenied() {
        assertEquals(ActionRisk.DENY, AgentPolicy.classify(AgentAction("root_shell")))
    }

    @Test fun screenActionsAlwaysRequireOwnerApproval() {
        for (action in listOf("read_screen", "navigate", "scroll")) {
            assertEquals(
                ActionRisk.OWNER_APPROVAL_REQUIRED,
                AgentPolicy.classify(AgentAction(action))
            )
        }
    }

    @Test fun communicationsAlwaysRequireOwnerApprovalUntilTrustedContactPolicyExists() {
        for (action in listOf("place_call", "send_message")) {
            assertEquals(
                ActionRisk.OWNER_APPROVAL_REQUIRED,
                AgentPolicy.classify(AgentAction(action))
            )
        }
    }

    @Test fun sensitiveActionsRequireOwnerApproval() {
        for (action in listOf("purchase", "transfer_money", "delete_data", "change_security")) {
            assertEquals(
                ActionRisk.OWNER_APPROVAL_REQUIRED,
                AgentPolicy.classify(AgentAction(action))
            )
        }
    }
}
