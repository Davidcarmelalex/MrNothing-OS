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


LOW_RISK = frozenset({"open_app", "read_screen", "get_battery", "scroll", "navigate"})
SENSITIVE = frozenset({"purchase", "transfer_money", "delete_data", "change_security"})
CONTACT_ACTIONS = frozenset({"place_call", "send_message"})


def authorize(request: Request) -> Decision:
    if not request.authenticated:
        return Decision.DENY
    if request.action in LOW_RISK:
        return Decision.ALLOW
    if request.action in CONTACT_ACTIONS:
        return Decision.ALLOW if request.contact_approved else Decision.APPROVAL
    if request.action in SENSITIVE:
        return Decision.APPROVAL
    return Decision.DENY
