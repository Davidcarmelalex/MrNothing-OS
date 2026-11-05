import unittest
from pathlib import Path

from scripts.qa020b2_authority_trust import (
    BUTTON_DESCRIPTIONS,
    CANCELLED,
    CREDENTIAL_CANCELLED,
    FIELD_DUMMY_VALUES,
    FIELD_HINTS,
    FIELD_LABELS,
    INSECURE_DENIAL,
    INITIAL_STATUS,
    PACKAGE,
    PREVIEW_FAILURE,
    assert_authority_screen,
    assert_cancelled,
    assert_cancel_status,
    assert_credential_cancelled,
    assert_dummy_fields,
    assert_insecure_denial,
    assert_launcher,
    assert_preview_failure,
    assert_trust_state_unchanged,
    find_button,
    find_field,
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
    edit_texts = FIELD_HINTS if edit_texts is None else edit_texts
    parts = [node("android.widget.TextView", text="Offline authority trust")]
    for index, label in enumerate(labels):
        parts.append(node("android.widget.TextView", text=label))
        if index < len(edit_texts):
            parts.append(node("android.widget.EditText", text=edit_texts[index]))
    for extra in edit_texts[len(labels):]:
        parts.append(node("android.widget.EditText", text=extra))
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

    def test_initial_status_may_be_below_scroll_view_viewport(self):
        self.assertTrue(assert_authority_screen(authority_xml(status="")).startswith(
            "Trust state: unavailable."
        ))

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
            assert_authority_screen(authority_xml(edit_texts=FIELD_HINTS[:-1]))

    def test_extra_edit_field_is_rejected(self):
        with self.assertRaises(ValueError):
            assert_authority_screen(authority_xml(edit_texts=FIELD_HINTS + ("extra",)))

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
            find_button(xml.replace("</hierarchy>", xml.removeprefix("<hierarchy>")),
                        BUTTON_DESCRIPTIONS["preview"])

    def test_malformed_or_nonpositive_bounds_are_rejected(self):
        for bounds in ("unknown", "[10,10][10,10]", "[20,20][10,10]"):
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                find_button(button_xml(BUTTON_DESCRIPTIONS["preview"], bounds=bounds),
                            BUTTON_DESCRIPTIONS["preview"])

    def test_invisible_button_is_rejected(self):
        with self.assertRaises(ValueError):
            find_button(button_xml(BUTTON_DESCRIPTIONS["preview"], visible="false"),
                        BUTTON_DESCRIPTIONS["preview"])

    def test_field_locator_uses_label_to_find_following_edit_text(self):
        xml = (
            "<hierarchy>"
            + node("android.widget.TextView", text=FIELD_LABELS[2])
            + node("android.widget.EditText", text=FIELD_HINTS[2], bounds="[20,40][220,140]")
            + "</hierarchy>"
        )
        self.assertEqual(find_field(xml, FIELD_LABELS[2]), (120, 90))

    def test_field_locator_rejects_missing_or_unknown_label(self):
        with self.assertRaises(ValueError):
            find_field(authority_xml(), "not a real field")
        missing_edit = (
            "<hierarchy>"
            + node("android.widget.TextView", text=FIELD_LABELS[0])
            + node("android.widget.TextView", text=FIELD_LABELS[1])
            + "</hierarchy>"
        )
        with self.assertRaises(ValueError):
            find_field(missing_edit, FIELD_LABELS[0])

    def test_invalid_fingerprint_preview_is_visible(self):
        assert_preview_failure(authority_xml(status=PREVIEW_FAILURE))

    def test_insecure_device_confirmation_is_denied(self):
        assert_insecure_denial(authority_xml(status=INSECURE_DENIAL))

    def test_credential_prompt_cancellation_is_visible(self):
        assert_credential_cancelled(authority_xml(status=CREDENTIAL_CANCELLED))

    def test_dummy_values_are_verified_before_cancel(self):
        self.assertTrue(assert_dummy_fields(authority_xml(
            edit_texts=FIELD_DUMMY_VALUES
        )).startswith("Trust state: unavailable."))

    def test_wrong_dummy_value_is_rejected(self):
        values = list(FIELD_DUMMY_VALUES)
        values[2] = "unexpected"
        with self.assertRaises(ValueError):
            assert_dummy_fields(authority_xml(edit_texts=values))

    def test_cancel_status_is_asserted_in_its_own_visible_snapshot(self):
        assert_cancel_status(authority_xml(status=CANCELLED))
        with self.assertRaises(ValueError):
            assert_cancel_status(authority_xml(status=INITIAL_STATUS))

    def test_cancel_restores_all_five_empty_field_hints_and_preserves_state(self):
        self.assertTrue(assert_cancelled(authority_xml(
            status="", edit_texts=FIELD_HINTS
        )).startswith("Trust state: unavailable."))

    def test_cancel_with_retained_import_is_rejected(self):
        values = (FIELD_DUMMY_VALUES[0],) + FIELD_HINTS[1:]
        with self.assertRaises(ValueError):
            assert_cancelled(authority_xml(status=CANCELLED, edit_texts=values))

    def test_cancel_rejects_partial_scroll_viewport(self):
        partial = authority_xml(
            status=CANCELLED,
            labels=FIELD_LABELS[-3:],
            edit_texts=FIELD_HINTS[-3:]
        )
        with self.assertRaises(ValueError):
            assert_cancelled(partial)

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

    def test_smoke_is_emulator_only_and_uses_only_fixed_invalid_dummy_values(self):
        self.assertIn('case "$ANDROID_SERIAL" in', SMOKE)
        self.assertIn('emulator-*)', SMOKE)
        self.assertIn('getprop ro.kernel.qemu', SMOKE)
        self.assertIn('grep -qx 1', SMOKE)
        self.assertIn('adb -s "$ANDROID_SERIAL" shell input text "$value"', SMOKE)
        self.assertIn('qa020b2_authority_trust.py cancel-status', SMOKE)
        for label, value in zip(FIELD_LABELS, FIELD_DUMMY_VALUES):
            self.assertIn(f'enter_dummy_field "{label}" "{value}"', SMOKE)
        self.assertNotIn("settings put", SMOKE)
        self.assertNotIn("cmd role add-role-holder", SMOKE)
        self.assertNotIn("pm grant", SMOKE)
        self.assertNotIn("fastboot", SMOKE)
        self.assertNotIn("adb root", SMOKE)
        self.assertNotIn('input text "$PIN"', SMOKE)
        self.assertNotIn('input text "$PASSWORD"', SMOKE)


if __name__ == "__main__":
    unittest.main()
