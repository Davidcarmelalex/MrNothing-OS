"""Constrained HERMES-to-Android command adapter.

This module is transport-independent. It never executes shell commands or
trusts an LLM-generated authentication flag. A verified transport supplies
the authenticated principal separately.
"""
from dataclasses import dataclass
from typing import Any
from core.phase1_policy import Decision, Request, authorize

SUPPORTED = frozenset({"get_battery", "open_app"})

@dataclass(frozen=True)
class CommandEnvelope:
    command_id: str
    action: str
    arguments: dict[str, Any]

@dataclass(frozen=True)
class DispatchDecision:
    accepted: bool
    reason: str
    command_id: str

def validate(envelope: CommandEnvelope, *, authenticated: bool) -> DispatchDecision:
    if not envelope.command_id or len(envelope.command_id) > 128:
        return DispatchDecision(False, "INVALID_COMMAND_ID", envelope.command_id)
    if not isinstance(envelope.arguments, dict):
        return DispatchDecision(False, "INVALID_ARGUMENTS", envelope.command_id)
    decision = authorize(Request(action=envelope.action, authenticated=authenticated))
    if decision != Decision.ALLOW:
        return DispatchDecision(False, decision.value, envelope.command_id)
    if envelope.action not in SUPPORTED:
        return DispatchDecision(False, "NOT_IMPLEMENTED", envelope.command_id)
    if envelope.action == "open_app":
        package = envelope.arguments.get("packageName")
        if not isinstance(package, str) or not package or len(package) > 255:
            return DispatchDecision(False, "INVALID_PACKAGE", envelope.command_id)
        if not all(c.isalnum() or c in "._" for c in package):
            return DispatchDecision(False, "INVALID_PACKAGE", envelope.command_id)
    return DispatchDecision(True, "READY_FOR_AUTHENTICATED_TRANSPORT", envelope.command_id)
