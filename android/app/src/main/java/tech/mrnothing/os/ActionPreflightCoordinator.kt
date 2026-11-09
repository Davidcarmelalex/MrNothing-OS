package tech.mrnothing.os

/**
 * Supplies current safety context from app-owned runtime state.
 *
 * Implementations must not read model/LLM output, remote request fields, or
 * caller-supplied booleans as evidence. No production provider is connected.
 */
internal fun interface ScreenSafetySignalProvider {
    fun currentSignals(): ScreenPreflightSignals?
}

/** Safe default until a reviewed app-owned provider exists. */
internal object DenyAllScreenSafetySignalProvider : ScreenSafetySignalProvider {
    override fun currentSignals(): ScreenPreflightSignals = ScreenPreflightSignals(
        trustedOwnerSession = false,
        safeUnlockedDevice = false,
        ownAccessibilityServiceEnabled = false,
        activeProjectionSession = false,
        consentIndicatorVisible = false,
        restrictedSurface = true,
        emergencyStopEngaged = true,
        sessionRevoked = true
    )
}

internal enum class ActionPreflightBlockReason {
    INVALID_ACTION_ARGUMENTS,
    SAFETY_STATE_UNAVAILABLE,
    SAFETY_POLICY_BLOCKED,
    PLATFORM_PREREQUISITES_BLOCKED
}

/**
 * A positive result means only that two read-only preflight policies passed.
 * It is not owner consent, verified transport, authorization, or dispatch.
 */
internal sealed interface ActionPreflightDecision {
    data object ReadyForIndependentAuthorization : ActionPreflightDecision
    data class Blocked(
        val reason: ActionPreflightBlockReason,
        val platformReason: ActionPermissionBlockReason? = null
    ) : ActionPreflightDecision
}

/**
 * Composes the existing safety-context and action-specific Android probes.
 *
 * This class has no executor, dispatcher, permission prompt, or platform side
 * effect. Callers must still obtain independent verified transport/owner
 * capability and revalidate all evidence at the eventual side-effect boundary.
 */
internal class ActionPreflightCoordinator(
    private val permissionGate: ActionPermissionGate,
    private val safetySignals: ScreenSafetySignalProvider =
        DenyAllScreenSafetySignalProvider
) {
    fun evaluate(
        action: String,
        arguments: OwnerActionArguments?
    ): ActionPreflightDecision {
        // Reject malformed or mismatched action/argument pairs before reading
        // app state or Android platform state.
        if (OwnerActionArgumentsCanonicalizer.canonicalJson(action, arguments) == null) {
            return ActionPreflightDecision.Blocked(
                ActionPreflightBlockReason.INVALID_ACTION_ARGUMENTS
            )
        }

        val signals = try {
            safetySignals.currentSignals()
        } catch (_: SecurityException) {
            null
        } catch (_: RuntimeException) {
            null
        } ?: return ActionPreflightDecision.Blocked(
            ActionPreflightBlockReason.SAFETY_STATE_UNAVAILABLE
        )

        if (ScreenActionPreflight.evaluate(action, signals) !=
            ScreenPreflightResult.PRECONDITIONS_PRESENT
        ) {
            return ActionPreflightDecision.Blocked(
                ActionPreflightBlockReason.SAFETY_POLICY_BLOCKED
            )
        }

        return when (val platform = permissionGate.evaluate(action, arguments)) {
            ActionPermissionDecision.PlatformPrerequisitesPresent ->
                ActionPreflightDecision.ReadyForIndependentAuthorization
            is ActionPermissionDecision.Blocked ->
                ActionPreflightDecision.Blocked(
                    ActionPreflightBlockReason.PLATFORM_PREREQUISITES_BLOCKED,
                    platform.reason
                )
        }
    }
}
