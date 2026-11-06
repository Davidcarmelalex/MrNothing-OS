"""Read-only emulator UI semantics audit; NOT spoken TalkBack acceptance."""
import argparse
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

PKG = "tech.mrnothing.os"
RECOVERY = "Recovery: open Android Home app settings to select the stock launcher"
SETTINGS = "Open Android system settings"
CONSENT = "Open Android confirmation to select Mr. Nothing as the default Home app"
BOUND = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\Z")


def audit(xml: str, density: float) -> dict:
    if not 0.5 <= density <= 8:
        raise ValueError("Invalid emulator density")
    try:
        nodes = [n.attrib for n in ET.fromstring(xml).iter("node")
                 if n.attrib.get("package") == PKG]
    except ET.ParseError as exc:
        raise ValueError("Malformed hierarchy") from exc
    if not nodes:
        raise ValueError("Launcher hierarchy missing")
    headings = ["MR. NOTHING", "Device status", "Installed apps"]
    indices = []
    for heading in headings:
        found = [i for i, n in enumerate(nodes)
                 if n.get("class") == "android.widget.TextView" and n.get("text") == heading]
        if len(found) != 1:
            raise ValueError("Missing or ambiguous section " + heading)
        indices.append(found[0])
    if indices != sorted(indices):
        raise ValueError("Section reading order incorrect")
    actions = [(i, n) for i, n in enumerate(nodes)
               if n.get("class") == "android.widget.Button"]
    if len(actions) < 2:
        raise ValueError("No system actions")
    descriptions = []
    for _, node in actions:
        if any(node.get(k) != "true" for k in ("clickable", "enabled", "focusable")):
            raise ValueError("Inaccessible action")
        desc = node.get("content-desc", "").strip()
        if not desc:
            raise ValueError("Unlabelled action")
        descriptions.append(desc)
    for desc in (RECOVERY, SETTINGS):
        if descriptions.count(desc) != 1:
            raise ValueError("Missing or duplicate system action")
    if descriptions.count(CONSENT) > 1:
        raise ValueError("Duplicate consent action")
    def index(desc):
        return next(i for i, n in actions if n.get("content-desc") == desc)
    if not (indices[1] < index(RECOVERY) < index(SETTINGS) < indices[2]):
        raise ValueError("System action reading order incorrect")
    if CONSENT in descriptions and not (indices[1] < index(CONSENT) < index(RECOVERY)):
        raise ValueError("Consent action reading order incorrect")
    for desc in (RECOVERY, SETTINGS):
        node = next(n for _, n in actions if n["content-desc"] == desc)
        m = BOUND.fullmatch(node.get("bounds", ""))
        if not m:
            raise ValueError("Missing action bounds")
        x1, y1, x2, y2 = map(int, m.groups())
        if min(x2-x1, y2-y1) / density < 48:
            raise ValueError("System action below 48dp touch target")
    return {"check": "QA-012 emulator accessibility semantics",
            "structural_checks_passed": True, "action_count": len(actions),
            "consent_action_present": CONSENT in descriptions,
            "recovery_action_present": True, "spoken_navigation_verified": False,
            "acceptance_passed": False, "talkback_enabled_by_test": False,
            "note": "Hierarchy, labels, order and bounds only; NOT spoken TalkBack acceptance."}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hierarchy", type=Path, required=True)
    p.add_argument("--density", type=float, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = audit(a.hierarchy.read_text(), a.density)
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("QA-012 structural audit passed; spoken TalkBack NOT tested")


if __name__ == "__main__":
    main()
