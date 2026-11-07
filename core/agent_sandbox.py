"""AGENT-013: deterministic, *offline* plan simulator.

This is not a device executor, network endpoint, Android bridge, or proof of
authenticated transport. It deliberately has no OS/device side effects.
A future executor MUST bind plans to signed admission and user consent.
"""
from dataclasses import dataclass
import json
import math
import re
import time
from threading import Event
from typing import Callable

from core.hermes_gateway import CommandEnvelope, validate

_ID = re.compile(r"[A-Za-z0-9_.-]{1,128}\Z")
_SUPPORTED = frozenset({"get_battery", "open_app"})
_MAX_STEPS = 20


@dataclass(frozen=True)
class PlanStep:
    command_id: str
    action: str
    arguments: dict


@dataclass(frozen=True)
class SandboxPlan:
    plan_id: str
    steps: tuple[PlanStep, ...]


@dataclass(frozen=True)
class SandboxDevice:
    battery_percent: int | None
    installed_packages: frozenset[str]


@dataclass(frozen=True)
class SimulatedStep:
    command_id: str
    outcome: str
    value: str


@dataclass(frozen=True)
class SandboxResult:
    state: str
    reason: str
    steps: tuple[SimulatedStep, ...]
    device_actions_executed: bool = False
    spoken_navigation_verified: bool = False
    production_ready: bool = False


def _compile(plan: SandboxPlan, authenticated: bool):
    """Validate entire plan and snapshot arguments before simulation."""
    if authenticated is not True:
        return "UNAUTHENTICATED", ()
    if type(plan) is not SandboxPlan or type(plan.plan_id) is not str or not _ID.fullmatch(plan.plan_id):
        return "INVALID_PLAN", ()
    if type(plan.steps) is not tuple or not 1 <= len(plan.steps) <= _MAX_STEPS:
        return "INVALID_STEP_COUNT", ()
    seen = set()
    compiled = []
    for step in plan.steps:
        if type(step) is not PlanStep or type(step.command_id) is not str or not _ID.fullmatch(step.command_id):
            return "INVALID_STEP_ID", ()
        if step.command_id in seen:
            return "DUPLICATE_STEP_ID", ()
        seen.add(step.command_id)
        if type(step.action) is not str or step.action not in _SUPPORTED:
            return "UNSUPPORTED_ACTION", ()
        if type(step.arguments) is not dict:
            return "INVALID_ARGUMENTS", ()
        try:
            if len(json.dumps(step.arguments, allow_nan=False, sort_keys=True)) > 8192:
                return "ARGUMENTS_TOO_LARGE", ()
        except (TypeError, ValueError, OverflowError, RecursionError):
            return "INVALID_ARGUMENTS", ()
        if step.action == "get_battery":
            if step.arguments:
                return "UNEXPECTED_ARGUMENTS", ()
            value = ""
        else:
            if set(step.arguments) != {"packageName"}:
                return "INVALID_PACKAGE_ARGUMENTS", ()
            value = step.arguments["packageName"]
        verdict = validate(CommandEnvelope(step.command_id, step.action, step.arguments),
                           authenticated=True)
        if not verdict.accepted:
            return verdict.reason, ()
        compiled.append((step.command_id, step.action, value))
    return "VALID", tuple(compiled)


def simulate(
    plan: SandboxPlan,
    *,
    transport_authenticated: bool,
    device: SandboxDevice,
    deadline: float,
    cancel: Event | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> SandboxResult:
    """Simulate allowed actions only. Never calls Android, shell or network APIs."""
    reason, steps = _compile(plan, transport_authenticated)
    if reason != "VALID":
        return SandboxResult("REJECTED", reason, ())
    if type(device) is not SandboxDevice or (
        device.battery_percent is not None and
        (type(device.battery_percent) is not int or not 0 <= device.battery_percent <= 100)
    ) or type(device.installed_packages) is not frozenset or any(
        type(pkg) is not str or not pkg for pkg in device.installed_packages
    ):
        return SandboxResult("REJECTED", "INVALID_SIMULATOR", ())
    if type(deadline) not in (float, int) or not math.isfinite(deadline):
        return SandboxResult("REJECTED", "INVALID_DEADLINE", ())
    if cancel is not None and not isinstance(cancel, Event):
        return SandboxResult("REJECTED", "INVALID_CANCEL_SIGNAL", ())
    results = []
    for command_id, action, value in steps:
        if cancel is not None and cancel.is_set():
            return SandboxResult("CANCELLED", "OWNER_CANCELLED", tuple(results))
        try:
            now = clock()
            if type(now) not in (float, int) or not math.isfinite(now):
                raise ValueError("invalid clock")
        except Exception:
            return SandboxResult("FAILED", "CLOCK_UNAVAILABLE", tuple(results))
        if now >= deadline:
            return SandboxResult("TIMED_OUT", "DEADLINE_EXCEEDED", tuple(results))
        if action == "get_battery":
            battery = ("UNAVAILABLE" if device.battery_percent is None
                       else str(device.battery_percent))
            results.append(SimulatedStep(command_id, "SIMULATED_READ", battery))
        elif value in device.installed_packages:
            results.append(SimulatedStep(command_id, "WOULD_OPEN_APP", value))
        else:
            return SandboxResult("FAILED", "APP_NOT_IN_SANDBOX", tuple(results))
    return SandboxResult("SUCCEEDED", "SIMULATION_ONLY", tuple(results))
