"""M3 no-op executor: consumes verified capabilities without device effects."""

from dataclasses import dataclass

from core.owner_consent_transport import (
    OwnerConsentTlsAdapter,
    VerifiedOwnerActionCapability,
)


@dataclass(frozen=True)
class NoOpExecutionResult:
    accepted: bool
    reason: str
    simulated: bool
    device_actions_executed: bool = False


class NoOpActionExecutor:
    """Test harness only. It never calls Android, shell, network or OS APIs."""

    def __init__(self, adapter: OwnerConsentTlsAdapter) -> None:
        if type(adapter) is not OwnerConsentTlsAdapter:
            raise TypeError("a concrete trusted transport adapter is required")
        self._adapter = adapter

    def simulate(
        self,
        peer,
        capability: VerifiedOwnerActionCapability,
        *,
        action: str,
        arguments: dict,
    ) -> NoOpExecutionResult:
        """Consume one verified capability and report simulation only."""
        try:
            admission = self._adapter.consume_action_capability(
                peer,
                capability,
                action=action,
                arguments=arguments,
            )
        except Exception:
            return NoOpExecutionResult(
                False, "ADMISSION_UNAVAILABLE", False, False
            )
        if not admission.admitted:
            return NoOpExecutionResult(
                False, admission.reason, False, False
            )
        return NoOpExecutionResult(
            True, "SIMULATED_ONLY", True, False
        )
