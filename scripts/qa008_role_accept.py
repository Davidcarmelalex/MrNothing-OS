"""QA-008: strictly verify affirmative HOME consent on disposable emulator."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
# A direct script invocation puts scripts/ (not the repository root) on sys.path.
# Package imports are used by unittest and `python -m`; direct CI invocations
# require the sibling import. Avoid modifying sys.path or swallowing ImportError.
if __package__:
    from .qa007_role_consent import BOUNDS, PACKAGE, verify_consent_prompt, tap_coordinates
else:
    from qa007_role_consent import BOUNDS, PACKAGE, verify_consent_prompt, tap_coordinates

APPROVE = frozenset({"allow", "set as default", "set as default app", "set default", "ok"})

def select_coordinates(path: Path) -> tuple[int, int]:
    """Select only the Mr. Nothing option in the real system HOME chooser.

    The Android 15 permission-controller chooser disables its approval button
    until a radio option is selected. Never select by screen coordinates alone.
    """
    verify_consent_prompt(path)
    candidates = []
    for row in ET.parse(path).getroot().iter("node"):
        if row.attrib.get("class") != "android.widget.LinearLayout":
            continue
        children = list(row.iter("node"))
        labels = [
            node for node in children
            if node.attrib.get("class") == "android.widget.TextView"
            and node.attrib.get("text") == "Mr. Nothing OS"
            and "permissioncontroller" in node.attrib.get("package", "").lower()
        ]
        radios = [
            node for node in children
            if node.attrib.get("class") == "android.widget.RadioButton"
            and "permissioncontroller" in node.attrib.get("package", "").lower()
        ]
        if len(labels) != 1 or len(radios) != 1:
            continue
        radio = radios[0].attrib
        if radio.get("checkable") != "true" or radio.get("enabled") != "true":
            continue
        if radio.get("checked") != "false":
            continue
        match = BOUNDS.fullmatch(labels[0].attrib.get("bounds", ""))
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            if x2 > x1 and y2 > y1:
                candidates.append(((x1 + x2) // 2, (y1 + y2) // 2))
    if len(candidates) != 1:
        raise ValueError("Expected exactly one unselected system HOME option for Mr. Nothing")
    return candidates[0]

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
    # Android's role service may legitimately report no HOME role holders
    # before the user chooses a default launcher (a single blank line).
    # The acceptance gate concerns the *after* snapshot: exactly our package
    # must hold HOME, with no additional holders, and it must be a transition.
    if PACKAGE in old or new != [PACKAGE]:
        raise ValueError("Exclusive HOME role was not granted by consent")

def verify_home(path: Path) -> None:
    if not any(n.attrib.get("package") == PACKAGE and n.attrib.get("text") == "MR. NOTHING"
               for n in ET.parse(path).getroot().iter("node")):
        raise ValueError("Mr. Nothing is not visible after HOME")

def verify_settings(path: Path) -> None:
    """Require the real Android default-Home chooser, not just a Settings package.

    On API 35 the Settings intent delegates this page to Google's Android
    PermissionController; the page need not be hosted by com.android.settings.
    Match the exact system host, page heading and both launcher options.
    """
    nodes = [n.attrib for n in ET.parse(path).getroot().iter("node")]
    system_hosts = {
        "com.android.settings",
        "com.android.permissioncontroller",
        "com.google.android.permissioncontroller",
    }
    for host in system_hosts:
        hosted = [a for a in nodes if a.get("package") == host]
        headings = [
            a for a in hosted
            if (a.get("text") or a.get("content-desc") or "").strip() == "Default home app"
        ]
        mrnothing = [a for a in hosted if a.get("text") == "Mr. Nothing OS"]
        stock = [a for a in hosted if a.get("text") == "Pixel Launcher"]
        if len(headings) == len(mrnothing) == len(stock) == 1:
            return
    raise ValueError("Verified Android default HOME chooser with both launchers not visible")

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "select":
        print(*select_coordinates(Path(sys.argv[2])))
    elif len(sys.argv) == 3 and sys.argv[1] == "approve":
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
        raise SystemExit("usage: qa008_role_accept.py select|approve|granted|home|settings|recovery")
