"""Strict UI-hierarchy assertions for SEC-020B2 runtime smoke tests."""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PACKAGE = "tech.mrnothing.os"
TITLE = "Offline authority trust"
FIELD_LABELS = (
    "Authority key identifier",
    "Generation",
    "Ed25519 public-key SPKI DER (canonical Base64)",
    "Current-authority rotation signature (Base64)",
    "Independently obtained SHA-256 fingerprint",
)
INITIAL_STATUS = "No authority change is pending. Compare the fingerprint independently."
PREVIEW_FAILURE = (
    "Candidate fingerprint unavailable. Check the key identifier, generation and canonical Base64."
)
INSECURE_DENIAL = "Secure, unlocked and interactive device state required. Refused."
CREDENTIAL_CANCELLED = "Credential canceled, expired, mismatched or unsafe. No trust change made."
CANCELLED = "Canceled. No trust change was made."
BUTTON_DESCRIPTIONS = {
    "preview": "Calculate the fingerprint of the entered Ed25519 public key",
    "confirm": "Require separate fingerprint confirmation and fresh Android device credential",
    "cancel": "Cancel any pending trust ceremony and clear imported public-key fields",
    "return": "Return to Mr. Nothing without changing authority trust",
}
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\Z")


def parse_hierarchy(xml):
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ValueError("Malformed UIAutomator hierarchy") from exc
    if root.tag != "hierarchy":
        raise ValueError("Expected UIAutomator hierarchy root")
    return list(root.iter("node"))


def _exact_text(nodes, expected, class_name=None):
    matches = [
        node for node in nodes
        if node.get("package") == PACKAGE
        and node.get("text") == expected
        and (class_name is None or node.get("class") == class_name)
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one local UI node with text: {expected}")
    return matches[0]


def trust_state(xml):
    nodes = parse_hierarchy(xml)
    matches = [
        node.get("text", "")
        for node in nodes
        if node.get("package") == PACKAGE
        and node.get("class") == "android.widget.TextView"
        and node.get("text", "").startswith("Trust state: ")
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one authority trust-state label")
    value = matches[0]
    if not (value.startswith("Trust state: empty.") or
            value.startswith("Trust state: unavailable.")):
        raise ValueError("Unexpected trust state for a fresh disposable emulator")
    return value


def assert_authority_screen(xml):
    nodes = parse_hierarchy(xml)
    _exact_text(nodes, TITLE, "android.widget.TextView")
    for label in FIELD_LABELS:
        _exact_text(nodes, label, "android.widget.TextView")
    edits = [
        node for node in nodes
        if node.get("package") == PACKAGE
        and node.get("class") == "android.widget.EditText"
    ]
    if len(edits) != 5:
        raise ValueError("Expected exactly five authority import fields")
    # The status TextView is below the initial ScrollView viewport; later actions assert it.
    return trust_state(xml)


def find_button(xml, description):
    matches = [
        node for node in parse_hierarchy(xml)
        if node.get("package") == PACKAGE
        and node.get("class") == "android.widget.Button"
        and node.get("content-desc") == description
        and node.get("enabled") == "true"
        and node.get("clickable") == "true"
        and node.get("visible-to-user", "true") == "true"
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one visible, enabled local button")
    bounds = BOUNDS.fullmatch(matches[0].get("bounds", ""))
    if not bounds:
        raise ValueError("Invalid button bounds")
    x1, y1, x2, y2 = map(int, bounds.groups())
    if x1 >= x2 or y1 >= y2:
        raise ValueError("Nonpositive button bounds")
    return (x1 + x2) // 2, (y1 + y2) // 2


def assert_preview_failure(xml):
    _exact_text(parse_hierarchy(xml), PREVIEW_FAILURE, "android.widget.TextView")


def assert_insecure_denial(xml):
    _exact_text(parse_hierarchy(xml), INSECURE_DENIAL, "android.widget.TextView")


def assert_credential_cancelled(xml):
    _exact_text(parse_hierarchy(xml), CREDENTIAL_CANCELLED, "android.widget.TextView")


def assert_cancelled(xml):
    nodes = parse_hierarchy(xml)
    _exact_text(nodes, CANCELLED, "android.widget.TextView")
    edits = [
        node for node in nodes
        if node.get("package") == PACKAGE
        and node.get("class") == "android.widget.EditText"
    ]
    if len(edits) != 5 or any(node.get("text", "") for node in edits):
        raise ValueError("Cancel did not clear all five authority import fields")
    return trust_state(xml)


def assert_trust_state_unchanged(before, after_xml):
    after = trust_state(after_xml)
    if before != after:
        raise ValueError("Trust state changed during the non-committing UI smoke test")
    return after


def assert_launcher(xml):
    _exact_text(parse_hierarchy(xml), "MR. NOTHING", "android.widget.TextView")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=(
        "screen", "button", "preview", "denied", "credential-cancelled",
        "cancelled", "same-state", "launcher"
    ))
    parser.add_argument("xml")
    parser.add_argument("value", nargs="?")
    args = parser.parse_args()
    content = Path(args.xml).read_text(encoding="utf-8")
    if args.mode == "screen":
        print(assert_authority_screen(content))
    elif args.mode == "button":
        if not args.value:
            raise ValueError("Button description is required")
        print(*find_button(content, args.value))
    elif args.mode == "preview":
        assert_preview_failure(content)
        print("Invalid/empty fingerprint preview refused")
    elif args.mode == "denied":
        assert_insecure_denial(content)
        print("Insecure-device trust transition refused")
    elif args.mode == "credential-cancelled":
        assert_credential_cancelled(content)
        print("System credential prompt canceled without trust mutation")
    elif args.mode == "cancelled":
        print(assert_cancelled(content))
    elif args.mode == "same-state":
        if args.value is None:
            raise ValueError("Previous trust state is required")
        print(assert_trust_state_unchanged(args.value, content))
    elif args.mode == "launcher":
        assert_launcher(content)
        print("Launcher returned")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"QA-020B2 REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(1)
