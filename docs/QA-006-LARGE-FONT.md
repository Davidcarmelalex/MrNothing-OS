# QA-006 — Large-font emulator verification

**Owner:** CI/QA + Android/UX. **Supervisor gate:** PENDING_INDEPENDENT_REVIEW.

This bounded QA increment extends the existing Android 15 x86_64 disposable-emulator smoke test. It saves a normal-font hierarchy, changes the **emulator only** to 200% system font scale, restarts the launcher, captures a large-font screenshot and hierarchy, and checks that the MR. NOTHING heading's measured UI bounds increase. It scrolls to verify that the stock-Home recovery action remains discoverable. The script restores the previous font setting on exit.

## Acceptance gate
- QA-005 and QA-006 pass in the same completed GitHub Actions emulator run at the new commit.
- Evidence ZIP includes `qa006/large-font.png`, `qa006/large-hierarchy.xml`, activity start output and the scroll hierarchy containing the recovery action.
- The hierarchy comparison demonstrates a larger title bounding box, not merely that the setting was written.
- Python unit tests and workflow security gates pass.
- Independent reviewer inspects actual evidence before approving M2.

## Explicit limitations
This is **not** TalkBack spoken-order testing, human usability validation, full UI visual-diff validation, Home-role switching, orientation testing, Pixel 9 Pro hardware compatibility, OTA/recovery validation or production signing. The script refuses physical devices by serial and emulator property. Never run it against an actual owner's phone.
