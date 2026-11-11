"""QA-UX-008 parser, instrumentation and exact-head workflow regression gates."""
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/qa_ux008_agent_plan.py"
spec = importlib.util.spec_from_file_location("qa_ux008_agent_plan", HELPER)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def hierarchy(*nodes):
    return '<hierarchy rotation="0">' + "".join(nodes) + "</hierarchy>"


def node(**attrs):
    defaults = {
        "package": "tech.mrnothing.os",
        "class": "android.widget.Button",
        "content-desc": helper.BUTTONS["entry"],
        "enabled": "true",
        "clickable": "true",
        "visible-to-user": "true",
        "bounds": "[10,20][210,100]",
    }
    defaults.update(attrs)
    return "<node " + " ".join(f'{k}="{v}"' for k, v in defaults.items()) + "/>"


class AgentPlanUiParserTests(unittest.TestCase):
    def test_owner_entry_is_uniquely_clickable_and_in_bounds(self):
        self.assertEqual((110, 60), helper.button_center(
            hierarchy(node()), helper.BUTTONS["entry"], 300, 500))

    def test_rejects_wrong_package_disabled_duplicate_and_offscreen_controls(self):
        for content in (
            node(package="com.other.app"),
            node(enabled="false"),
            node(**{"visible-to-user": "false"}),
            node() + node(),
            node(bounds="[10,20][310,100]"),
            node(bounds="[10,20][10,100]"),
        ):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    helper.button_center(hierarchy(content), helper.BUTTONS["entry"], 300, 500)

    def test_rejects_unrecognized_action_or_invalid_hierarchy(self):
        with self.assertRaises(ValueError):
            helper.button_center(hierarchy(node()), "Execute real message", 300, 500)
        with self.assertRaises(ValueError):
            helper.nodes("<other/>")

    def test_review_requires_explicit_denial_and_no_consent(self):
        good = ("Offline sample rehearsal (no AI inference):\n"
                "State: REVIEW_REQUIRED\nPreviewed: 0/3\n"
                "Supervisor gate: BLOCKED_NO_ACTIVE_STEP\n"
                "Authorized: No · Device actions executed: No · No consent granted.")
        text_node = node(**{"class": "android.widget.TextView", "text": good,
                            "content-desc": ""})
        helper.assert_screen(hierarchy(text_node), "review")
        with self.assertRaises(ValueError):
            helper.assert_screen(hierarchy(text_node.replace("Authorized: No", "Authorized: Yes")), "review")

    def test_focus_requires_labeled_local_button(self):
        focused = node(focused="true")
        self.assertEqual(helper.BUTTONS["entry"], helper.focused_button(hierarchy(focused)))
        with self.assertRaises(ValueError):
            helper.focused_button(hierarchy(node(focused="true", **{"content-desc": ""})))

    def test_switching_preview_modes_cancels_hidden_rehearsal_cursor(self):
        activity = (ROOT / "android/app/src/main/java/tech/mrnothing/os/AgentPlanPreviewActivity.kt").read_text()
        instrumentation = (ROOT / "android/app/src/androidTest/java/tech/mrnothing/os/AgentPlanPreviewActivityTest.kt").read_text()
        for function, next_function in (("private fun preview(action: String)", "private fun previewPlan()"),
                                        ("private fun previewPlan()", "private fun showRehearsal(")):
            section = activity.split(function, 1)[1].split(next_function, 1)[0]
            self.assertIn("rehearsal.cancel()", section)
        self.assertIn("testSwitchingPreviewModesInvalidatesAcknowledgedRehearsal", instrumentation)
        self.assertIn("Supervisor gate: BLOCKED_TERMINAL_REHEARSAL", instrumentation)

    def test_instrumentation_is_registered_and_scope_is_exact(self):
        gradle = (ROOT / "android/app/build.gradle.kts").read_text()
        kotlin = (ROOT / "android/app/src/androidTest/java/tech/mrnothing/os/AgentPlanPreviewActivityTest.kt").read_text()
        workflow = (ROOT / ".github/workflows/qa005-emulator.yml").read_text()
        shell = (ROOT / "scripts/qa_ux008_agent_plan_smoke.sh").read_text()
        self.assertIn('"tech.mrnothing.os.AgentPlanPreviewActivityTest"', gradle)
        for token in ("testSampleReviewProgressionTerminalDenialAndCancellation",
                      "testOnStopClearsActiveRehearsalWithoutGrant",
                      "BLOCKED_NO_VERIFIED_SESSION", "BLOCKED_TERMINAL_REHEARSAL",
                      "Previewed: 3/3", "Offline agent plan preview"):
            self.assertIn(token, kotlin)
        self.assertIn("github.head_ref == 'feat/qa-ux008-agent-rehearsal-emulator-20261111'", workflow)
        self.assertIn("github.event.pull_request.head.repo.full_name == 'Davidcarmelalex/MrNothing-OS'", workflow)
        self.assertIn("QAUX008_OUTPUT:", workflow)
        self.assertIn("bash scripts/qa_ux008_agent_plan_smoke.sh", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("ro.kernel.qemu", shell)
        self.assertIn("settings put system font_scale 2.0", shell)
        self.assertIn("trap restore EXIT INT TERM", shell)
        self.assertIn("KEYCODE_TAB", shell)
        self.assertIn("tap entry", shell)
        self.assertNotIn("adb root", shell)
        self.assertNotIn("am start -W -n tech.mrnothing.os/.AgentPlanPreviewActivity", shell)


if __name__ == "__main__":
    unittest.main()
