"""QA-010: keyboard focus accessibility; not a TalkBack test."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

PKG = "tech.mrnothing.os"
RECOVERY = "Recovery: open Android Home app settings to select the stock launcher"
SETTINGS = "Open Android system settings"


def controls(path):
    found = []
    for node in ET.parse(path).getroot().iter("node"):
        a = node.attrib
        if a.get("package") != PKG or a.get("class") != "android.widget.Button":
            continue
        if any(a.get(k) != "true" for k in ("clickable", "enabled", "focusable")) or not a.get("content-desc", "").strip():
            raise ValueError("Inaccessible or disabled launcher button")
        found.append(a)
    return found


def baseline(path):
    labels = [a["content-desc"] for a in controls(path)]
    if len(labels) < 2 or len(labels) != len(set(labels)):
        raise ValueError("Expected uniquely labelled buttons")
    if labels.count(RECOVERY) != 1 or labels.count(SETTINGS) != 1 or labels.index(RECOVERY) >= labels.index(SETTINGS):
        raise ValueError("Recovery or Settings missing, ambiguous or misordered")


def focused(path):
    labels = [a["content-desc"] for a in controls(path) if a.get("focused") == "true"]
    if len(labels) > 1:
        raise ValueError("Multiple focused launcher buttons")
    return labels[0] if labels else ""


def sequence(base, folder):
    baseline(base)
    files = sorted(folder.glob("focus-*.xml"))
    if len(files) < 2:
        raise ValueError("Insufficient focus snapshots")
    labels = [focused(p) for p in files]
    if RECOVERY not in labels or len(set(x for x in labels if x)) < 2:
        raise ValueError("Keyboard focus did not traverse recovery and another button")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "baseline":
        baseline(Path(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "focus":
        print(focused(Path(sys.argv[2])))
    elif len(sys.argv) == 4 and sys.argv[1] == "sequence":
        sequence(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        raise SystemExit("usage: qa010_accessibility.py baseline|focus <xml>|sequence <baseline.xml> <folder>")
