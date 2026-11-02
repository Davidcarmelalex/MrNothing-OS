"""QA-008: strictly verify affirmative HOME consent on disposable emulator."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from scripts.qa007_role_consent import BOUNDS, PACKAGE, verify_consent_prompt, tap_coordinates

APPROVE = frozenset({"allow", "set as default", "set as default app", "set default", "ok"})

def approve_coordinates(path: Path) -> tuple[int, int]:
    verify_consent_prompt(path)
    candidates = []
    for node in ET.parse(path).getroot().iter("node"):
        attrs = node.attrib
        if "permissioncontroller" not in attrs.get("package", "").lower():
            continue
        label = (attrs.get("text") or attrs.get("content-desc") or "").strip().lower()
        if label not in APPROVE or attrs.get("clickable") != "true" or attrs.get("enabled") != "true":
            continue
        match = BOUNDS.fullmatch(attrs.get("bounds", ""))
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            if x2 > x1 and y2 > y1:
                candidates.append(((x1 + x2) // 2, (y1 + y2) // 2))
    if len(candidates) != 1:
        raise ValueError("Expected exactly one approved system consent control")
    return candidates[0]

def verify_granted(before: str, after: str) -> None:
    lines = lambda s: sorted(set(x.strip() for x in s.splitlines() if x.strip()))
    old, new = lines(before), lines(after)
    if not old or PACKAGE in old or new != [PACKAGE]:
        raise ValueError("Exclusive HOME role was not granted by consent")

def verify_home(path: Path) -> None:
    if not any(n.attrib.get("package") == PACKAGE and n.attrib.get("text") == "MR. NOTHING"
               for n in ET.parse(path).getroot().iter("node")):
        raise ValueError("Mr. Nothing is not visible after HOME")

def verify_settings(path: Path) -> None:
    if not any(n.attrib.get("package", "").startswith("com.android.settings")
               for n in ET.parse(path).getroot().iter("node")):
        raise ValueError("Android stock HOME settings not visible")

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "approve":
        print(*approve_coordinates(Path(sys.argv[2])))
    elif len(sys.argv) == 4 and sys.argv[1] == "granted":
        verify_granted(Path(sys.argv[2]).read_text(), Path(sys.argv[3]).read_text())
    elif len(sys.argv) == 3 and sys.argv[1] == "home":
        verify_home(Path(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "settings":
        verify_settings(Path(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "recovery":
        print(*tap_coordinates(Path(sys.argv[2]),
            "Recovery: open Android Home app settings to select the stock launcher"))
    else:
        raise SystemExit("usage: qa008_role_accept.py approve|granted|home|settings|recovery")
