import unittest
from threading import Event

from core.agent_sandbox import PlanStep, SandboxPlan, SandboxDevice, simulate

DEVICE = SandboxDevice(75, frozenset({"com.android.settings", "com.example.app"}))


def step(i=1, action="get_battery", args=None):
    return PlanStep(f"cmd-{i}", action, {} if args is None else args)


def plan(*steps):
    return SandboxPlan("plan-1", tuple(steps or (step(),)))


def run(p=None, **kwargs):
    return simulate(p if p is not None else plan(),
                    transport_authenticated=kwargs.pop("transport_authenticated", True),
                    device=kwargs.pop("device", DEVICE),
                    deadline=kwargs.pop("deadline", 10.0),
                    clock=kwargs.pop("clock", lambda: 1.0),
                    **kwargs)


class AgentSandboxTests(unittest.TestCase):
    def test_battery_simulated(self):
        result = run()
        self.assertEqual(result.state, "SUCCEEDED")
        self.assertEqual(result.steps[0].value, "75")
        self.assertFalse(result.device_actions_executed)
        self.assertFalse(result.production_ready)

    def test_app_launch_simulated_not_executed(self):
        result = run(plan(step(action="open_app", args={"packageName": "com.android.settings"})))
        self.assertEqual(result.steps[0].outcome, "WOULD_OPEN_APP")
        self.assertFalse(result.device_actions_executed)

    def test_two_steps(self):
        result = run(plan(step(), step(2, "open_app", {"packageName": "com.example.app"})))
        self.assertEqual(len(result.steps), 2)

    def test_unauthenticated(self):
        self.assertEqual(run(transport_authenticated=False).reason, "UNAUTHENTICATED")

    def test_non_boolean_auth(self):
        self.assertEqual(run(transport_authenticated=1).state, "REJECTED")

    def test_empty_plan(self):
        self.assertEqual(run(SandboxPlan("p", ())).reason, "INVALID_STEP_COUNT")

    def test_over_limit(self):
        self.assertEqual(run(plan(*[step(i) for i in range(21)])).reason, "INVALID_STEP_COUNT")

    def test_max_steps(self):
        self.assertEqual(run(plan(*[step(i) for i in range(20)])).state, "SUCCEEDED")

    def test_duplicate_step_id(self):
        self.assertEqual(run(plan(step(), step())).reason, "DUPLICATE_STEP_ID")

    def test_bad_plan_id(self):
        self.assertEqual(run(SandboxPlan("../bad", (step(),))).reason, "INVALID_PLAN")

    def test_bad_step_id(self):
        self.assertEqual(run(plan(PlanStep("../bad", "get_battery", {}))).reason, "INVALID_STEP_ID")

    def test_unknown_action(self):
        self.assertEqual(run(plan(step(action="root_shell"))).reason, "UNSUPPORTED_ACTION")

    def test_call_needs_approval(self):
        self.assertEqual(run(plan(step(action="place_call"))).state, "REJECTED")

    def test_transfer_refused(self):
        self.assertEqual(run(plan(step(action="transfer_money"))).state, "REJECTED")

    def test_read_screen_refused(self):
        self.assertEqual(run(plan(step(action="read_screen"))).state, "REJECTED")

    def test_extra_battery_args(self):
        self.assertEqual(run(plan(step(args={"surprise": 1}))).reason, "UNEXPECTED_ARGUMENTS")

    def test_extra_open_app_args(self):
        self.assertEqual(run(plan(step(action="open_app", args={"packageName": "com.example.app", "root": True}))).reason, "INVALID_PACKAGE_ARGUMENTS")

    def test_bad_package(self):
        self.assertEqual(run(plan(step(action="open_app", args={"packageName": "com.x;rm"}))).state, "REJECTED")

    def test_missing_app_fails(self):
        self.assertEqual(run(plan(step(action="open_app", args={"packageName": "com.absent"}))).reason, "APP_NOT_IN_SANDBOX")

    def test_invalid_later_step_prevents_all(self):
        result = run(plan(step(), step(2, "root_shell")))
        self.assertEqual(result.state, "REJECTED")
        self.assertEqual(result.steps, ())

    def test_cancel_before_start(self):
        flag = Event()
        flag.set()
        self.assertEqual(run(cancel=flag).state, "CANCELLED")

    def test_cancel_between_steps(self):
        flag = Event()
        calls = [0]
        def clock():
            calls[0] += 1
            if calls[0] == 1:
                flag.set()
            return 1.0
        result = run(plan(step(), step(2)), cancel=flag, clock=clock)
        self.assertEqual(result.state, "CANCELLED")
        self.assertEqual(len(result.steps), 1)

    def test_timeout_before_start(self):
        self.assertEqual(run(deadline=1.0).state, "TIMED_OUT")

    def test_timeout_between_steps(self):
        values = iter((1.0, 11.0))
        result = run(plan(step(), step(2)), clock=lambda: next(values))
        self.assertEqual(result.state, "TIMED_OUT")
        self.assertEqual(len(result.steps), 1)

    def test_clock_failure_fails_closed(self):
        def broken():
            raise RuntimeError("offline")
        self.assertEqual(run(clock=broken).reason, "CLOCK_UNAVAILABLE")

    def test_nan_clock_fails_closed(self):
        self.assertEqual(run(clock=lambda: float("nan")).state, "FAILED")

    def test_nan_deadline_refused(self):
        self.assertEqual(run(deadline=float("nan")).reason, "INVALID_DEADLINE")

    def test_invalid_device_refused(self):
        self.assertEqual(run(device=SandboxDevice(101, frozenset())).reason, "INVALID_SIMULATOR")

    def test_battery_unavailable(self):
        result = run(device=SandboxDevice(None, frozenset()))
        self.assertEqual(result.steps[0].value, "UNAVAILABLE")

    def test_malformed_arguments_refused(self):
        self.assertEqual(run(plan(step(args={"nan": float("nan")}))).state, "REJECTED")

    def test_non_json_arguments_refused(self):
        self.assertEqual(run(plan(step(args={"bad": object()}))).state, "REJECTED")

    def test_oversized_arguments_refused(self):
        self.assertEqual(run(plan(step(args={"pad": "x" * 9000}))).reason, "ARGUMENTS_TOO_LARGE")

    def test_cancel_signal_type(self):
        self.assertEqual(run(cancel=object()).reason, "INVALID_CANCEL_SIGNAL")

    def test_no_spoken_acceptance(self):
        self.assertFalse(run().spoken_navigation_verified)


if __name__ == "__main__":
    unittest.main()
