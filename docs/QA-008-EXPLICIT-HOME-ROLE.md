# QA-008: explicit HOME acceptance and recovery route

Run only on the disposable Android API 35 emulator. This scenario deliberately taps an Android permission-controller approval control after verifying its package, label, bounds and uniqueness. It does **not** use privileged role overrides. Verify the HOME holder changes exclusively to Mr. Nothing, pressing HOME launches the app, and its recovery button opens Android Settings. Keep role snapshots, prompt and launcher UI hierarchy, and screenshot as CI artifacts.

This is not a physical-device test, stock-launcher re-selection test, TalkBack test or firmware validation. Unexpected system dialog variants fail closed and require inspection of actual emulator evidence. Independent signoff remains pending.
