#!/usr/bin/env python3
"""Source-level launcher accessibility/recovery checks, NOT a TalkBack test."""
from pathlib import Path
import re
import sys

SOURCE = Path("android/app/src/main/java/tech/mrnothing/os/MainActivity.kt")
REQUIRED = {
    "stock launcher recovery settings": "Settings.ACTION_HOME_SETTINGS",
    "fallback to Android settings": "Settings.ACTION_SETTINGS",
    "screen-reader section headings": "isAccessibilityHeading = true",
    "screen-reader action descriptions": "contentDescription = accessibilityLabel",
    "scalable sp typography": "TypedValue.COMPLEX_UNIT_SP",
    "minimum 56dp touch targets": "minHeight = dp(56)",
    "user-initiated recovery": 'addAction(root, "Switch default Home app"',
    "avoid resetting focus on resume": "if (lastHomeRoleHeld != homeRoleHeld()) render()",
}

def relative_luminance(rgb: tuple[int, int, int]) -> float:
    channels = [v / 255 for v in rgb]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))

def contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    high, low = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)

def check(source: str) -> list[str]:
    failures = [f"Missing {name}" for name, snippet in REQUIRED.items() if snippet not in source]
    palette = {}
    for name in ("backgroundColor", "secondaryTextColor", "accentColor", "buttonColor"):
        pattern = rf"private val {name} = Color\.rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)"
        match = re.search(pattern, source)
        if match is None:
            failures.append(f"Missing explicit {name} RGB palette")
            continue
        rgb = tuple(int(x) for x in match.groups())
        if any(x > 255 for x in rgb):
            failures.append(f"Invalid {name} RGB")
        else:
            palette[name] = rgb
    white = (255, 255, 255)
    for foreground in ("secondaryTextColor", "accentColor"):
        if "backgroundColor" in palette and foreground in palette:
            if contrast_ratio(palette[foreground], palette["backgroundColor"]) < 4.5:
                failures.append(f"{foreground} does not meet 4.5:1 normal text contrast")
    if "buttonColor" in palette and contrast_ratio(white, palette["buttonColor"]) < 4.5:
        failures.append("Button text does not meet 4.5:1 normal text contrast")
    return failures

def main() -> int:
    errors = check(SOURCE.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return 1
    print("Launcher source accessibility/recovery gate passed (not device-tested)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
