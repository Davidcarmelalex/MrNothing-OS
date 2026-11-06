"""QA-009: verify stock-launcher recovery via Android's own chooser.

Only the test harness taps the user-facing UI on a disposable emulator.
No privileged role mutation, shell-based HOME override or physical access.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if __package__:
    from .qa007_role_consent import BOUNDS, PACKAGE
    from .qa008_role_accept import verify_settings
else:
    from qa007_role_consent import BOUNDS, PACKAGE
    from qa008_role_accept import verify_settings

STOCK_PACKAGE = "com.google.android.apps.nexuslauncher"
SYSTEM_HOSTS = frozenset({
    "com.android.settings",
    "com.android.permissioncontroller",
    "com.google.android.permissioncontroller",
})


def stock_coordinates(path: Path) -> tuple[int, int]:
    """Select the uniquely labelled, unselected stock launcher row."""
    verify_settings(path)
    rows = []
    selected_owner = []
    for row in ET.parse(path).getroot().iter("node"):
        attrs = row.attrib
        if (attrs.get("class") != "android.widget.LinearLayout"
                or attrs.get("package") not in SYSTEM_HOSTS
                or attrs.get("clickable") != "true"
                or attrs.get("enabled") != "true"):
            continue
        descendants = [n.attrib for n in row.iter("node")]
        labels = [n for n in descendants if n.get("class") == "android.widget.TextView"
                  and n.get("package") == attrs["package"]]
        radios = [n for n in descendants if n.get("class") == "android.widget.RadioButton"
                  and n.get("package") == attrs["package"] and n.get("checkable") == "true"]
        if len(radios) != 1:
            continue
        if len([n for n in labels if n.get("text") == "Mr. Nothing OS"]) == 1:
            selected_owner.append(radios[0].get("checked") == "true")
        if len([n for n in labels if n.get("text") == "Pixel Launcher"]) != 1:
            continue
        if radios[0].get("checked") != "false" or radios[0].get("enabled") != "true":
            continue
        label = next(n for n in labels if n.get("text") == "Pixel Launcher")
        match = BOUNDS.fullmatch(label.get("bounds", ""))
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            if x2 > x1 and y2 > y1:
                rows.append(((x1 + x2) // 2, (y1 + y2) // 2))
    if selected_owner != [True] or len(rows) != 1:
        raise ValueError("Expected exactly one selected Mr. Nothing and unselected Pixel Launcher row")
    return rows[0]


def verify_return(before: str, after: str) -> None:
    def holders(s: str) -> list[str]:
        return sorted(set(line.strip() for line in s.splitlines() if line.strip()))
    if holders(before) != [PACKAGE] or holders(after) != [STOCK_PACKAGE]:
        raise ValueError("Stock HOME role not exclusively restored")


def verify_stock_home(path: Path) -> None:
    packages = {n.attrib.get("package") for n in ET.parse(path).getroot().iter("node")}
    if STOCK_PACKAGE not in packages or PACKAGE in packages:
        raise ValueError("Stock Pixel Launcher not visible after HOME")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "stock":
        print(*stock_coordinates(Path(sys.argv[2])))
    elif len(sys.argv) == 4 and sys.argv[1] == "role":
        verify_return(Path(sys.argv[2]).read_text(), Path(sys.argv[3]).read_text())
    elif len(sys.argv) == 3 and sys.argv[1] == "home":
        verify_stock_home(Path(sys.argv[2]))
    else:
        raise SystemExit("usage: qa009_stock_recovery.py stock <settings.xml>|role <before> <after>|home <home.xml>")
