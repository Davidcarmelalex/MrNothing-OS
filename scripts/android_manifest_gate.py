"""Source-manifest security gate for the experimental MrNothing launcher.

This inspects the checked-in manifest, not the Gradle-merged manifest.
It deliberately fails closed if new exported components or permissions appear.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ANDROID = "{http://schemas.android.com/apk/res/android}"
HOME = "android.intent.category.HOME"
DEFAULT = "android.intent.category.DEFAULT"
MAIN = "android.intent.action.MAIN"


def inspect_manifest(root: ET.Element) -> list[str]:
    problems: list[str] = []
    if root.tag != "manifest":
        return ["root must be manifest"]
    if root.get(ANDROID + "sharedUserId") is not None:
        problems.append("sharedUserId is forbidden")
    apps = root.findall("application")
    if len(apps) != 1:
        return problems + ["exactly one application is required"]
    app = apps[0]
    if app.get(ANDROID + "allowBackup") != "false":
        problems.append("allowBackup must be false")
    if app.get(ANDROID + "usesCleartextTraffic") != "false":
        problems.append("usesCleartextTraffic must be false")
    for attribute in ("debuggable", "testOnly", "requestLegacyExternalStorage"):
        if app.get(ANDROID + attribute) == "true":
            problems.append(attribute + " must not be true")
    if root.findall("uses-permission") or root.findall("uses-permission-sdk-23"):
        problems.append("new Android permissions require explicit policy review")
    found_home = False
    for component_type in ("activity", "activity-alias", "service", "receiver", "provider"):
        for component in app.findall(component_type):
            name = component.get(ANDROID + "name", "")
            exported = component.get(ANDROID + "exported")
            is_home = component_type == "activity" and name == ".MainActivity"
            if is_home:
                if exported != "true":
                    problems.append("Home activity must be explicitly exported")
                for intent in component.findall("intent-filter"):
                    actions = {x.get(ANDROID + "name") for x in intent.findall("action")}
                    categories = {x.get(ANDROID + "name") for x in intent.findall("category")}
                    if MAIN in actions and {HOME, DEFAULT}.issubset(categories):
                        found_home = True
            elif exported != "false":
                problems.append("non-Home component must explicitly be non-exported: " + name)
            if not name:
                problems.append("component missing android:name")
    if not found_home:
        problems.append("explicit MAIN/HOME/DEFAULT intent filter required")
    return problems


def check_file(path: str | Path) -> list[str]:
    try:
        return inspect_manifest(ET.parse(path).getroot())
    except (ET.ParseError, OSError) as exc:
        return ["manifest unavailable or invalid: " + str(exc)]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/android_manifest_gate.py <AndroidManifest.xml>", file=sys.stderr)
        return 2
    problems = check_file(argv[1])
    if problems:
        for problem in problems:
            print("MANIFEST SECURITY ERROR: " + problem, file=sys.stderr)
        return 1
    print("Source AndroidManifest.xml security gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
