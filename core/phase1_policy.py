"""Minimal fail-closed Phase 1 action authorization policy.

This is a standalone foundation, not yet integrated with HERMES.
"""
from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    ALLOW = "allow"
    APPROVAL = "approval_required"
    DENY = "deny"


@dataclass(frozen=True)
class Request:
    action: str
    authenticated: bool
    contact_approved: bool = False


# Only actions that do not inspect screen contents or manipulate other UI state.
LOW_RISK = frozenset({"open_app", "get_battery"})
# Security boundary SEC-014: screen access and UI manipulation must NEVER be
# allowed by a model-supplied authentication/approval flag. Until a trusted,
# per-session owner consent and Android-permission gate is integrated, they
# remain approval-required and are NOT executable by the HERMES adapter.
SCREEN_ACTIONS = frozenset({"read_screen", "scroll", "navigate"})
SENSITIVE = frozenset({"purchase", "transfer_money", "delete_data", "change_security"})
CONTACT_ACTIONS = frozenset({"place_call", "send_message"})


def authorize(request: Request) -> Decision:
    if not request.authenticated:
        return Decision.DENY
    if request.action in LOW_RISK:
        return Decision.ALLOW
    if request.action in SCREEN_ACTIONS:
        return Decision.APPROVAL
    if request.action in CONTACT_ACTIONS:
        return Decision.ALLOW if request.contact_approved else Decision.APPROVAL
    if request.action in SENSITIVE:
        return Decision.APPROVAL
    return Decision.DENY
