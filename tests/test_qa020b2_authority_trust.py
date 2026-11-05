import unittest
from pathlib import Path

from scripts.qa020b2_authority_trust import (
    BUTTON_DESCRIPTIONS,
    CANCELLED,
    CREDENTIAL_CANCELLED,
    FIELD_LABELS,
    INSECURE_DENIAL,
    INITIAL_STATUS,
    PACKAGE,
    PREVIEW_FAILURE,
    assert_authority_screen,
    assert_cancelled,
    assert_credential_cancelled,
    assert_insecure_denial,
    assert_launcher,
    assert_preview_failure,
    assert_trust_state_unchanged,
    find_button,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/qa005-emulator.yml").read_text(encoding="utf-8")
SMOKE = (ROOT / "scripts/qa020b2_authority_trust_smoke.sh").read_text(encoding="utf-8")


def node(kind, text="", desc="", bounds="[10,20][210,100]", enabled="true",
         clickable="false", package=PACKAGE, visible="true"):
    return (
        f'<node package="{package}" class="{kind}" text="{text}" '
        f'content-desc="{desc}" bounds="{bounds}" enabled="{enabled}" '
        f'clickable="{clickable}" visible-to-user="{visible}"/>'
    )


def authority_xml(state="Trust state: unavailable. All mutations are refused.",
                  status=INITIAL_STATUS, edit_texts=None, labels=None):
    labels = FIELD_LABELS if labels is None else labels
    edit_texts = [""] * 5 if edit_texts is None else edit_texts
    parts = [node("android.widget.TextView", text="Offline authority trust")]
    parts.extend(node("android.widget.TextView", text=label) for label in labels)
    parts.extend(node("android.widget.EditText", text=value) for value in edit_texts)
    parts.extend([
        node("android.widget.TextView", text=state),
        node("android.widget.TextView", text=status),
    ])
    return "<hierarchy>" + "".join(parts) + "</hierarchy>"


def button_xml(description, **kwargs):
    return "<hierarchy>" + node(
        "android.widget.Button", desc=description, clickable="true", **kwargs
    ) + "</hierarchy>"


class Qa020B2HierarchyTests(unittest.TestCase):
    def test_authority_screen_accepts_fresh_emulator_unavailable_state(self):
        self.assertTrue(assert_authority_screen(authority_xml()).startswith(
            "Trust state: unavailable."
        ))

    def test_authority_screen_accepts_empty_state(self):
        self.assertTrue(assert_authority_screen(authority_xml(
            state="Trust state: empty. First install requires generation 1."
        )).startswith("Trust state: empty."))

    def test_corrupt_or_recovery_state_is_not_accepted_as_fresh(self):
        for state in (
            "Trust state: corrupt · INVALID_RECORD. All mutations are refused.",
            "Trust state: recovery required at watermark 2.",
        ):
            with self.subTest(state=state), self.assertRaises(ValueError):
                assert_authority_screen(authority_xml(state=state))

    def test_missing_field_label_is_rejected(self):
        with self.assertRaises(ValueError):
            assert_authority_screen(authority_xml(labels=FIELD_LABELS[:-1]))

    def test_missing_edit_field_is_rejected(self):
        with self.assertRaises(ValueError):
            assert_authority_screen(authority_xml(edit_texts=[""] * 4))

    def test_extra_edit_field_is_rejected(self):
        with self.assertRaises(ValueError):
            assert_authority_screen(authority_xml(edit_texts=[""] * 6))

    def test_visible_enabled_button_returns_center(self):
        xml = button_xml(BUTTON_DESCRIPTIONS["preview"])
        self.assertEqual(find_button(xml, BUTTON_DESCRIPTIONS["preview"]), (110, 60))

    def test_disabled_button_is_rejected(self):
        xml = button_xml(BUTTON_DESCRIPTIONS["preview"], enabled="false")
        with self.assertRaises(ValueError):
            find_button(xml, BUTTON_DESCRIPTIONS["preview"])

    def test_wrong_package_button_is_rejected(self):
        xml = button_xml(BUTTON_DESCRIPTIONS["preview"], package="com.android.settings")
        with self.assertRaises(ValueError):
            find_button(xml, BUTTON_DESCRIPTIONS["preview"])

    def test_duplicate_button_is_rejected(self):
        xml = button_xml(BUTTON_DESCRIPTIONS["preview"])
        with self.assertRaises(ValueError):
            find_button(xml.replace("</hierarchy>", xml.removeprefix("<hierarchy>")))

    def test_malformed_or_nonpositive_bounds_are_rejected(self):
        for bounds in ("unknown", "[10,10][10,10]", "[20,20][10,10]"):
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                find_button(button_xml(BUTTON_DESCRIPTIONS["preview"], bounds=bounds),
                            BUTTON_DESCRIPTIONS["preview"])

    def test_invisible_button_is_rejected(self):
        with self.assertRaises(ValueError):
            find_button(button_xml(BUTTON_DESCRIPTIONS["preview"], visible="false"),
                        BUTTON_DESCRIPTIONS["preview"])

    def test_invalid_fingerprint_preview_is_visible(self):
        assert_preview_failure(authority_xml(status=PREVIEW_FAILURE))

    def test_insecure_device_confirmation_is_denied(self):
        assert_insecure_denial(authority_xml(status=INSECURE_DENIAL))

    def test_credential_prompt_cancellation_is_visible(self):
        assert_credential_cancelled(authority_xml(status=CREDENTIAL_CANCELLED))

    def test_cancel_clears_all_fields_and_preserves_trust_state(self):
        xml = authority_xml(status=CANCELLED, edit_texts=[""] * 5)
        self.assertTrue(assert_cancelled(xml).startswith("Trust state: unavailable."))

    def test_cancel_with_retained_import_is_rejected(self):
        with self.assertRaises(ValueError):
            assert_cancelled(authority_xml(status=CANCELLED, edit_texts=["secret"] + [""] * 4))

    def test_trust_state_must_remain_identical(self):
        before = "Trust state: empty. First install requires generation 1."
        after = authority_xml(state=before, status=CANCELLED)
        self.assertEqual(assert_trust_state_unchanged(before, after), before)
        with self.assertRaises(ValueError):
            assert_trust_state_unchanged(before, authority_xml())

    def test_launcher_return_is_verified(self):
        assert_launcher("<hierarchy>" + node(
            "android.widget.TextView", text="MR. NOTHING"
        ) + "</hierarchy>")
        with self.assertRaises(ValueError):
            assert_launcher("<hierarchy></hierarchy>")

    def test_emulator_workflow_runs_runtime_gate_and_policy_tests(self):
        self.assertIn("'scripts/qa020b2_*'", WORKFLOW)
        self.assertIn("'tests/test_qa020b2_*'", WORKFLOW)
        self.assertIn("QA-020B2: owner authority trust UI runtime", WORKFLOW)
        self.assertIn("qa020b2_authority_trust_smoke.sh", WORKFLOW)

    def test_smoke_is_emulator_only_and_never_enters_credentials(self):
        self.assertIn('case "$ANDROID_SERIAL" in', SMOKE)
        self.assertIn('emulator-*)', SMOKE)
        self.assertIn('getprop ro.kernel.qemu', SMOKE)
        self.assertIn('grep -qx 1', SMOKE)
        self.assertNotIn("input text", SMOKE)
        self.assertNotIn("settings put", SMOKE)
        self.assertNotIn("cmd role add-role-holder", SMOKE)
        self.assertNotIn("pm grant", SMOKE)
        self.assertNotIn("fastboot", SMOKE)
        self.assertNotIn("adb root", SMOKE)


if __name__ == "__main__":
    unittest.main()
