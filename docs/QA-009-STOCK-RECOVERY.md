# QA-009: stock Pixel launcher recovery

On the disposable API 35 x86_64 emulator only, continue from QA-008 after the owner-facing Android **Default home app** page is open. Validate the system host, both launcher labels, a uniquely selected Mr. Nothing radio row, and a uniquely unselected Pixel Launcher row. Tap the Pixel Launcher row through the Android UI (never via privileged role overrides), then require an exclusive role transition to `com.google.android.apps.nexuslauncher` and a Pixel Launcher UI hierarchy after pressing HOME.

Capture before/after HOME role snapshots, UI hierarchy and screenshot. Any ambiguous row, missing role transition or wrong launcher fails closed. A stock-launcher selection in this disposable emulator is a test fixture, **not** consent for changing any physical device. This does not test Pixel 9 Pro hardware, TalkBack, OS firmware recovery or OTA rollback. Independent supervisor approval remains pending.

The selection parser is grounded in `qa008/settings.xml` from successful [QA-008 CI run 41422497145](https://github.com/Davidcarmelalex/MrNothing-OS/actions/runs/41422497145). QA-009 is **not runtime-verified** until its own CI succeeds.
