package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

class AgentPolicyTest {
    @Test fun unauthenticatedIsDenied() {
        assertEquals(Verdict.DENY, AgentPolicy.decide(AgentAction("open_app", false)))
    }
    @Test fun unknownActionIsDenied() {
        assertEquals(Verdict.DENY, AgentPolicy.decide(AgentAction("root_shell", true)))
    }
    @Test fun safeReadIsAllowed() {
        assertEquals(Verdict.ALLOW, AgentPolicy.decide(AgentAction("get_battery", true)))
    }
    @Test fun unknownRecipientNeedsApproval() {
        assertEquals(Verdict.APPROVAL_REQUIRED, AgentPolicy.decide(AgentAction("place_call", true)))
    }
    @Test fun allowlistedRecipientIsAllowed() {
        assertEquals(Verdict.ALLOW, AgentPolicy.decide(AgentAction("place_call", true, true)))
    }
    @Test fun screenActionsRequireApprovalEvenWhenAuthenticated() {
        for (action in listOf("read_screen", "navigate", "scroll")) {
            assertEquals(Verdict.APPROVAL_REQUIRED, AgentPolicy.decide(AgentAction(action, true)))
        }
    }
    @Test fun screenActionsDenyUnauthenticated() {
        for (action in listOf("read_screen", "navigate", "scroll")) {
            assertEquals(Verdict.DENY, AgentPolicy.decide(AgentAction(action, false)))
        }
    }
    @Test fun contactApprovalDoesNotGrantScreenAccess() {
        for (action in listOf("read_screen", "navigate", "scroll")) {
            assertEquals(Verdict.APPROVAL_REQUIRED, AgentPolicy.decide(AgentAction(action, true, true)))
        }
    }
    @Test fun paymentNeedsApproval() {
        assertEquals(Verdict.APPROVAL_REQUIRED, AgentPolicy.decide(AgentAction("transfer_money", true)))
    }
}
