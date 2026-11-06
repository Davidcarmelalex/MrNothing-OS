package tech.mrnothing.os

import android.content.Context
import org.json.JSONObject

/** Local, deliberately constrained command dispatcher.
 * Remote transport must authenticate the owner before constructing a command.
 * This class does not trust a JSON field claiming to be authenticated.
 */
data class TrustedCommand(
    val action: String,
    val approvedContact: Boolean = false,
    val packageName: String? = null
)
sealed class CommandResult {
    data class Success(val payload: String) : CommandResult()
    data class Rejected(val reason: String) : CommandResult()
}

class CommandRouter(private val context: Context) {
    fun execute(command: TrustedCommand, authenticatedByTransport: Boolean): CommandResult {
        val verdict = AgentPolicy.decide(
            AgentAction(command.action, authenticatedByTransport, command.approvedContact)
        )
        if (verdict != Verdict.ALLOW) return CommandResult.Rejected(verdict.name)
        return when (command.action) {
            "get_battery" -> {
                val data = DeviceDiagnostics.snapshot(context)
                CommandResult.Success(JSONObject().put("batteryPercent", data.batteryPercent).toString())
            }
            "open_app" -> {
                val pkg = command.packageName ?: return CommandResult.Rejected("MISSING_PACKAGE")
                try {
                    if (AppCatalog.launch(context, pkg)) CommandResult.Success("APP_LAUNCHED")
                    else CommandResult.Rejected("APP_NOT_LAUNCHABLE")
                } catch (_: RuntimeException) {
                    CommandResult.Rejected("APP_LAUNCH_FAILED")
                }
            }
            else -> CommandResult.Rejected("NOT_IMPLEMENTED")
        }
    }
}
