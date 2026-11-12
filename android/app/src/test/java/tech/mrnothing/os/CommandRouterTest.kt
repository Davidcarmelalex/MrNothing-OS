package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

class CommandRouterTest {
    private val router = CommandRouter()

    @Test fun lowRiskActionsAreRejectedUntilVerifiedSessionIntegrationExists() {
        val requests = listOf(
            UntrustedCommandRequest("get_battery"),
            UntrustedCommandRequest("open_app", "com.example.reader")
        )
        for (request in requests) {
            assertEquals(
                CommandResult.Rejected("VERIFIED_TRANSPORT_SESSION_REQUIRED"),
                router.execute(request)
            )
        }
    }

    @Test fun sensitiveAndUnknownActionsAreAlsoRejected() {
        val requests = listOf(
            UntrustedCommandRequest("read_screen"),
            UntrustedCommandRequest("send_message"),
            UntrustedCommandRequest("transfer_money"),
            UntrustedCommandRequest("root_shell")
        )
        for (request in requests) {
            assertEquals(
                CommandResult.Rejected("VERIFIED_TRANSPORT_SESSION_REQUIRED"),
                router.execute(request)
            )
        }
    }

    @Test fun malformedActionIsRejectedBeforeSessionAdmission() {
        assertEquals(
            CommandResult.Rejected("INVALID_ACTION"),
            router.execute(UntrustedCommandRequest(" "))
        )
        assertEquals(
            CommandResult.Rejected("INVALID_ACTION"),
            router.execute(UntrustedCommandRequest("x".repeat(129)))
        )
    }
}
