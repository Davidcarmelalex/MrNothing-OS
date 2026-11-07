# UX-003 — Accessible HOME launcher and recovery (source implementation)

## Implemented
- All launcher text uses scalable SP; layout spacing and button targets use density-independent DP.
- Explicit accessibility headings and descriptive action labels for TalkBack.
- Normal-text foreground/background palette tested against WCAG AA 4.5:1 contrast calculations.
- All launcher buttons have at least a 56dp minimum height.
- The launcher includes an always-visible **Switch default Home app** recovery action that opens Android's `Settings.ACTION_HOME_SETTINGS`, letting the owner choose the stock launcher. If unavailable, it opens system Settings.
- The HOME role is requested only after the owner presses the button; it is not silently acquired.
- The launcher does not re-render on every activity resume, reducing unintended TalkBack focus/scroll resets.
- Device status honestly labels the agent offline and cellular AI audio unverified.

## Automated gate
`python3 scripts/launcher_accessibility_gate.py` verifies source-level accessibility and recovery requirements. Unit tests include deliberately broken source cases and contrast math. The Android build and JVM tests run in GitHub Actions.

## Unverified / acceptance gates remaining
- Real TalkBack navigation and reading order, 200% font-scale clipping, landscape, gesture navigation, dark/high-contrast accessibility settings and RTL behavior on an emulator.
- Stock launcher recovery on an emulator and actual Pixel 9 Pro.
- Screen-reader focus after app launch, task switching and process death.
- Independent accessibility reviewer approval.

**Source gates are not a substitute for runtime accessibility testing.** Do not mark M2 complete until emulator/device evidence and independent review exist. No root, device flashing or privileged app control is part of UX-003.
