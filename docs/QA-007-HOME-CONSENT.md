# QA-007 — HOME role consent cancellation (emulator only)

**Scope:** On a disposable Android API 35 emulator, launch Mr. Nothing, tap its user-visible `Choose Mr. Nothing as Home` button, verify that Android's permission-controller prompt identifies Mr. Nothing, dismiss with Back, and assert that the original HOME role holder is unchanged.

The test does **not** approve the request, force the role with `cmd role add-role-holder`, change any physical phone, or claim stock-launcher recovery has been exercised. It is a negative-consent test, not a full role-switching E2E test. The emulator test is expected to fail closed if the role is already held or if the permission-controller UI changes unexpectedly. Retained evidence: before/prompt hierarchies, role holders before/after and launcher start result. Do not record private data in artifacts.

**Acceptance:** Workflow run succeeds with a real emulator, UI prompt evidence and unchanged HOME holder. Source/unit tests alone do not meet this gate. Full affirmative HOME switching, stock-launcher recovery and TalkBack remain separate requirements.
